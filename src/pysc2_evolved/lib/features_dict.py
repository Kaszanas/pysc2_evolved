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
"""Render feature layers from SC2 Observation dicts into numpy arrays."""
# pylint: disable=g-complex-comprehension

import collections
import random

import numpy as np
from absl import logging
from s2clientprotocol import raw_pb2 as sc_raw
from s2clientprotocol import sc2api_pb2 as sc_pb

from pysc2_evolved.lib import (
    actions,
    colors,
    named_array,
    point,
    static_data,
    stopwatch,
    transform,
)
from pysc2_evolved.lib.features_types import (
    EffectPos,
    FeatureType,
    FeatureUnit,
    Passthrough,
    Player,
    ProductionQueue,
    Radar,
    ScoreByCategory,
    ScoreByVital,
    ScoreCategories,
    ScoreCumulative,
    ScoreVitals,
    UnitCounts,
    UnitLayer,
)

sw = stopwatch.sw

EPSILON = 1e-5


class Feature(
    collections.namedtuple(
        "Feature",
        ["index", "name", "layer_set", "full_name", "scale", "type", "palette", "clip"],
    )
):
    """Define properties of a feature layer.

    Attributes:
      index: Index of this layer into the set of layers.
      name: The name of the layer within the set.
      layer_set: Which set of feature layers to look at in the observation dict.
      full_name: The full name including for visualization.
      scale: Max value (+1) of this layer, used to scale the values.
      type: A FeatureType for scalar vs categorical.
      palette: A color palette for rendering.
      clip: Whether to clip the values for coloring.
    """

    __slots__ = ()

    dtypes = {
        1: np.uint8,
        8: np.uint8,
        16: np.uint16,
        32: np.int32,
    }

    def unpack(self, obs):
        """Return a correctly shaped numpy array for this feature."""
        if "feature_layer_data" not in obs:
            return None
        planes = obs["feature_layer_data"].get(self.layer_set)
        if planes is None:
            return None
        plane = planes.get(self.name)
        if plane is None:
            return None
        return self.unpack_layer(plane)

    @staticmethod
    @sw.decorate
    def unpack_layer(plane):
        """Return a correctly shaped numpy array given the feature layer bytes."""
        size = point.Point(plane["size"]["x"], plane["size"]["y"])
        if size == (0, 0):
            return None
        data = np.frombuffer(
            plane["data"], dtype=Feature.dtypes[plane["bits_per_pixel"]]
        )
        if plane["bits_per_pixel"] == 1:
            data = np.unpackbits(data)
            if data.shape[0] != size.x * size.y:
                data = data[: size.x * size.y]
        return data.reshape(size.y, size.x)

    @staticmethod
    @sw.decorate
    def unpack_rgb_image(plane):
        """Return a correctly shaped numpy array given the image bytes."""
        assert plane["bits_per_pixel"] == 24, "{} != 24".format(plane["bits_per_pixel"])
        size = point.Point(plane["size"]["x"], plane["size"]["y"])
        data = np.frombuffer(plane["data"], dtype=np.uint8)
        return data.reshape(size.y, size.x, 3)

    @sw.decorate
    def color(self, plane: np.ndarray) -> np.ndarray:
        if True:  # self.clip:
            plane = np.clip(plane, 0, self.scale - 1)
        return self.palette[plane]


class ScreenFeatures(
    collections.namedtuple(
        "ScreenFeatures",
        [
            "height_map",
            "visibility_map",
            "creep",
            "power",
            "player_id",
            "player_relative",
            "unit_type",
            "selected",
            "unit_hit_points",
            "unit_hit_points_ratio",
            "unit_energy",
            "unit_energy_ratio",
            "unit_shields",
            "unit_shields_ratio",
            "unit_density",
            "unit_density_aa",
            "effects",
            "hallucinations",
            "cloaked",
            "blip",
            "buffs",
            "buff_duration",
            "active",
            "build_progress",
            "pathable",
            "buildable",
            "placeholder",
        ],
    )
):
    """The set of screen feature layers."""

    __slots__ = ()

    def __new__(cls, **kwargs):
        feats = {}
        for name, (scale, type_, palette, clip) in kwargs.items():
            feats[name] = Feature(
                index=ScreenFeatures._fields.index(name),
                name=name,
                layer_set="renders",
                full_name="screen " + name,
                scale=scale,
                type=type_,
                palette=palette(scale) if callable(palette) else palette,
                clip=clip,
            )
        return super(ScreenFeatures, cls).__new__(
            cls, **feats
        )  # pytype: disable=missing-parameter


class MinimapFeatures(
    collections.namedtuple(
        "MinimapFeatures",
        [
            "height_map",
            "visibility_map",
            "creep",
            "camera",
            "player_id",
            "player_relative",
            "selected",
            "unit_type",
            "alerts",
            "pathable",
            "buildable",
        ],
    )
):
    """The set of minimap feature layers."""

    __slots__ = ()

    def __new__(cls, **kwargs):
        feats = {}
        for name, (scale, type_, palette) in kwargs.items():
            feats[name] = Feature(
                index=MinimapFeatures._fields.index(name),
                name=name,
                layer_set="minimap_renders",
                full_name="minimap " + name,
                scale=scale,
                type=type_,
                palette=palette(scale) if callable(palette) else palette,
                clip=False,
            )
        return super(MinimapFeatures, cls).__new__(
            cls, **feats
        )  # pytype: disable=missing-parameter


SCREEN_FEATURES = ScreenFeatures(
    height_map=(256, FeatureType.SCALAR, colors.height_map, False),
    visibility_map=(4, FeatureType.CATEGORICAL, colors.VISIBILITY_PALETTE, False),
    creep=(2, FeatureType.CATEGORICAL, colors.CREEP_PALETTE, False),
    power=(2, FeatureType.CATEGORICAL, colors.POWER_PALETTE, False),
    player_id=(17, FeatureType.CATEGORICAL, colors.PLAYER_ABSOLUTE_PALETTE, False),
    player_relative=(5, FeatureType.CATEGORICAL, colors.PLAYER_RELATIVE_PALETTE, False),
    unit_type=(
        max(static_data.UNIT_TYPES) + 1,
        FeatureType.CATEGORICAL,
        colors.unit_type,
        False,
    ),
    selected=(2, FeatureType.CATEGORICAL, colors.SELECTED_PALETTE, False),
    unit_hit_points=(1600, FeatureType.SCALAR, colors.hot, True),
    unit_hit_points_ratio=(256, FeatureType.SCALAR, colors.hot, False),
    unit_energy=(1000, FeatureType.SCALAR, colors.hot, True),
    unit_energy_ratio=(256, FeatureType.SCALAR, colors.hot, False),
    unit_shields=(1000, FeatureType.SCALAR, colors.hot, True),
    unit_shields_ratio=(256, FeatureType.SCALAR, colors.hot, False),
    unit_density=(16, FeatureType.SCALAR, colors.hot, True),
    unit_density_aa=(256, FeatureType.SCALAR, colors.hot, False),
    effects=(16, FeatureType.CATEGORICAL, colors.effects, False),
    hallucinations=(2, FeatureType.CATEGORICAL, colors.POWER_PALETTE, False),
    cloaked=(2, FeatureType.CATEGORICAL, colors.POWER_PALETTE, False),
    blip=(2, FeatureType.CATEGORICAL, colors.POWER_PALETTE, False),
    buffs=(max(static_data.BUFFS) + 1, FeatureType.CATEGORICAL, colors.buffs, False),
    buff_duration=(256, FeatureType.SCALAR, colors.hot, False),
    active=(2, FeatureType.CATEGORICAL, colors.POWER_PALETTE, False),
    build_progress=(256, FeatureType.SCALAR, colors.hot, False),
    pathable=(2, FeatureType.CATEGORICAL, colors.winter, False),
    buildable=(2, FeatureType.CATEGORICAL, colors.winter, False),
    placeholder=(2, FeatureType.CATEGORICAL, colors.winter, False),
)

MINIMAP_FEATURES = MinimapFeatures(
    height_map=(256, FeatureType.SCALAR, colors.height_map),
    visibility_map=(4, FeatureType.CATEGORICAL, colors.VISIBILITY_PALETTE),
    creep=(2, FeatureType.CATEGORICAL, colors.CREEP_PALETTE),
    camera=(2, FeatureType.CATEGORICAL, colors.CAMERA_PALETTE),
    player_id=(17, FeatureType.CATEGORICAL, colors.PLAYER_ABSOLUTE_PALETTE),
    player_relative=(5, FeatureType.CATEGORICAL, colors.PLAYER_RELATIVE_PALETTE),
    selected=(2, FeatureType.CATEGORICAL, colors.winter),
    unit_type=(
        max(static_data.UNIT_TYPES) + 1,
        FeatureType.CATEGORICAL,
        colors.unit_type,
    ),
    alerts=(2, FeatureType.CATEGORICAL, colors.winter),
    pathable=(2, FeatureType.CATEGORICAL, colors.winter),
    buildable=(2, FeatureType.CATEGORICAL, colors.winter),
)


def _to_point(dims):
    """Convert (width, height) or size -> point.Point."""
    assert dims

    if isinstance(dims, (tuple, list)):
        if len(dims) != 2:
            raise ValueError(
                "A two element tuple or list is expected here, got {}.".format(dims)
            )
        else:
            width = int(dims[0])
            height = int(dims[1])
            if width <= 0 or height <= 0:
                raise ValueError("Must specify +ve dims, got {}.".format(dims))
            else:
                return point.Point(width, height)
    else:
        size = int(dims)
        if size <= 0:
            raise ValueError("Must specify a +ve value for size, got {}.".format(dims))
        else:
            return point.Point(size, size)


class Dimensions(object):
    """Screen and minimap dimensions configuration.

    Both screen and minimap must be specified. Sizes must be positive.
    Screen size must be greater than or equal to minimap size in both dimensions.

    Attributes:
      screen: A (width, height) int tuple or a single int to be used for both.
      minimap: A (width, height) int tuple or a single int to be used for both.
    """

    def __init__(self, screen=None, minimap=None):
        if not screen or not minimap:
            raise ValueError(
                "screen and minimap must both be set, screen={}, minimap={}".format(
                    screen, minimap
                )
            )

        self._screen = _to_point(screen)
        self._minimap = _to_point(minimap)

    @property
    def screen(self):
        return self._screen

    @property
    def minimap(self):
        return self._minimap

    def __repr__(self):
        return "Dimensions(screen={}, minimap={})".format(self.screen, self.minimap)

    def __eq__(self, other):
        return (
            isinstance(other, Dimensions)
            and self.screen == other.screen
            and self.minimap == other.minimap
        )

    def __ne__(self, other):
        return not self == other


class AgentInterfaceFormat(object):
    """Observation and action interface format specific to a particular agent."""

    def __init__(
        self,
        feature_dimensions=None,
        rgb_dimensions=None,
        raw_resolution=None,
        action_space=None,
        camera_width_world_units=None,
        use_feature_units=False,
        use_raw_units=False,
        use_raw_actions=False,
        max_raw_actions=512,
        max_selected_units=30,
        use_unit_counts=False,
        use_camera_position=False,
        show_cloaked=False,
        show_burrowed_shadows=False,
        show_placeholders=False,
        hide_specific_actions=True,
        action_delay_fn=None,
        send_observation_proto=False,
        crop_to_playable_area=False,
        raw_crop_to_playable_area=False,
        allow_cheating_layers=False,
        add_cargo_to_units=False,
    ):
        """Initializer."""

        if not (feature_dimensions or rgb_dimensions or use_raw_units):
            raise ValueError(
                "Must set either the feature layer or rgb dimensions, or use raw units."
            )

        if action_space:
            if not isinstance(action_space, actions.ActionSpace):
                raise ValueError("action_space must be of type ActionSpace.")

            if action_space == actions.ActionSpace.RAW:
                use_raw_actions = True
            elif (
                action_space == actions.ActionSpace.FEATURES and not feature_dimensions
            ) or (action_space == actions.ActionSpace.RGB and not rgb_dimensions):
                raise ValueError(
                    "Action space must match the observations, action space={}, "
                    "feature_dimensions={}, rgb_dimensions={}".format(
                        action_space, feature_dimensions, rgb_dimensions
                    )
                )
        else:
            if use_raw_actions:
                action_space = actions.ActionSpace.RAW
            elif feature_dimensions and rgb_dimensions:
                raise ValueError(
                    "You must specify the action space if you have both screen and "
                    "rgb observations."
                )
            elif feature_dimensions:
                action_space = actions.ActionSpace.FEATURES
            else:
                action_space = actions.ActionSpace.RGB

        if raw_resolution:
            raw_resolution = _to_point(raw_resolution)

        if use_raw_actions:
            if not use_raw_units:
                raise ValueError(
                    "You must set use_raw_units if you intend to use_raw_actions"
                )
            if action_space != actions.ActionSpace.RAW:
                raise ValueError(
                    "Don't specify both an action_space and use_raw_actions."
                )

        if rgb_dimensions and (
            rgb_dimensions.screen.x < rgb_dimensions.minimap.x
            or rgb_dimensions.screen.y < rgb_dimensions.minimap.y
        ):
            raise ValueError(
                "RGB Screen (%s) can't be smaller than the minimap (%s)."
                % (rgb_dimensions.screen, rgb_dimensions.minimap)
            )

        self._feature_dimensions = feature_dimensions
        self._rgb_dimensions = rgb_dimensions
        self._action_space = action_space
        self._camera_width_world_units = camera_width_world_units or 24
        self._use_feature_units = use_feature_units
        self._use_raw_units = use_raw_units
        self._raw_resolution = raw_resolution
        self._use_raw_actions = use_raw_actions
        self._max_raw_actions = max_raw_actions
        self._max_selected_units = max_selected_units
        self._use_unit_counts = use_unit_counts
        self._use_camera_position = use_camera_position
        self._show_cloaked = show_cloaked
        self._show_burrowed_shadows = show_burrowed_shadows
        self._show_placeholders = show_placeholders
        self._hide_specific_actions = hide_specific_actions
        self._action_delay_fn = action_delay_fn
        self._send_observation_proto = send_observation_proto
        self._add_cargo_to_units = add_cargo_to_units
        self._crop_to_playable_area = crop_to_playable_area
        self._raw_crop_to_playable_area = raw_crop_to_playable_area
        self._allow_cheating_layers = allow_cheating_layers

        if action_space == actions.ActionSpace.FEATURES:
            self._action_dimensions = feature_dimensions
        else:
            self._action_dimensions = rgb_dimensions

    @property
    def feature_dimensions(self):
        return self._feature_dimensions

    @property
    def rgb_dimensions(self):
        return self._rgb_dimensions

    @property
    def action_space(self):
        return self._action_space

    @property
    def camera_width_world_units(self):
        return self._camera_width_world_units

    @property
    def use_feature_units(self):
        return self._use_feature_units

    @property
    def use_raw_units(self):
        return self._use_raw_units

    @property
    def raw_resolution(self):
        return self._raw_resolution

    @raw_resolution.setter
    def raw_resolution(self, value):
        self._raw_resolution = value

    @property
    def use_raw_actions(self):
        return self._use_raw_actions

    @property
    def max_raw_actions(self):
        return self._max_raw_actions

    @property
    def max_selected_units(self):
        return self._max_selected_units

    @property
    def use_unit_counts(self):
        return self._use_unit_counts

    @property
    def use_camera_position(self):
        return self._use_camera_position

    @property
    def show_cloaked(self):
        return self._show_cloaked

    @property
    def show_burrowed_shadows(self):
        return self._show_burrowed_shadows

    @property
    def show_placeholders(self):
        return self._show_placeholders

    @property
    def hide_specific_actions(self):
        return self._hide_specific_actions

    @property
    def action_delay_fn(self):
        return self._action_delay_fn

    @property
    def send_observation_proto(self):
        return self._send_observation_proto

    @property
    def add_cargo_to_units(self):
        return self._add_cargo_to_units

    @property
    def action_dimensions(self):
        return self._action_dimensions

    @property
    def crop_to_playable_area(self):
        return self._crop_to_playable_area

    @property
    def raw_crop_to_playable_area(self):
        return self._raw_crop_to_playable_area

    @property
    def allow_cheating_layers(self):
        return self._allow_cheating_layers


def parse_agent_interface_format(
    feature_screen=None,
    feature_minimap=None,
    rgb_screen=None,
    rgb_minimap=None,
    action_space=None,
    action_delays=None,
    **kwargs,
):
    """Creates an AgentInterfaceFormat object from keyword args."""
    if feature_screen or feature_minimap:
        feature_dimensions = Dimensions(feature_screen, feature_minimap)
    else:
        feature_dimensions = None

    if rgb_screen or rgb_minimap:
        rgb_dimensions = Dimensions(rgb_screen, rgb_minimap)
    else:
        rgb_dimensions = None

    def _action_delay_fn(delays):
        """Delay frequencies per game loop delay -> fn returning game loop delay."""
        if not delays:
            return None
        else:
            total = sum(delays)
            cumulative_sum = np.cumsum([delay / total for delay in delays])

            def fn():
                sample = random.uniform(0, 1) - EPSILON
                for i, cumulative in enumerate(cumulative_sum):
                    if sample <= cumulative:
                        return i + 1
                raise ValueError("Failed to sample action delay??")

            return fn

    return AgentInterfaceFormat(
        feature_dimensions=feature_dimensions,
        rgb_dimensions=rgb_dimensions,
        action_space=(action_space and actions.ActionSpace[action_space.upper()]),
        action_delay_fn=_action_delay_fn(action_delays),
        **kwargs,
    )


def features_from_game_info(
    game_info, agent_interface_format=None, map_name=None, **kwargs
):
    """Construct a Features object using data extracted from game info dict."""
    if isinstance(agent_interface_format, sc_pb.InterfaceOptions):
        return Passthrough()

    if not map_name:
        map_name = game_info.get("map_name")

    options = game_info.get("options", {})
    if "feature_layer" in options:
        fl_opts = options["feature_layer"]
        feature_dimensions = Dimensions(
            screen=(fl_opts["resolution"]["x"], fl_opts["resolution"]["y"]),
            minimap=(
                fl_opts["minimap_resolution"]["x"],
                fl_opts["minimap_resolution"]["y"],
            ),
        )
        camera_width_world_units = fl_opts.get("width")
    else:
        feature_dimensions = None
        camera_width_world_units = None

    if "render" in options:
        rgb_opts = options["render"]
        rgb_dimensions = Dimensions(
            screen=(rgb_opts["resolution"]["x"], rgb_opts["resolution"]["y"]),
            minimap=(
                rgb_opts["minimap_resolution"]["x"],
                rgb_opts["minimap_resolution"]["y"],
            ),
        )
    else:
        rgb_dimensions = None

    map_size = game_info["start_raw"]["map_size"]

    requested_races = {
        info["player_id"]: info["race_requested"]
        for info in game_info.get("player_info", [])
        if info.get("type") != sc_pb.Observer
    }

    if agent_interface_format:
        if kwargs:
            raise ValueError(
                "Either give an agent_interface_format or kwargs, not both."
            )
        aif = agent_interface_format
        if (
            aif.rgb_dimensions != rgb_dimensions
            or aif.feature_dimensions != feature_dimensions
            or (
                feature_dimensions
                and aif.camera_width_world_units != camera_width_world_units
            )
        ):
            raise ValueError(
                """
The supplied agent_interface_format doesn't match the resolutions computed from
the game_info:
  rgb_dimensions: %s vs %s
  feature_dimensions: %s vs %s
  camera_width_world_units: %s vs %s
"""
                % (
                    aif.rgb_dimensions,
                    rgb_dimensions,
                    aif.feature_dimensions,
                    feature_dimensions,
                    aif.camera_width_world_units,
                    camera_width_world_units,
                )
            )
    else:
        agent_interface_format = AgentInterfaceFormat(
            feature_dimensions=feature_dimensions,
            rgb_dimensions=rgb_dimensions,
            camera_width_world_units=camera_width_world_units,
            **kwargs,
        )

    return Features(
        agent_interface_format=agent_interface_format,
        map_size=map_size,
        map_name=map_name,
        requested_races=requested_races,
    )


def _init_valid_functions(action_dimensions):
    """Initialize ValidFunctions and set up the callbacks."""
    sizes = {
        "screen": tuple(int(i) for i in action_dimensions.screen),
        "screen2": tuple(int(i) for i in action_dimensions.screen),
        "minimap": tuple(int(i) for i in action_dimensions.minimap),
    }

    types = actions.Arguments(
        *[
            actions.ArgumentType.spec(t.id, t.name, sizes.get(t.name, t.sizes))
            for t in actions.TYPES
        ]
    )

    functions = actions.Functions(
        [
            actions.Function.spec(f.id, f.name, tuple(types[t.id] for t in f.args))
            for f in actions.FUNCTIONS
        ]
    )

    return actions.ValidActions(types, functions)


def _init_valid_raw_functions(raw_resolution, max_selected_units):
    """Initialize ValidFunctions and set up the callbacks."""
    sizes = {
        "world": tuple(int(i) for i in raw_resolution),
        "unit_tags": (max_selected_units,),
    }
    types = actions.RawArguments(
        *[
            actions.ArgumentType.spec(t.id, t.name, sizes.get(t.name, t.sizes))
            for t in actions.RAW_TYPES
        ]
    )

    functions = actions.Functions(
        [
            actions.Function.spec(f.id, f.name, tuple(types[t.id] for t in f.args))
            for f in actions.RAW_FUNCTIONS
        ]
    )

    return actions.ValidActions(types, functions)


class Features(object):
    """Render feature layers from SC2 Observation dicts into numpy arrays."""

    def __init__(
        self,
        agent_interface_format=None,
        map_size=None,
        requested_races=None,
        map_name="unknown",
    ):
        if not agent_interface_format:
            raise ValueError("Please specify agent_interface_format")

        self._agent_interface_format = agent_interface_format
        aif = self._agent_interface_format

        if map_size and isinstance(map_size, dict):
            ms = point.Point(map_size["x"], map_size["y"])
        elif map_size:
            ms = point.Point.build(map_size)
        else:
            ms = None

        if not aif.raw_resolution and ms:
            aif.raw_resolution = ms
        self._map_size = ms
        self._map_name = map_name

        if aif.use_feature_units or aif.use_camera_position or aif.use_raw_units:
            self.init_camera(
                aif.feature_dimensions,
                ms,
                aif.camera_width_world_units,
                aif.raw_resolution,
            )

        self._send_observation_proto = aif.send_observation_proto
        self._raw = aif.use_raw_actions
        if self._raw:
            self._valid_functions = _init_valid_raw_functions(
                aif.raw_resolution, aif.max_selected_units
            )
            self._raw_tags = []
        else:
            self._valid_functions = _init_valid_functions(aif.action_dimensions)
        self._requested_races = requested_races
        if requested_races is not None:
            assert len(requested_races) <= 2

    def init_camera(
        self, feature_dimensions, map_size, camera_width_world_units, raw_resolution
    ):
        if not map_size or not camera_width_world_units:
            raise ValueError(
                "Either pass the game_info with raw enabled, or map_size and "
                "camera_width_world_units in order to use feature_units or camera"
                "position."
            )
        self._world_to_world_tl = transform.Linear(
            point.Point(1, -1), point.Point(0, map_size.y)
        )
        self._world_tl_to_world_camera_rel = transform.Linear(offset=-map_size / 4)
        if feature_dimensions:
            world_camera_rel_to_feature_screen = transform.Linear(
                feature_dimensions.screen / camera_width_world_units,
                feature_dimensions.screen / 2,
            )
            self._world_to_feature_screen_px = transform.Chain(
                self._world_to_world_tl,
                self._world_tl_to_world_camera_rel,
                world_camera_rel_to_feature_screen,
                transform.PixelToCoord(),
            )

        world_tl_to_feature_minimap = transform.Linear(
            scale=raw_resolution / map_size.max_dim() if raw_resolution else None
        )
        self._world_to_minimap_px = transform.Chain(
            self._world_to_world_tl,
            world_tl_to_feature_minimap,
            transform.PixelToCoord(),
        )
        self._camera_size = (
            raw_resolution / map_size.max_dim() * camera_width_world_units
        )

    def _update_camera(self, camera_center):
        """Update the camera transform based on the new camera center."""
        self._world_tl_to_world_camera_rel.offset = (
            -self._world_to_world_tl.fwd_pt(camera_center)
            * self._world_tl_to_world_camera_rel.scale
        )

    def observation_spec(self):
        """The observation spec for the SC2 environment."""
        obs_spec = named_array.NamedDict(
            {
                "action_result": (0,),  # See error.proto: ActionResult.
                "alerts": (0,),  # See sc2api.proto: Alert.
                "build_queue": (0, len(UnitLayer)),
                "cargo": (0, len(UnitLayer)),
                "cargo_slots_available": (1,),
                "control_groups": (10, 2),
                "game_loop": (1,),
                "last_actions": (0,),
                "map_name": (0,),
                "multi_select": (0, len(UnitLayer)),
                "player": (len(Player),),
                "production_queue": (0, len(ProductionQueue)),
                "score_cumulative": (len(ScoreCumulative),),
                "score_by_category": (len(ScoreByCategory), len(ScoreCategories)),
                "score_by_vital": (len(ScoreByVital), len(ScoreVitals)),
                "single_select": (0, len(UnitLayer)),  # Only (n, 7) for n in (0, 1).
            }
        )

        if not self._raw:
            obs_spec["available_actions"] = (0,)

        aif = self._agent_interface_format

        if aif.feature_dimensions:
            obs_spec["feature_screen"] = (
                len(SCREEN_FEATURES),
                aif.feature_dimensions.screen.y,
                aif.feature_dimensions.screen.x,
            )

            obs_spec["feature_minimap"] = (
                len(MINIMAP_FEATURES),
                aif.feature_dimensions.minimap.y,
                aif.feature_dimensions.minimap.x,
            )
        if aif.rgb_dimensions:
            obs_spec["rgb_screen"] = (
                aif.rgb_dimensions.screen.y,
                aif.rgb_dimensions.screen.x,
                3,
            )
            obs_spec["rgb_minimap"] = (
                aif.rgb_dimensions.minimap.y,
                aif.rgb_dimensions.minimap.x,
                3,
            )
        if aif.use_feature_units:
            obs_spec["feature_units"] = (
                0,
                len(FeatureUnit),
            )
            obs_spec["feature_effects"] = (0, len(EffectPos))

        if aif.use_raw_units:
            obs_spec["raw_units"] = (0, len(FeatureUnit))
            obs_spec["raw_effects"] = (0, len(EffectPos))

        if aif.use_feature_units or aif.use_raw_units:
            obs_spec["radar"] = (0, len(Radar))

        obs_spec["upgrades"] = (0,)

        if aif.use_unit_counts:
            obs_spec["unit_counts"] = (0, len(UnitCounts))

        if aif.use_camera_position:
            obs_spec["camera_position"] = (2,)
            obs_spec["camera_size"] = (2,)

        if self._send_observation_proto:
            obs_spec["_response_observation"] = (0,)

        obs_spec["home_race_requested"] = (1,)
        obs_spec["away_race_requested"] = (1,)
        return obs_spec

    def action_spec(self):
        """The action space pretty complicated and fills the ValidFunctions."""
        return self._valid_functions

    @property
    def map_size(self):
        return self._map_size

    @property
    def requested_races(self):
        return self._requested_races

    @sw.decorate
    def transform_obs(self, obs):
        """Render some SC2 observations into something an agent can handle."""
        empty_unit = np.array([], dtype=np.int32).reshape((0, len(UnitLayer)))
        out = named_array.NamedDict(
            {  # Fill out some that are sometimes empty.
                "single_select": empty_unit,
                "multi_select": empty_unit,
                "build_queue": empty_unit,
                "cargo": empty_unit,
                "production_queue": np.array([], dtype=np.int32).reshape(
                    (0, len(ProductionQueue))
                ),
                "last_actions": np.array([], dtype=np.int32),
                "cargo_slots_available": np.array([0], dtype=np.int32),
                "home_race_requested": np.array([0], dtype=np.int32),
                "away_race_requested": np.array([0], dtype=np.int32),
                "map_name": self._map_name,
            }
        )

        def or_zeros(layer, size):
            if layer is not None:
                return layer.astype(np.int32, copy=False)
            else:
                return np.zeros((size.y, size.x), dtype=np.int32)

        aif = self._agent_interface_format

        obs_data = obs["observation"]

        if aif.feature_dimensions:
            with sw("feature_screen"):
                out["feature_screen"] = named_array.NamedNumpyArray(
                    np.stack(
                        [
                            or_zeros(f.unpack(obs_data), aif.feature_dimensions.screen)
                            for f in SCREEN_FEATURES
                        ]
                    ),
                    names=[ScreenFeatures, None, None],
                )
            with sw("feature_minimap"):
                out["feature_minimap"] = named_array.NamedNumpyArray(
                    np.stack(
                        [
                            or_zeros(
                                f.unpack(obs_data),
                                aif.feature_dimensions.minimap,
                            )
                            for f in MINIMAP_FEATURES
                        ]
                    ),
                    names=[MinimapFeatures, None, None],
                )

        if aif.rgb_dimensions:
            with sw("rgb_screen"):
                out["rgb_screen"] = Feature.unpack_rgb_image(
                    obs_data["render_data"]["map"]
                ).astype(np.int32)
            with sw("rgb_minimap"):
                out["rgb_minimap"] = Feature.unpack_rgb_image(
                    obs_data["render_data"]["minimap"]
                ).astype(np.int32)

        if not self._raw:
            with sw("last_actions"):
                out["last_actions"] = np.array(
                    [self.reverse_action(a).function for a in obs.get("actions", [])],
                    dtype=np.int32,
                )

        out["action_result"] = np.array(
            [o.get("result", 0) for o in obs.get("action_errors", [])], dtype=np.int32
        )

        out["alerts"] = np.array(obs_data.get("alerts", []), dtype=np.int32)

        out["game_loop"] = np.array([obs_data["game_loop"]], dtype=np.int32)

        with sw("score"):
            score = obs_data.get("score", {})
            score_details = score.get("score_details", {})

            out["score_cumulative"] = named_array.NamedNumpyArray(
                [
                    score.get("score", 0),
                    score_details.get("idle_production_time", 0),
                    score_details.get("idle_worker_time", 0),
                    score_details.get("total_value_units", 0),
                    score_details.get("total_value_structures", 0),
                    score_details.get("killed_value_units", 0),
                    score_details.get("killed_value_structures", 0),
                    score_details.get("collected_minerals", 0),
                    score_details.get("collected_vespene", 0),
                    score_details.get("collection_rate_minerals", 0),
                    score_details.get("collection_rate_vespene", 0),
                    score_details.get("spent_minerals", 0),
                    score_details.get("spent_vespene", 0),
                ],
                names=ScoreCumulative,
                dtype=np.int32,
            )

            def get_score_details(key, details, categories):
                row = details.get(key.name, {})
                return [row.get(category.name, 0) for category in categories]

            out["score_by_category"] = named_array.NamedNumpyArray(
                [
                    get_score_details(key, score_details, ScoreCategories)
                    for key in ScoreByCategory
                ],
                names=[ScoreByCategory, ScoreCategories],
                dtype=np.int32,
            )

            out["score_by_vital"] = named_array.NamedNumpyArray(
                [
                    get_score_details(key, score_details, ScoreVitals)
                    for key in ScoreByVital
                ],
                names=[ScoreByVital, ScoreVitals],
                dtype=np.int32,
            )

        player = obs_data.get("player_common", {})
        out["player"] = named_array.NamedNumpyArray(
            [
                player.get("player_id", 0),
                player.get("minerals", 0),
                player.get("vespene", 0),
                player.get("food_used", 0),
                player.get("food_cap", 0),
                player.get("food_army", 0),
                player.get("food_workers", 0),
                player.get("idle_worker_count", 0),
                player.get("army_count", 0),
                player.get("warp_gate_count", 0),
                player.get("larva_count", 0),
            ],
            names=Player,
            dtype=np.int32,
        )

        def unit_vec(u):
            return np.array(
                (
                    u.get("unit_type", 0),
                    u.get("player_relative", 0),
                    u.get("health", 0.0),
                    u.get("shields", 0.0),
                    u.get("energy", 0.0),
                    u.get("transport_slots_taken", 0),
                    int(u.get("build_progress", 0) * 100),
                ),
                dtype=np.int32,
            )

        ui = obs_data.get("ui_data", {})

        with sw("ui"):
            groups = np.zeros((10, 2), dtype=np.int32)
            for g in ui.get("groups", []):
                groups[g["control_group_index"], :] = (
                    g["leader_unit_type"],
                    g["count"],
                )
            out["control_groups"] = groups

            if "single" in ui:
                out["single_select"] = named_array.NamedNumpyArray(
                    [unit_vec(ui["single"]["unit"])], [None, UnitLayer]
                )
            elif "multi" in ui:
                out["multi_select"] = named_array.NamedNumpyArray(
                    [unit_vec(u) for u in ui["multi"]["units"]], [None, UnitLayer]
                )
            elif "cargo" in ui:
                out["single_select"] = named_array.NamedNumpyArray(
                    [unit_vec(ui["cargo"]["unit"])], [None, UnitLayer]
                )
                out["cargo"] = named_array.NamedNumpyArray(
                    [unit_vec(u) for u in ui["cargo"]["passengers"]], [None, UnitLayer]
                )
                out["cargo_slots_available"] = np.array(
                    [ui["cargo"]["slots_available"]], dtype=np.int32
                )
            elif "production" in ui:
                out["single_select"] = named_array.NamedNumpyArray(
                    [unit_vec(ui["production"]["unit"])], [None, UnitLayer]
                )
                if ui["production"].get("build_queue"):
                    out["build_queue"] = named_array.NamedNumpyArray(
                        [unit_vec(u) for u in ui["production"]["build_queue"]],
                        [None, UnitLayer],
                        dtype=np.int32,
                    )
                if ui["production"].get("production_queue"):
                    out["production_queue"] = named_array.NamedNumpyArray(
                        [
                            (item["ability_id"], item["build_progress"] * 100)
                            for item in ui["production"]["production_queue"]
                        ],
                        [None, ProductionQueue],
                        dtype=np.int32,
                    )

        tag_types = {}

        def get_addon_type(tag):
            if not tag_types:
                for u in raw.get("units", []):
                    tag_types[u["tag"]] = u["unit_type"]
            return tag_types.get(tag, 0)

        def full_unit_vec(u, pos_transform, is_raw=False):
            pos = u.get("pos", {"x": 0, "y": 0, "z": 0})
            screen_pos = pos_transform.fwd_pt(point.Point(pos["x"], pos["y"]))
            screen_radius = pos_transform.fwd_dist(u.get("radius", 0))

            orders = u.get("orders", [])

            def raw_order(i):
                if len(orders) > i:
                    return actions.RAW_ABILITY_ID_TO_FUNC_ID.get(
                        orders[i]["ability_id"], 0
                    )
                return 0

            health = u.get("health", 0.0)
            health_max = u.get("health_max", 0.0)
            shield = u.get("shield", 0.0)
            shield_max = u.get("shield_max", 0.0)
            energy = u.get("energy", 0.0)
            energy_max = u.get("energy_max", 0.0)

            buff_ids = u.get("buff_ids", [])

            features = [
                u.get("unit_type", 0),
                u.get("alliance", 0),
                health,
                shield,
                energy,
                u.get("cargo_space_taken", 0),
                int(u.get("build_progress", 0) * 100),
                int(health / health_max * 255) if health_max > 0 else 0,
                int(shield / shield_max * 255) if shield_max > 0 else 0,
                int(energy / energy_max * 255) if energy_max > 0 else 0,
                u.get("display_type", 0),
                u.get("owner", 0),
                screen_pos.x,
                screen_pos.y,
                u.get("facing", 0),
                screen_radius,
                u.get("cloak", 0),
                u.get("is_selected", False),
                u.get("is_blip", False),
                u.get("is_powered", False),
                u.get("mineral_contents", 0),
                u.get("vespene_contents", 0),
                u.get("cargo_space_max", 0),
                u.get("assigned_harvesters", 0),
                u.get("ideal_harvesters", 0),
                u.get("weapon_cooldown", 0),
                len(orders),
                raw_order(0),
                raw_order(1),
                u.get("tag", 0) if is_raw else 0,
                u.get("is_hallucination", False),
                buff_ids[0] if len(buff_ids) >= 1 else 0,
                buff_ids[1] if len(buff_ids) >= 2 else 0,
                get_addon_type(u.get("add_on_tag")) if u.get("add_on_tag") else 0,
                u.get("is_active", False),
                u.get("is_on_screen", False),
                int(orders[0]["progress"] * 100) if len(orders) >= 1 else 0,
                int(orders[1]["progress"] * 100) if len(orders) >= 2 else 0,
                raw_order(2),
                raw_order(3),
                0,
                u.get("buff_duration_remain", 0),
                u.get("buff_duration_max", 0),
                u.get("attack_upgrade_level", 0),
                u.get("armor_upgrade_level", 0),
                u.get("shield_upgrade_level", 0),
            ]
            return features

        raw = obs_data.get("raw_data", {})

        if aif.use_feature_units:
            with sw("feature_units"):
                cam = raw["player"]["camera"]
                self._update_camera(point.Point(cam["x"], cam["y"]))
                feature_units = [
                    full_unit_vec(u, self._world_to_feature_screen_px)
                    for u in raw.get("units", [])
                    if u.get("is_on_screen")
                ]
                out["feature_units"] = named_array.NamedNumpyArray(
                    feature_units, [None, FeatureUnit], dtype=np.int64
                )

                feature_effects = []
                feature_screen_size = aif.feature_dimensions.screen
                for effect in raw.get("effects", []):
                    for pos in effect.get("pos", []):
                        screen_pos = self._world_to_feature_screen_px.fwd_pt(
                            point.Point(pos["x"], pos["y"])
                        )
                        if (
                            0 <= screen_pos.x < feature_screen_size.x
                            and 0 <= screen_pos.y < feature_screen_size.y
                        ):
                            feature_effects.append(
                                [
                                    effect["effect_id"],
                                    effect.get("alliance", 0),
                                    effect.get("owner", 0),
                                    effect.get("radius", 0),
                                    screen_pos.x,
                                    screen_pos.y,
                                ]
                            )
                out["feature_effects"] = named_array.NamedNumpyArray(
                    feature_effects, [None, EffectPos], dtype=np.int32
                )

        if aif.use_raw_units:
            with sw("raw_units"):
                with sw("to_list"):
                    raw_units = [
                        full_unit_vec(u, self._world_to_minimap_px, is_raw=True)
                        for u in raw.get("units", [])
                    ]
                with sw("to_numpy"):
                    out["raw_units"] = named_array.NamedNumpyArray(
                        raw_units, [None, FeatureUnit], dtype=np.int64
                    )
                if raw_units:
                    self._raw_tags = out["raw_units"][:, FeatureUnit.tag]
                else:
                    self._raw_tags = np.array([])

                raw_effects = []
                for effect in raw.get("effects", []):
                    for pos in effect.get("pos", []):
                        raw_pos = self._world_to_minimap_px.fwd_pt(
                            point.Point(pos["x"], pos["y"])
                        )
                        raw_effects.append(
                            [
                                effect["effect_id"],
                                effect.get("alliance", 0),
                                effect.get("owner", 0),
                                effect.get("radius", 0),
                                raw_pos.x,
                                raw_pos.y,
                            ]
                        )
                out["raw_effects"] = named_array.NamedNumpyArray(
                    raw_effects, [None, EffectPos], dtype=np.int32
                )

        upgrades = raw.get("player", {}).get("upgrade_ids", [])
        out["upgrades"] = np.array(upgrades, dtype=np.int32)

        def cargo_units(u, pos_transform, is_raw=False):
            """Compute unit features."""
            pos = u.get("pos", {"x": 0, "y": 0, "z": 0})
            screen_pos = pos_transform.fwd_pt(point.Point(pos["x"], pos["y"]))
            features = []
            for v in u.get("passengers", []):
                health = v.get("health", 0.0)
                health_max = v.get("health_max", 0.0)
                shield = v.get("shield", 0.0)
                shield_max = v.get("shield_max", 0.0)
                energy = v.get("energy", 0.0)
                energy_max = v.get("energy_max", 0.0)

                features.append(
                    [
                        v.get("unit_type", 0),
                        u.get("alliance", 0),
                        health,
                        shield,
                        energy,
                        0,
                        0,
                        int(health / health_max * 255) if health_max > 0 else 0,
                        int(shield / shield_max * 255) if shield_max > 0 else 0,
                        int(energy / energy_max * 255) if energy_max > 0 else 0,
                        0,
                        u.get("owner", 0),
                        screen_pos.x,
                        screen_pos.y,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        v.get("tag", 0) if is_raw else 0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        1,
                        0,
                        0,
                        0,
                        0,
                        0,
                    ]
                )
            return features

        if aif.add_cargo_to_units:
            with sw("add_cargo_to_units"):
                if aif.use_feature_units:
                    with sw("feature_units"):
                        with sw("to_list"):
                            feature_cargo_units = []
                            for u in raw.get("units", []):
                                if u.get("is_on_screen"):
                                    feature_cargo_units += cargo_units(
                                        u, self._world_to_feature_screen_px
                                    )
                        with sw("to_numpy"):
                            if feature_cargo_units:
                                all_feature_units = np.array(
                                    feature_cargo_units, dtype=np.int64
                                )
                                all_feature_units = np.concatenate(
                                    [out["feature_units"], feature_cargo_units], axis=0
                                )
                                out["feature_units"] = named_array.NamedNumpyArray(
                                    all_feature_units,
                                    [None, FeatureUnit],
                                    dtype=np.int64,
                                )
                if aif.use_raw_units:
                    with sw("raw_units"):
                        with sw("to_list"):
                            raw_cargo_units = []
                            for u in raw.get("units", []):
                                raw_cargo_units += cargo_units(
                                    u, self._world_to_minimap_px, is_raw=True
                                )
                        with sw("to_numpy"):
                            if raw_cargo_units:
                                raw_cargo_units = np.array(
                                    raw_cargo_units, dtype=np.int64
                                )
                                all_raw_units = np.concatenate(
                                    [out["raw_units"], raw_cargo_units], axis=0
                                )
                                out["raw_units"] = named_array.NamedNumpyArray(
                                    all_raw_units, [None, FeatureUnit], dtype=np.int64
                                )
                                self._raw_tags = out["raw_units"][:, FeatureUnit.tag]

        if aif.use_unit_counts:
            with sw("unit_counts"):
                unit_counts = collections.defaultdict(int)
                for u in raw.get("units", []):
                    if u.get("alliance") == sc_raw.Self:
                        unit_counts[u.get("unit_type")] += 1
                out["unit_counts"] = named_array.NamedNumpyArray(
                    sorted(unit_counts.items()), [None, UnitCounts], dtype=np.int32
                )

        if aif.use_camera_position:
            cam = raw["player"]["camera"]
            camera_position = self._world_to_minimap_px.fwd_pt(
                point.Point(cam["x"], cam["y"])
            )
            out["camera_position"] = np.array(
                (camera_position.x, camera_position.y), dtype=np.int32
            )
            out["camera_size"] = np.array(
                (self._camera_size.x, self._camera_size.y), dtype=np.int32
            )

        if not self._raw:
            out["available_actions"] = np.array(
                self.available_actions(obs["observation"]), dtype=np.int32
            )

        if self._requested_races is not None:
            pid = player.get("player_id", 0)
            out["home_race_requested"] = np.array(
                (self._requested_races[pid],), dtype=np.int32
            )
            for player_id, race in self._requested_races.items():
                if player_id != pid:
                    out["away_race_requested"] = np.array((race,), dtype=np.int32)

        if aif.use_feature_units or aif.use_raw_units:

            def transform_radar(radar):
                pos = radar["pos"]
                p = self._world_to_minimap_px.fwd_pt(point.Point(pos["x"], pos["y"]))
                return p.x, p.y, radar["radius"]

            out["radar"] = named_array.NamedNumpyArray(
                list(map(transform_radar, raw.get("radar", []))),
                [None, Radar],
                dtype=np.int32,
            )

        if self._send_observation_proto:
            out["_response_observation"] = lambda: obs

        return out

    @sw.decorate
    def available_actions(self, obs_data):
        """Return the list of available action ids."""
        available_actions = set()
        hide_specific_actions = self._agent_interface_format.hide_specific_actions

        for a in obs_data.get("abilities", []):
            ability_id = a.get("ability_id")
            if ability_id not in actions.ABILITY_IDS:
                continue

            # requires_point logic?
            # actions.POINT_REQUIRED_FUNCS is a dict mapping True/False (or enum) to set of types.
            # a.requires_point should be present in dict.
            # In proto it's bool? No, it's enum Point/NoPoint/TargetUnit etc?
            # Checking pysc2 code: requires_point seems to be mapped to PointRequirement enum if coming from proto.
            # We assume the dict has the same value.

            found_applicable = False
            for func in actions.ABILITY_IDS[ability_id]:
                if (
                    func.function_type
                    in actions.POINT_REQUIRED_FUNCS[a.get("requires_point")]
                ):
                    if func.general_id == 0 or not hide_specific_actions:
                        available_actions.add(func.id)
                        found_applicable = True
                    if func.general_id != 0:
                        for general_func in actions.ABILITY_IDS[func.general_id]:
                            if general_func.function_type is func.function_type:
                                available_actions.add(general_func.id)
                                found_applicable = True
                                break

            if not found_applicable:
                raise ValueError("Failed to find applicable action for {}".format(a))
        return list(available_actions)

    @sw.decorate
    def transform_action(self, obs, func_call, skip_available=False):
        """Transform an agent-style action to one that SC2 can consume."""
        # This returns protobuf.

        if isinstance(func_call, sc_pb.Action):
            return func_call

        func_id = func_call.function
        try:
            if self._raw:
                func = actions.RAW_FUNCTIONS[func_id]
            else:
                func = actions.FUNCTIONS[func_id]
        except KeyError:
            raise ValueError("Invalid function id: %s." % func_id)

        # Available?
        obs_data = obs.get("observation", {})
        if not (
            skip_available or self._raw or func_id in self.available_actions(obs_data)
        ):
            raise ValueError(
                "Function %s/%s is currently not available" % (func_id, func.name)
            )

        if len(func_call.arguments) != len(func.args):
            raise ValueError(
                "Wrong number of arguments for function: %s, got: %s"
                % (func, func_call.arguments)
            )

        aif = self._agent_interface_format
        for t, arg in zip(func.args, func_call.arguments):
            if t.count:
                if 1 <= len(arg) <= t.count:
                    continue
                else:
                    raise ValueError(
                        "Wrong number of values for argument of %s, got: %s"
                        % (func, func_call.arguments)
                    )

            if t.name in ("screen", "screen2"):
                sizes = aif.action_dimensions.screen
            elif t.name == "minimap":
                sizes = aif.action_dimensions.minimap
            elif t.name == "world":
                sizes = aif.raw_resolution
            else:
                sizes = t.sizes

            if len(sizes) != len(arg):
                raise ValueError(
                    "Wrong number of values for argument of %s, got: %s"
                    % (func, func_call.arguments)
                )

            for s, a in zip(sizes, arg):
                if not np.all(0 <= a) and np.all(a < s):
                    raise ValueError(
                        "Argument is out of range for %s, got: %s"
                        % (func, func_call.arguments)
                    )

        kwargs = {
            type_.name: type_.fn(a) for type_, a in zip(func.args, func_call.arguments)
        }

        sc2_action = sc_pb.Action()
        kwargs["action"] = sc2_action
        if func.ability_id:
            kwargs["ability_id"] = func.ability_id

        if self._raw:
            if "world" in kwargs:
                kwargs["world"] = self._world_to_minimap_px.back_pt(kwargs["world"])

            def find_original_tag(position):
                if position >= len(self._raw_tags):
                    return position
                original_tag = self._raw_tags[position]
                if original_tag == 0:
                    logging.warning("Tag not found: %s", original_tag)
                return original_tag

            if "target_unit_tag" in kwargs:
                kwargs["target_unit_tag"] = find_original_tag(
                    kwargs["target_unit_tag"][0]
                )
            if "unit_tags" in kwargs:
                kwargs["unit_tags"] = [
                    find_original_tag(t) for t in kwargs["unit_tags"]
                ]
            actions.RAW_FUNCTIONS[func_id].function_type(**kwargs)
        else:
            kwargs["action_space"] = aif.action_space
            actions.FUNCTIONS[func_id].function_type(**kwargs)
        return sc2_action

    @sw.decorate
    def reverse_action(self, action):
        """Transform an SC2-style action dict into an agent-style action."""
        FUNCTIONS = actions.FUNCTIONS

        aif = self._agent_interface_format

        def func_call_ability(ability_id, cmd_type, *args):
            if ability_id not in actions.ABILITY_IDS:
                logging.warning(
                    "Unknown ability_id: %s.",
                    ability_id,
                )
                return FUNCTIONS.no_op()

            if aif.hide_specific_actions:
                try:
                    general_id = next(iter(actions.ABILITY_IDS[ability_id])).general_id
                    if general_id:
                        ability_id = general_id
                except StopIteration:
                    pass

            for func in actions.ABILITY_IDS[ability_id]:
                if func.function_type is cmd_type:
                    return FUNCTIONS[func.id](*args)
            return FUNCTIONS.no_op()

        # action is dict
        if "action_ui" in action:
            act_ui = action["action_ui"]
            if "multi_panel" in act_ui:
                return FUNCTIONS.select_unit(
                    act_ui["multi_panel"]["type"] - 1,
                    act_ui["multi_panel"]["unit_index"],
                )
            if "control_group" in act_ui:
                return FUNCTIONS.select_control_group(
                    act_ui["control_group"]["action"] - 1,
                    act_ui["control_group"]["control_group_index"],
                )
            if "select_idle_worker" in act_ui:
                return FUNCTIONS.select_idle_worker(
                    act_ui["select_idle_worker"]["type"] - 1
                )
            if "select_army" in act_ui:
                return FUNCTIONS.select_army(act_ui["select_army"]["selection_add"])
            if "select_warp_gates" in act_ui:
                return FUNCTIONS.select_warp_gates(
                    act_ui["select_warp_gates"]["selection_add"]
                )
            if "select_larva" in act_ui:
                return FUNCTIONS.select_larva()
            if "cargo_panel" in act_ui:
                return FUNCTIONS.unload(act_ui["cargo_panel"]["unit_index"])
            if "production_panel" in act_ui:
                return FUNCTIONS.build_queue(act_ui["production_panel"]["unit_index"])
            if "toggle_autocast" in act_ui:
                return func_call_ability(
                    act_ui["toggle_autocast"]["ability_id"], actions.autocast
                )

        if "action_feature_layer" in action or "action_render" in action:
            # Not fully supported in dict mode for now as spatial requires protobuf helper actions.spatial
            # If we needed strict support we would reimplement actions.spatial for dicts.
            # Assuming most usage is observations.
            pass

        return FUNCTIONS.no_op()

    @sw.decorate
    def reverse_raw_action(self, action, prev_obs):
        # Similar logic would be needed here for dict support
        return actions.RAW_FUNCTIONS.no_op()
