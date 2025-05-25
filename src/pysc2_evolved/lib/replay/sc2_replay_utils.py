# Copyright 2021 DeepMind Technologies Ltd. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities built on top of sc2_replay."""

import collections
import dataclasses
from typing import Any, Dict, List, Mapping

from pysc2_evolved.lib.replay import sc2_replay

_EVENT_TYPES_TO_FILTER_OUT = frozenset(
    [
        # Not related to actions.
        "SetSyncLoadingTime",
        "SetSyncPlayingTime",
        "TriggerSoundLengthSync",
        "UserFinishedLoadingSync",
        "UserOptions",
        # Always accompanied by a CommandManagerState, which we track.
        "CmdUpdateTargetPoint",
        # Of interest for the visual interface, but skipped for now as we are
        # targeting raw.
        "CameraSave",
        "ControlGroupUpdate",
        "SelectionDelta",
    ]
)


def _readable_event_type(full_event_type):
    return full_event_type[len("NNet.Game.S") : -5]


@dataclasses.dataclass
class EventData:
    game_loop: int
    event_type: str


@dataclasses.dataclass
class PlayerIDs:
    player_name: str | None = None
    player_toon: str | None = None
    user_id: int | None = None
    player_id: int | None = None
    slot_id: int | None = None

    def __hash__(self):
        return hash(
            (
                self.player_name,
                self.player_toon,
                self.user_id,
                self.player_id,
                self.slot_id,
            )
        )


def get_detail_player_list(replay: sc2_replay.SC2Replay) -> List[Dict[str, Any]]:
    details = replay.details()
    details_player_list = details["m_playerList"]
    for player in details_player_list:
        toon_object = player["m_toon"]
        region = toon_object["m_region"]
        program_id = toon_object["m_programId"][-2:]
        realm = toon_object["m_realm"]
        m_id = toon_object["m_id"]

        toon_string = f"{region}-{program_id}-{realm}-{m_id}"
        player["m_toon"] = toon_string

    return details_player_list


def get_init_data_slot_list(replay: sc2_replay.SC2Replay) -> List[Dict[str, Any]]:
    init_data = replay.init_data()
    init_data_sync_lobby_state = init_data["m_syncLobbyState"]
    init_data_lobby_state = init_data_sync_lobby_state["m_lobbyState"]
    init_data_slots = init_data_lobby_state["m_slots"]

    return init_data_slots


def get_nickname_from_toon(
    slot_list: List[Dict[str, Any]],
    details_player_list: List[Dict[str, Any]],
) -> Dict[str, PlayerIDs]:
    toon_to_player_dict = {}
    for details_player in details_player_list:
        player_toon = details_player["m_toon"]
        player_name = details_player["m_name"]

        toon_to_player_dict[player_toon] = PlayerIDs(
            player_name=player_name, player_toon=player_toon
        )

    for index, slot_data in enumerate(slot_list):
        slot_toon = slot_data["m_toonHandle"]
        if slot_toon in toon_to_player_dict:
            slot_index = index
            user_id = slot_data["m_userId"]

            toon_to_player_dict[slot_toon].slot_id = slot_index
            toon_to_player_dict[slot_toon].user_id = user_id

    return toon_to_player_dict


def get_user_id_to_PlayerIDs_mapping(
    toon_to_player_ids_mapping: Dict[str, PlayerIDs],
) -> Dict[str, PlayerIDs]:
    new_dict = dict()
    for _, value in toon_to_player_ids_mapping.items():
        new_dict[value.user_id] = value

    return new_dict


def get_player_ids(user_id_to_object_mapping: Dict[int, PlayerIDs]):
    player_id_to_info_mapping = {}
    for _, player_ids in user_id_to_object_mapping.items():
        player_id_to_info_mapping[player_ids.player_id] = player_ids

    return player_id_to_info_mapping


def get_active_players(replay: sc2_replay.SC2Replay) -> Dict[str, PlayerIDs]:
    slots = get_init_data_slot_list(replay=replay)
    details_player_list = get_detail_player_list(replay=replay)

    toon_to_player_ids_mapping = get_nickname_from_toon(
        slot_list=slots, details_player_list=details_player_list
    )

    user_id_to_object_mapping = get_user_id_to_PlayerIDs_mapping(
        toon_to_player_ids_mapping=toon_to_player_ids_mapping
    )

    for event in replay.tracker_events():
        # event_type = _readable_event_type(event["_event"])

        event_type = event["_event"].split(".")[-1]

        # We are only interested in the PlayerSetup event.
        # This is important for the participating players more so than the observers.
        if event_type != "SPlayerSetupEvent":
            continue

        # This should be the user ID of the participating player:
        user_id = event["m_userId"]
        active_player_object = user_id_to_object_mapping[user_id]

        player_id = event["m_playerId"]
        active_player_object.player_id = player_id

        # slot_id = event["m_slotId"]

        # TODO: It is possible to get the user toon from the slot.
        # But how do I get other user information such as nickname?

    return user_id_to_object_mapping


def raw_action_skips(replay: sc2_replay.SC2Replay) -> Mapping[int, List[int]]:
    """
    Returns player id -> list, the game loops on which each player acted.

    Args:
      replay: An sc2_replay.SC2Replay instance.

    Note that these skips are specific to the raw interface - further work will
    be needed to support visual.
    """
    action_frames = collections.defaultdict(list)
    last_game_loop = None

    # Acquiring only the active players without observers:
    active_players_user_id_map = get_active_players(replay=replay)

    # Extract per-user events of interest.
    for event in replay.game_events():
        event_type = _readable_event_type(event["_event"])
        if event_type not in _EVENT_TYPES_TO_FILTER_OUT:
            game_loop = event["_gameloop"]
            last_game_loop = game_loop

            # TODO:
            # REVIEW: This only works for replays that have two players.
            # Need to verify that the observerss or other users are always with
            # ID above 2, then it is safe to say that such events can be skipped.
            # Then there would be no need to raise this exception.
            user_id = event["_userid"]["m_userId"]
            # player_id = user_id + 1

            # We don't care about observers and other users for now:
            if user_id not in active_players_user_id_map:
                continue

            player_information = active_players_user_id_map[user_id]
            player_id = player_information.player_id

            # REVIEW: Observers/referees can leave the game before.
            # We need to make sure that this pertains only to the active players.
            # As soon as anyone leaves, we stop tracking events.
            # We check if the user left only in case of active players.
            # We do not care if the observers leave the game:
            if event_type == "GameUserLeave":
                break

            # REVIEW: This check is not true for replays with observers:
            # if player_id < 1 or player_id > 2:
            #     raise ValueError(f"Unexpected player_id: {player_id}")
            if (
                action_frames[player_id]
                and action_frames[player_id][-1].game_loop == game_loop
            ):
                # Later (non-camera) events on the same game loop take priority.
                if event_type != "CameraUpdate":
                    action_frames[player_id][-1].event_type = event_type
            else:
                action_frames[player_id].append(EventData(game_loop, event_type))

    for player_id in action_frames:
        # Filter out repeated camera updates.
        filtered = []
        for v in action_frames[player_id]:
            if (
                v.event_type == "CameraUpdate"
                and filtered
                and filtered[-1].event_type == "CameraUpdate"
            ):
                filtered[-1].game_loop = v.game_loop
            else:
                filtered.append(v)
        # If the last update is a camera move, remove it (only camera moves with a
        # raw action following them should be added).
        if filtered and filtered[-1].event_type == "CameraUpdate":
            filtered.pop()
        # Extract game loops.
        action_frames[player_id] = [v.game_loop for v in filtered]
        if not action_frames[player_id] or (
            action_frames[player_id][-1] != last_game_loop
        ):
            action_frames[player_id].append(last_game_loop)
    return action_frames
