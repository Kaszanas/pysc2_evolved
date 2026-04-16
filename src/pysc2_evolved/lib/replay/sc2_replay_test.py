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

import pytest

from pysc2_evolved.lib import gfile, resources
from pysc2_evolved.lib.replay import sc2_replay

PATH = "pysc2_evolved/lib/replay/test_data/replay_01.SC2Replay"


@pytest.fixture
def replay():
    replay_path = resources.GetResourceFilename(PATH)
    with gfile.Open(replay_path, mode="rb") as f:
        replay_data = f.read()
    return sc2_replay.SC2Replay(replay_data)


@pytest.mark.minor
class TestSc2Replay:
    def test_details(self, replay):
        replay_details = replay.details()
        assert replay_details["m_cacheHandles"] == []
        assert replay_details["m_campaignIndex"] == 0
        assert replay_details["m_defaultDifficulty"] == 3
        assert replay_details["m_description"] == ""
        assert replay_details["m_difficulty"] == ""
        assert not replay_details["m_disableRecoverGame"]
        assert replay_details["m_gameSpeed"] == 4
        assert replay_details["m_imageFilePath"] == ""
        assert not replay_details["m_isBlizzardMap"]
        assert (
            replay_details["m_mapFileName"]
            == "Ladder2019Season1May/CyberForestLE.SC2Map"
        )
        assert not replay_details["m_miniSave"]
        assert replay_details["m_modPaths"] == [
            "Mods/Liberty.SC2Mod",
            "Mods/Swarm.SC2Mod",
            "Mods/Void.SC2Mod",
            "Mods/VoidMulti.SC2Mod",
        ]
        # (there is more data here, just listing the most interesting bits)
        assert replay_details["m_playerList"][0]["m_name"] == "Supervised"
        assert not replay_details["m_playerList"][0]["m_observe"]
        assert replay_details["m_playerList"][0]["m_race"] == "Protoss"
        assert replay_details["m_playerList"][0]["m_result"] == 2
        assert (
            replay_details["m_playerList"][1]["m_name"]
            == "temp_x1_5_beast3f_6571236_final"
        )
        assert not replay_details["m_playerList"][1]["m_observe"]
        assert replay_details["m_playerList"][1]["m_race"] == "Protoss"
        assert replay_details["m_playerList"][1]["m_result"] == 1
        assert not replay_details["m_restartAsTransitionMap"]
        assert replay_details["m_thumbnail"]["m_file"] == "Minimap.tga"
        assert replay_details["m_timeLocalOffset"] == 0
        assert replay_details["m_timeUTC"] == 132772394814660570
        assert replay_details["m_title"] == "Cyber Forest LE"

    def test_init_data(self, replay):
        init_data = replay.init_data()
        # (there is more data here, just listing the most interesting bits)
        game_description = init_data["m_syncLobbyState"]["m_gameDescription"]
        assert game_description["m_gameOptions"]["m_fog"] == 0
        assert game_description["m_gameSpeed"] == 4
        assert game_description["m_isBlizzardMap"] is False
        assert game_description["m_isRealtimeMode"] is False
        assert (
            game_description["m_mapFileName"]
            == "Ladder2019Season1May/CyberForestLE.SC2Map"
        )

    def test_tracker_events(self, replay):
        events = list(replay.tracker_events())
        event_types = set(s["_event"] for s in events)

        assert event_types == {
            "NNet.Replay.Tracker.SPlayerSetupEvent",
            "NNet.Replay.Tracker.SPlayerStatsEvent",
            "NNet.Replay.Tracker.SUnitBornEvent",
            "NNet.Replay.Tracker.SUnitDiedEvent",
            "NNet.Replay.Tracker.SUnitDoneEvent",
            "NNet.Replay.Tracker.SUnitInitEvent",
            "NNet.Replay.Tracker.SUnitPositionsEvent",
            "NNet.Replay.Tracker.SUnitTypeChangeEvent",
            "NNet.Replay.Tracker.SUpgradeEvent",
        }

    def test_game_events(self, replay):
        events = list(replay.game_events())
        event_types = set(s["_event"] for s in events)

        assert event_types == {
            "NNet.Game.SCameraUpdateEvent",
            "NNet.Game.SCmdEvent",
            "NNet.Game.SCmdUpdateTargetPointEvent",
            "NNet.Game.SCmdUpdateTargetUnitEvent",
            "NNet.Game.SCommandManagerStateEvent",
            "NNet.Game.SPeerSetSyncLoadingTimeEvent",
            "NNet.Game.SPeerSetSyncPlayingTimeEvent",
            "NNet.Game.SSelectionDeltaEvent",
            "NNet.Game.SUserFinishedLoadingSyncEvent",
            "NNet.Game.SUserOptionsEvent",
        }

    def test_message_events(self, replay):
        events = list(replay.message_events())
        event_types = set(s["_event"] for s in events)

        assert event_types == {"NNet.Game.SLoadingProgressMessage"}

    def test_attributes_events(self, replay):
        events = list(replay.attributes_events())
        assert events == []
