#!/usr/bin/python
# Copyright 2018 Google Inc. All Rights Reserved.
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

import numpy as np
import pytest
from s2clientprotocol import common_pb2

from pysc2_evolved.lib import actions, features, point, units
from pysc2_evolved.tests import dummy_observation

_PROBE = dummy_observation.Unit(
    units.Protoss.Probe, features.PlayerRelative.SELF, 20, 20, 0, 0, 1.0
)

_ZEALOT = dummy_observation.Unit(
    units.Protoss.Zealot, features.PlayerRelative.SELF, 100, 50, 0, 0, 1.0
)

_MOTHERSHIP = dummy_observation.Unit(
    units.Protoss.Mothership, features.PlayerRelative.SELF, 350, 7, 200, 0, 1.0
)


@pytest.mark.minor
class TestDummyObservation:
    def setup_method(self):
        self._features = features.Features(
            features.AgentInterfaceFormat(
                feature_dimensions=features.Dimensions(
                    screen=(64, 60), minimap=(32, 28)
                ),
                rgb_dimensions=features.Dimensions(screen=(128, 124), minimap=(64, 60)),
                action_space=actions.ActionSpace.FEATURES,
                use_feature_units=True,
            ),
            map_size=point.Point(256, 256),
        )
        self._obs_spec = self._features.observation_spec()
        self._builder = dummy_observation.Builder(self._obs_spec)

    def test_feature_screen_matches_spec(self):
        obs = self._get_obs()
        for f in features.SCREEN_FEATURES:
            self._check_layer(
                getattr(obs.feature_layer_data.renders, f.name), 64, 60, 8
            )

    def test_feature_minimap_matches_spec(self):
        obs = self._get_obs()
        for f in features.MINIMAP_FEATURES:
            self._check_layer(
                getattr(obs.feature_layer_data.minimap_renders, f.name), 32, 28, 8
            )

    def test_rgb_screen_matches_spec(self):
        obs = self._get_obs()
        self._check_layer(obs.render_data.map, 128, 124, 24)

    def test_game_loop_can_be_set(self):
        self._builder.game_loop(1234)
        obs = self._get_obs()
        assert obs.game_loop == 1234

    def test_player_common_can_be_set(self):
        self._builder.player_common(
            minerals=1000,
            vespene=200,
            food_cap=200,
            food_used=198,
            food_army=140,
            food_workers=58,
            army_count=92,
            warp_gate_count=7,
            larva_count=15,
        )

        obs = self._get_obs()
        assert obs.player_common.player_id == 1  # (we didn't set it)
        assert obs.player_common.minerals == 1000
        assert obs.player_common.vespene == 200
        assert obs.player_common.food_cap == 200
        assert obs.player_common.food_used == 198
        assert obs.player_common.food_army == 140
        assert obs.player_common.food_workers == 58
        assert obs.player_common.idle_worker_count == 2  # (didn't set it)
        assert obs.player_common.army_count == 92
        assert obs.player_common.warp_gate_count == 7
        assert obs.player_common.larva_count == 15

    def test_score_can_be_set(self):
        self._builder.score(54321)
        obs = self._get_obs()
        assert obs.score.score == 54321

    def test_score_details_can_be_set(self):
        self._builder.score_details(
            idle_production_time=1,
            idle_worker_time=2,
            total_value_units=3,
            killed_value_units=5,
            killed_value_structures=6,
            collected_minerals=7,
            collected_vespene=8,
            collection_rate_minerals=9,
            collection_rate_vespene=10,
            spent_minerals=11,
            spent_vespene=12,
        )
        obs = self._get_obs()
        assert obs.score.score_details.idle_production_time == 1
        assert obs.score.score_details.idle_worker_time == 2
        assert obs.score.score_details.total_value_units == 3
        assert obs.score.score_details.total_value_structures == 230
        assert obs.score.score_details.killed_value_units == 5
        assert obs.score.score_details.killed_value_structures == 6
        assert obs.score.score_details.collected_minerals == 7
        assert obs.score.score_details.collected_vespene == 8
        assert obs.score.score_details.collection_rate_minerals == 9
        assert obs.score.score_details.collection_rate_vespene == 10
        assert obs.score.score_details.spent_minerals == 11
        assert obs.score.score_details.spent_vespene == 12

    def test_score_by_category_spec(self):
        # Note that if these dimensions are changed, client code is liable to break.
        np.testing.assert_array_equal(
            self._obs_spec.score_by_category, np.array([11, 5], dtype=np.int32)
        )

    @pytest.mark.parametrize(
        "entry_name", [entry.name for entry in features.ScoreByCategory]
    )
    def test_score_by_category(self, entry_name):
        self._builder.score_by_category(
            entry_name, none=10, army=1200, economy=400, technology=100, upgrade=200
        )

        response_observation = self._builder.build()
        obs = response_observation.observation
        entry = getattr(obs.score.score_details, entry_name)
        assert entry.none == 10
        assert entry.army == 1200
        assert entry.economy == 400
        assert entry.technology == 100
        assert entry.upgrade == 200

        # Check the transform_obs does what we expect, too.
        transformed_obs = self._features.transform_obs(response_observation)
        transformed_entry = getattr(transformed_obs.score_by_category, entry_name)
        assert transformed_entry.none == 10
        assert transformed_entry.army == 1200
        assert transformed_entry.economy == 400
        assert transformed_entry.technology == 100
        assert transformed_entry.upgrade == 200

    def test_score_by_vital_spec(self):
        # Note that if these dimensions are changed, client code is liable to break.
        np.testing.assert_array_equal(
            self._obs_spec.score_by_vital, np.array([3, 3], dtype=np.int32)
        )

    @pytest.mark.parametrize(
        "entry_name", [entry.name for entry in features.ScoreByVital]
    )
    def test_score_by_vital(self, entry_name):
        self._builder.score_by_vital(entry_name, life=1234, shields=45, energy=423)

        response_observation = self._builder.build()
        obs = response_observation.observation
        entry = getattr(obs.score.score_details, entry_name)
        assert entry.life == 1234
        assert entry.shields == 45
        assert entry.energy == 423

        # Check the transform_obs does what we expect, too.
        transformed_obs = self._features.transform_obs(response_observation)
        transformed_entry = getattr(transformed_obs.score_by_vital, entry_name)
        assert transformed_entry.life == 1234
        assert transformed_entry.shields == 45
        assert transformed_entry.energy == 423

    def test_rgb_minimap_matches_spec(self):
        obs = self._get_obs()
        self._check_layer(obs.render_data.minimap, 64, 60, 24)

    def test_no_single_select(self):
        obs = self._get_obs()
        assert not obs.ui_data.HasField("single")

    def test_with_single_select(self):
        self._builder.single_select(_PROBE)
        obs = self._get_obs()
        self._check_unit(obs.ui_data.single.unit, _PROBE)

    def test_no_multi_select(self):
        obs = self._get_obs()
        assert not obs.ui_data.HasField("multi")

    def test_with_multi_select(self):
        nits = [_MOTHERSHIP, _PROBE, _PROBE, _ZEALOT]
        self._builder.multi_select(nits)
        obs = self._get_obs()
        assert len(obs.ui_data.multi.units) == 4
        for proto, builder in zip(obs.ui_data.multi.units, nits):
            self._check_unit(proto, builder)

    def test_build_queue(self):
        nits = [_MOTHERSHIP, _PROBE]
        production = [
            {
                "ability_id": actions.FUNCTIONS.Train_Mothership_quick.ability_id,
                "build_progress": 0.5,
            },
            {
                "ability_id": actions.FUNCTIONS.Train_Probe_quick.ability_id,
                "build_progress": 0,
            },
            {
                "ability_id": actions.FUNCTIONS.Research_ShadowStrike_quick.ability_id,
                "build_progress": 0,
            },
        ]
        self._builder.build_queue(nits, production)
        obs = self._get_obs()
        assert len(obs.ui_data.production.build_queue) == 2
        for proto, builder in zip(obs.ui_data.production.build_queue, nits):
            self._check_unit(proto, builder)
        assert len(obs.ui_data.production.production_queue) == 3
        for proto, p in zip(obs.ui_data.production.production_queue, production):
            assert proto.ability_id == p["ability_id"]
            assert proto.build_progress == p["build_progress"]

    def test_feature_units_are_added(self):
        feature_units = [
            dummy_observation.FeatureUnit(
                units.Protoss.Probe,
                features.PlayerRelative.SELF,
                owner=1,
                pos=common_pb2.Point(x=10, y=10, z=0),
                radius=1.0,
                health=10,
                health_max=20,
                is_on_screen=True,
                shield=0,
                shield_max=20,
            ),
            dummy_observation.FeatureUnit(
                units.Terran.Marine,
                features.PlayerRelative.SELF,
                owner=1,
                pos=common_pb2.Point(x=11, y=12, z=0),
                radius=1.0,
                health=35,
                health_max=45,
                is_on_screen=True,
                shield=0,
                shield_max=0,
            ),
        ]

        self._builder.feature_units(feature_units)

        obs = self._get_obs()
        for proto, builder in zip(obs.raw_data.units, feature_units):
            self._check_feature_unit(proto, builder)

    def _get_obs(self):
        return self._builder.build().observation

    def _check_layer(self, layer, x, y, bits):
        assert layer.size.x == x
        assert layer.size.y == y
        assert layer.bits_per_pixel == bits

    def _check_attributes_match(self, a, b, attributes):
        for attribute in attributes:
            assert getattr(a, attribute) == getattr(b, attribute)

    def _check_unit(self, proto, builder):
        return self._check_attributes_match(proto, builder, vars(builder).keys())

    def _check_feature_unit(self, proto, builder):
        return self._check_attributes_match(
            proto,
            builder,
            [
                "unit_type",
                "alliance",
                "owner",
                "pos",
                "radius",
                "health",
                "health_max",
                "is_on_screen",
                "shield",
                "shield_max",
            ],
        )
