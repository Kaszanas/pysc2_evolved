#!/usr/bin/python
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for features."""

import copy
import pickle

import numpy
import pytest
from google.protobuf import text_format
from s2clientprotocol import sc2api_pb2 as sc_pb

from pysc2_evolved.lib import actions, features, point

# Heavily trimmed, so this is useful for testing actions, but not observations.
observation_text_proto = """
player_common {
  player_id: 1
  minerals: 0
  vespene: 0
  food_cap: 10
  food_used: 0
  food_army: 0
  food_workers: 0
  idle_worker_count: 0
  army_count: 0
  warp_gate_count: 0
  larva_count: 0
}
game_loop: 20
"""


RECTANGULAR_DIMENSIONS = features.Dimensions(screen=(84, 80), minimap=(64, 67))
SQUARE_DIMENSIONS = features.Dimensions(screen=84, minimap=64)


def gen_random_function_call(action_spec, func_id):
    args = [
        [numpy.random.randint(0, size) for size in arg.sizes]  # pylint: disable=g-complex-comprehension
        for arg in action_spec.functions[func_id].args
    ]
    return actions.FunctionCall(func_id, args)


@pytest.mark.minor
class TestAvailableActions:
    always_expected = {
        "no_op",
        "move_camera",
        "select_point",
        "select_rect",
        "select_control_group",
    }

    def setup_method(self):
        self.obs = text_format.Parse(observation_text_proto, sc_pb.Observation())
        self._hide_specific_actions(True)

    def _hide_specific_actions(self, hide_specific_actions):
        self.features = features.Features(
            features.AgentInterfaceFormat(
                feature_dimensions=RECTANGULAR_DIMENSIONS,
                hide_specific_actions=hide_specific_actions,
            )
        )

    def _assert_avail(self, expected):
        actual = self.features.available_actions(self.obs)
        actual_names = {actions.FUNCTIONS[i].name for i in actual}
        assert actual_names == set(expected) | self.always_expected

    def test_always(self):
        self._assert_avail([])

    def test_select_unit(self):
        self.obs.ui_data.multi.units.add(unit_type=1)
        self._assert_avail(["select_unit"])

    def test_select_idle_worker(self):
        self.obs.player_common.idle_worker_count = 1
        self._assert_avail(["select_idle_worker"])

    def test_select_army(self):
        self.obs.player_common.army_count = 3
        self._assert_avail(["select_army"])

    def test_select_warp_gates(self):
        self.obs.player_common.warp_gate_count = 1
        self._assert_avail(["select_warp_gates"])

    def test_select_larva(self):
        self.obs.player_common.larva_count = 2
        self._assert_avail(["select_larva"])

    def test_quick(self):
        self.obs.abilities.add(ability_id=32)
        self._assert_avail(["Effect_Salvage_quick"])

    def test_screen(self):
        self.obs.abilities.add(ability_id=326, requires_point=True)
        self._assert_avail(["Build_SensorTower_screen"])

    def test_screen_minimap(self):
        self.obs.abilities.add(ability_id=17, requires_point=True)
        self._assert_avail(["Patrol_screen", "Patrol_minimap"])

    def test_screen_autocast(self):
        self.obs.abilities.add(ability_id=386, requires_point=True)
        self._assert_avail(["Effect_Heal_screen", "Effect_Heal_autocast"])

    def test_screen_quick(self):
        a = self.obs.abilities.add(ability_id=421)

        self._hide_specific_actions(True)
        a.requires_point = False
        self._assert_avail(["Build_TechLab_quick"])
        a.requires_point = True
        self._assert_avail(["Build_TechLab_screen"])

        self._hide_specific_actions(False)
        a.requires_point = False
        self._assert_avail(["Build_TechLab_Barracks_quick", "Build_TechLab_quick"])
        a.requires_point = True
        self._assert_avail(["Build_TechLab_Barracks_screen", "Build_TechLab_screen"])

    def test_general(self):
        self.obs.abilities.add(ability_id=1374)
        self._hide_specific_actions(False)
        self._assert_avail(["BurrowDown_quick", "BurrowDown_Baneling_quick"])
        self._hide_specific_actions(True)
        self._assert_avail(["BurrowDown_quick"])

    def test_general_type(self):
        a = self.obs.abilities.add(ability_id=1376)
        self._hide_specific_actions(False)
        self._assert_avail(
            [
                "BurrowUp_quick",
                "BurrowUp_Baneling_quick",
                "BurrowUp_autocast",
                "BurrowUp_Baneling_autocast",
            ]
        )
        self._hide_specific_actions(True)
        self._assert_avail(["BurrowUp_quick", "BurrowUp_autocast"])

        a.ability_id = 2110
        self._hide_specific_actions(False)
        self._assert_avail(["BurrowUp_quick", "BurrowUp_Lurker_quick"])
        self._hide_specific_actions(True)
        self._assert_avail(["BurrowUp_quick"])

    def test_many(self):
        add = [
            (23, True),  # Attack
            (318, True),  # Build_CommandCenter
            (320, True),  # Build_Refinery
            (319, True),  # Build_SupplyDepot
            (316, True),  # Effect_Repair_SCV
            (295, True),  # Harvest_Gather_SCV
            (16, True),  # Move
            (17, True),  # Patrol
            (4, False),  # Stop
        ]
        for a, r in add:
            self.obs.abilities.add(ability_id=a, requires_point=r)
        self._hide_specific_actions(False)
        self._assert_avail(
            [
                "Attack_Attack_minimap",
                "Attack_Attack_screen",
                "Attack_minimap",
                "Attack_screen",
                "Build_CommandCenter_screen",
                "Build_Refinery_screen",
                "Build_SupplyDepot_screen",
                "Effect_Repair_screen",
                "Effect_Repair_autocast",
                "Effect_Repair_SCV_autocast",
                "Effect_Repair_SCV_screen",
                "Harvest_Gather_screen",
                "Harvest_Gather_SCV_screen",
                "Move_minimap",
                "Move_screen",
                "Move_Move_minimap",
                "Move_Move_screen",
                "Patrol_minimap",
                "Patrol_screen",
                "Patrol_Patrol_minimap",
                "Patrol_Patrol_screen",
                "Stop_quick",
                "Stop_Stop_quick",
            ]
        )
        self._hide_specific_actions(True)
        self._assert_avail(
            [
                "Attack_minimap",
                "Attack_screen",
                "Build_CommandCenter_screen",
                "Build_Refinery_screen",
                "Build_SupplyDepot_screen",
                "Effect_Repair_screen",
                "Effect_Repair_autocast",
                "Harvest_Gather_screen",
                "Move_minimap",
                "Move_screen",
                "Patrol_minimap",
                "Patrol_screen",
                "Stop_quick",
            ]
        )


@pytest.mark.minor
class TestToPoint:
    def test_int_as_string(self):
        value = features._to_point("32")
        assert value == point.Point(32, 32)

    def test_int_string_two_tuple(self):
        value = features._to_point(("32", 64))
        assert value == point.Point(32, 64)

    def test_none_input_raises(self):
        with pytest.raises(AssertionError):
            features._to_point(None)

    def test_none_as_first_element_raises(self):
        with pytest.raises(TypeError):
            features._to_point((None, 32))

    def test_none_as_second_element_raises(self):
        with pytest.raises(TypeError):
            features._to_point((32, None))

    def test_singleton_tuple_raises(self):
        with pytest.raises(ValueError):
            features._to_point((32,))

    def test_three_tuple_raises(self):
        with pytest.raises(ValueError):
            features._to_point((32, 32, 32))


@pytest.mark.minor
class TestDimensions:
    def test_screen_size_without_minimap_raises(self):
        with pytest.raises(ValueError):
            features.Dimensions(screen=84)

    def test_screen_width_without_height_raises(self):
        with pytest.raises(ValueError):
            features.Dimensions(screen=(84, 0), minimap=64)

    def test_screen_width_height_without_minimap_raises(self):
        with pytest.raises(ValueError):
            features.Dimensions(screen=(84, 80))

    def test_minimap_width_and_height_without_screen_raises(self):
        with pytest.raises(ValueError):
            features.Dimensions(minimap=(64, 67))

    def test_none_none_raises(self):
        with pytest.raises(ValueError):
            features.Dimensions(screen=None, minimap=None)

    def test_singular_zeroes_raises(self):
        with pytest.raises(ValueError):
            features.Dimensions(screen=0, minimap=0)

    def test_two_zeroes_raises(self):
        with pytest.raises(ValueError):
            features.Dimensions(screen=(0, 0), minimap=(0, 0))

    def test_three_tuple_screen_raises(self):
        with pytest.raises(ValueError):
            features.Dimensions(screen=(1, 2, 3), minimap=32)

    def test_three_tuple_minimap_raises(self):
        with pytest.raises(ValueError):
            features.Dimensions(screen=64, minimap=(1, 2, 3))

    def test_negative_screen_raises(self):
        with pytest.raises(ValueError):
            features.Dimensions(screen=-64, minimap=32)

    def test_negative_minimap_raises(self):
        with pytest.raises(ValueError):
            features.Dimensions(screen=64, minimap=-32)

    def test_negative_screen_tuple_raises(self):
        with pytest.raises(ValueError):
            features.Dimensions(screen=(-64, -64), minimap=32)

    def test_negative_minimap_tuple_raises(self):
        with pytest.raises(ValueError):
            features.Dimensions(screen=64, minimap=(-32, -32))

    def test_equality(self):
        assert features.Dimensions(screen=64, minimap=64) == features.Dimensions(
            screen=64, minimap=64
        )
        assert features.Dimensions(screen=64, minimap=64) != features.Dimensions(
            screen=64, minimap=32
        )
        assert features.Dimensions(screen=64, minimap=64) != None


@pytest.mark.minor
class TestParseAgentInterfaceFormat:
    def test_no_arguments_raises(self):
        with pytest.raises(ValueError):
            features.parse_agent_interface_format()

    @pytest.mark.parametrize(
        "screen,minimap", [(32, None), (None, 32)]
    )
    def test_invalid_feature_combinations_raise(self, screen, minimap):
        with pytest.raises(ValueError):
            features.parse_agent_interface_format(
                feature_screen=screen, feature_minimap=minimap
            )

    def test_valid_feature_specification_is_parsed(self):
        agent_interface_format = features.parse_agent_interface_format(
            feature_screen=32, feature_minimap=(24, 24)
        )

        assert agent_interface_format.feature_dimensions.screen == point.Point(32, 32)
        assert agent_interface_format.feature_dimensions.minimap == point.Point(24, 24)

    @pytest.mark.parametrize(
        "screen,minimap", [(32, None), (None, 32), (32, 64)]
    )
    def test_invalid_minimap_combinations_raise(self, screen, minimap):
        with pytest.raises(ValueError):
            features.parse_agent_interface_format(
                rgb_screen=screen, rgb_minimap=minimap
            )

    def test_valid_minimap_specification_is_parsed(self):
        agent_interface_format = features.parse_agent_interface_format(
            rgb_screen=32, rgb_minimap=(24, 24)
        )

        assert agent_interface_format.rgb_dimensions.screen == point.Point(32, 32)
        assert agent_interface_format.rgb_dimensions.minimap == point.Point(24, 24)

    def test_invalid_action_space_raises(self):
        with pytest.raises(KeyError):
            features.parse_agent_interface_format(
                feature_screen=64,
                feature_minimap=64,
                action_space="UNKNOWN_ACTION_SPACE",
            )

    @pytest.mark.parametrize("action_space", actions.ActionSpace.__members__.keys())
    def test_valid_action_space_is_parsed(self, action_space):
        agent_interface_format = features.parse_agent_interface_format(
            feature_screen=32,
            feature_minimap=(24, 24),
            rgb_screen=64,
            rgb_minimap=(48, 48),
            use_raw_units=True,
            action_space=action_space,
        )

        assert agent_interface_format.action_space == actions.ActionSpace[action_space]

    def test_camera_width_world_units_are_parsed(self):
        agent_interface_format = features.parse_agent_interface_format(
            feature_screen=32, feature_minimap=(24, 24), camera_width_world_units=77
        )

        assert agent_interface_format.camera_width_world_units == 77

    def test_use_feature_units_is_parsed(self):
        agent_interface_format = features.parse_agent_interface_format(
            feature_screen=32, feature_minimap=(24, 24), use_feature_units=True
        )

        assert agent_interface_format.use_feature_units is True


@pytest.mark.minor
class TestFeatures:
    def test_functions_ids_are_consistent(self):
        for i, f in enumerate(actions.FUNCTIONS):
            assert i == f.id, "id doesn't match for %s" % f.id

    def test_all_versions_of_an_ability_have_the_same_general(self):
        for ability_id, funcs in actions.ABILITY_IDS.items():
            assert len({f.general_id for f in funcs}) == 1, (
                "Multiple generals for %s" % ability_id
            )

    def test_valid_functions_are_consistent(self):
        feats = features.Features(
            features.AgentInterfaceFormat(feature_dimensions=RECTANGULAR_DIMENSIONS)
        )

        valid_funcs = feats.action_spec()
        for func_def in valid_funcs.functions:
            func = actions.FUNCTIONS[func_def.id]
            assert func_def.id == func.id
            assert func_def.name == func.name
            assert len(func_def.args) == len(func.args)  # pylint: disable=g-generic-assert

    def test_ids_match_index(self):
        feats = features.Features(
            features.AgentInterfaceFormat(feature_dimensions=RECTANGULAR_DIMENSIONS)
        )
        action_spec = feats.action_spec()
        for func_index, func_def in enumerate(action_spec.functions):
            assert func_index == func_def.id
        for type_index, type_def in enumerate(action_spec.types):
            assert type_index == type_def.id

    def test_reversing_unknown_action(self):
        feats = features.Features(
            features.AgentInterfaceFormat(
                feature_dimensions=RECTANGULAR_DIMENSIONS, hide_specific_actions=False
            )
        )
        sc2_action = sc_pb.Action()
        sc2_action.action_feature_layer.unit_command.ability_id = 6  # Cheer
        func_call = feats.reverse_action(sc2_action)
        assert func_call.function == 0  # No-op

    def test_specific_actions_are_reversible(self):
        """Test that the `transform_action` and `reverse_action` are inverses."""
        feats = features.Features(
            features.AgentInterfaceFormat(
                feature_dimensions=RECTANGULAR_DIMENSIONS, hide_specific_actions=False
            )
        )
        action_spec = feats.action_spec()

        for func_def in action_spec.functions:
            for _ in range(10):
                func_call = gen_random_function_call(action_spec, func_def.id)

                sc2_action = feats.transform_action(
                    None, func_call, skip_available=True
                )
                func_call2 = feats.reverse_action(sc2_action)
                sc2_action2 = feats.transform_action(
                    None, func_call2, skip_available=True
                )
                if func_def.id == actions.FUNCTIONS.select_rect.id:
                    # Need to check this one manually since the same rect can be
                    # defined in multiple ways.
                    def rect(a):
                        return point.Rect(
                            point.Point(*a[1]).floor(), point.Point(*a[2]).floor()
                        )

                    assert func_call.function == func_call2.function
                    assert len(func_call.arguments) == len(func_call2.arguments)  # pylint: disable=g-generic-assert
                    assert func_call.arguments[0] == func_call2.arguments[0]
                    assert rect(func_call.arguments) == rect(func_call2.arguments)
                else:
                    assert func_call == func_call2, sc2_action
                assert sc2_action == sc2_action2

    def test_raw_action_unit_tags(self):
        feats = features.Features(
            features.AgentInterfaceFormat(
                use_raw_units=True, action_space=actions.ActionSpace.RAW
            ),
            map_size=point.Point(100, 100),
        )

        tags = [numpy.random.randint(2**20, 2**24) for _ in range(10)]
        ntags = numpy.array(tags, dtype=numpy.int64)
        tag = tags[0]
        ntag = numpy.array(tag, dtype=numpy.int64)

        def transform(fn, *args):
            func_call = actions.RAW_FUNCTIONS[fn]("now", *args)
            proto = feats.transform_action(None, func_call, skip_available=True)
            return proto.action_raw.unit_command

        assert transform("Attack_pt", tag, [15, 20]).unit_tags == [tag]
        assert transform("Attack_pt", ntag, [15, 20]).unit_tags == [tag]
        assert transform("Attack_pt", [tag], [15, 20]).unit_tags == [tag]
        assert transform("Attack_pt", [ntag], [15, 20]).unit_tags == [tag]
        assert transform("Attack_pt", tags, [15, 20]).unit_tags == tags
        assert transform("Attack_pt", ntags, [15, 20]).unit_tags == tags
        # Weird, but needed for backwards compatibility
        assert transform("Attack_pt", [tags], [15, 20]).unit_tags == tags
        assert transform("Attack_pt", [ntags], [15, 20]).unit_tags == tags

        assert transform("Attack_unit", tag, tag).target_unit_tag == tag
        assert transform("Attack_unit", tag, ntag).target_unit_tag == tag
        assert transform("Attack_unit", tag, [tag]).target_unit_tag == tag
        assert transform("Attack_unit", tag, [ntag]).target_unit_tag == tag

    def test_can_pickle_specs(self):
        feats = features.Features(
            features.AgentInterfaceFormat(feature_dimensions=SQUARE_DIMENSIONS)
        )
        action_spec = feats.action_spec()
        observation_spec = feats.observation_spec()

        assert action_spec == pickle.loads(pickle.dumps(action_spec))
        assert observation_spec == pickle.loads(pickle.dumps(observation_spec))

    def test_can_pickle_function_call(self):
        func = actions.FUNCTIONS.select_point("select", [1, 2])
        assert func == pickle.loads(pickle.dumps(func))

    def test_can_deepcopy_numpy_function_call(self):
        arguments = [numpy.float32] * len(actions.Arguments._fields)
        dtypes = actions.FunctionCall(
            function=numpy.float32, arguments=actions.Arguments(*arguments)
        )
        assert dtypes == copy.deepcopy(dtypes)

    def test_size_constructors(self):
        feats = features.Features(
            features.AgentInterfaceFormat(feature_dimensions=SQUARE_DIMENSIONS)
        )
        spec = feats.action_spec()
        assert spec.types.screen.sizes == (84, 84)
        assert spec.types.screen2.sizes == (84, 84)
        assert spec.types.minimap.sizes == (64, 64)

        feats = features.Features(
            features.AgentInterfaceFormat(feature_dimensions=RECTANGULAR_DIMENSIONS)
        )
        spec = feats.action_spec()
        assert spec.types.screen.sizes == (84, 80)
        assert spec.types.screen2.sizes == (84, 80)
        assert spec.types.minimap.sizes == (64, 67)

        feats = features.Features(
            features.AgentInterfaceFormat(feature_dimensions=RECTANGULAR_DIMENSIONS)
        )
        spec = feats.action_spec()
        assert spec.types.screen.sizes == (84, 80)
        assert spec.types.screen2.sizes == (84, 80)
        assert spec.types.minimap.sizes == (64, 67)

        # Missing one or the other of game_info and dimensions.
        with pytest.raises(ValueError):
            features.Features()

        # Resolution/action space mismatch.
        with pytest.raises(ValueError):
            features.Features(
                features.AgentInterfaceFormat(
                    feature_dimensions=RECTANGULAR_DIMENSIONS,
                    action_space=actions.ActionSpace.RGB,
                )
            )
        with pytest.raises(ValueError):
            features.Features(
                features.AgentInterfaceFormat(
                    rgb_dimensions=RECTANGULAR_DIMENSIONS,
                    action_space=actions.ActionSpace.FEATURES,
                )
            )
        with pytest.raises(ValueError):
            features.Features(
                features.AgentInterfaceFormat(
                    feature_dimensions=RECTANGULAR_DIMENSIONS,
                    rgb_dimensions=RECTANGULAR_DIMENSIONS,
                )
            )

    def test_fl_rgb_action_spec(self):
        feats = features.Features(
            features.AgentInterfaceFormat(
                feature_dimensions=RECTANGULAR_DIMENSIONS,
                rgb_dimensions=features.Dimensions(screen=(128, 132), minimap=(74, 77)),
                action_space=actions.ActionSpace.FEATURES,
            )
        )
        spec = feats.action_spec()
        assert spec.types.screen.sizes == (84, 80)
        assert spec.types.screen2.sizes == (84, 80)
        assert spec.types.minimap.sizes == (64, 67)

        feats = features.Features(
            features.AgentInterfaceFormat(
                feature_dimensions=RECTANGULAR_DIMENSIONS,
                rgb_dimensions=features.Dimensions(screen=(128, 132), minimap=(74, 77)),
                action_space=actions.ActionSpace.RGB,
            )
        )
        spec = feats.action_spec()
        assert spec.types.screen.sizes == (128, 132)
        assert spec.types.screen2.sizes == (128, 132)
        assert spec.types.minimap.sizes == (74, 77)

    def test_fl_rgb_observation_spec(self):
        feats = features.Features(
            features.AgentInterfaceFormat(
                feature_dimensions=RECTANGULAR_DIMENSIONS,
                rgb_dimensions=features.Dimensions(screen=(128, 132), minimap=(74, 77)),
                action_space=actions.ActionSpace.FEATURES,
            )
        )
        obs_spec = feats.observation_spec()
        assert obs_spec["feature_screen"] == (  # pylint: disable=g-generic-assert
            len(features.SCREEN_FEATURES),
            80,
            84,
        )
        assert obs_spec["feature_minimap"] == (  # pylint: disable=g-generic-assert
            len(features.MINIMAP_FEATURES),
            67,
            64,
        )
        assert obs_spec["rgb_screen"] == (132, 128, 3)
        assert obs_spec["rgb_minimap"] == (77, 74, 3)
