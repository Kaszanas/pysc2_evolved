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
from typing import List, Mapping, Set

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
    user_id: int
    player_id: int
    slot_id: int


def get_active_players(replay: sc2_replay.SC2Replay) -> Set[PlayerIDs]:
    user_id_set = set()

    for event in replay.tracker_events():
        event_type = _readable_event_type(event["_event"])

        # We are only interested in the PlayerSetup event.
        # This is important for the participating players more so than the observers.
        if event_type != "PlayerSetup":
            continue

        # This should be the user ID of the participating player:
        user_id = event["_userid"]["m_userId"]
        player_id = event["_userid"]["m_playerId"]
        slot_id = event["_userid"]["m_slotId"]

        if user_id not in user_id_set:
            user_id_set.add(
                PlayerIDs(user_id=user_id, player_id=player_id, slot_id=slot_id)
            )

    return user_id_set


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
    active_players = get_active_players(replay=replay)
    active_user_id_to_player_id = {
        player_object.user_id: player_object.player_id
        for player_object in active_players
    }

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

            player_id = None
            if player_id not in active_user_id_to_player_id:
                # This is an observer or a referee.
                # We can skip this event.
                continue
            player_id = active_user_id_to_player_id[user_id]

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
