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
"""A basic Color class."""

import collections
import colorsys
import math
import random
from typing import List, Tuple

import numpy

from pysc2_evolved.lib import static_data


class Color(collections.namedtuple("Color", ["r", "g", "b"])):
    """A basic Color class."""

    __slots__ = ()

    def set(
        self,
        r: int | float | None = None,
        g: int | float | None = None,
        b: int | float | None = None,
    ):
        return Color(r or self.r, b or self.b, g or self.g)

    def round(self) -> "Color":
        return Color(int(round(self.r)), int(round(self.g)), int(round(self.b)))

    def floor(self) -> "Color":
        return Color(
            int(math.floor(self.r)), int(math.floor(self.g)), int(math.floor(self.b))
        )

    def ceil(self) -> "Color":
        return Color(
            int(math.ceil(self.r)), int(math.ceil(self.g)), int(math.ceil(self.b))
        )

    def __str__(self) -> str:
        return "%d,%d,%d" % self

    def __add__(self, o: "Color") -> "Color":
        return Color(self.r + o.r, self.g + o.g, self.b + o.b)

    def __sub__(self, o: "Color") -> "Color":
        return Color(self.r - o.r, self.g - o.g, self.b - o.b)

    def __mul__(self, val: int | float) -> "Color":
        return Color(self.r * val, self.g * val, self.b * val)

    def __truediv__(self, val: int | float) -> "Color":
        return Color(self.r / val, self.g / val, self.b / val)

    def __floordiv__(self, val: int | float) -> "Color":
        return Color(self.r // val, self.g // val, self.b // val)

    __div__ = __truediv__


black = Color(0, 0, 0)
white = Color(255, 255, 255)
red = Color(255, 0, 0)
green = Color(0, 255, 0)
blue = Color(0, 0, 255)
cyan = Color(0, 255, 255)
yellow = Color(255, 255, 0)
purple = Color(255, 0, 255)


def smooth_hue_palette(scale: List[int]) -> numpy.ndarray:
    """Takes an array of ints and returns a corresponding colored rgb array."""
    # http://en.wikipedia.org/wiki/HSL_and_HSV#From_HSL
    # Based on http://stackoverflow.com/a/17382854 , with simplifications and
    # optimizations. Assumes S=1, L=0.5, meaning C=1 and m=0.
    # 0 stays black, everything else moves into a hue.

    # Some initial values and scaling. Check wikipedia for variable meanings.
    array = numpy.arange(scale)
    h = array * (6 / scale)  # range of [0,6)
    x = 255 * (1 - numpy.absolute(numpy.mod(h, 2) - 1))
    c = 255

    # Initialize outputs to zero/black
    out = numpy.zeros(h.shape + (3,), float)
    r = out[..., 0]
    g = out[..., 1]
    b = out[..., 2]

    mask = (0 < h) & (h < 1)
    r[mask] = c
    g[mask] = x[mask]

    mask = (1 <= h) & (h < 2)
    r[mask] = x[mask]
    g[mask] = c

    mask = (2 <= h) & (h < 3)
    g[mask] = c
    b[mask] = x[mask]

    mask = (3 <= h) & (h < 4)
    g[mask] = x[mask]
    b[mask] = c

    mask = (4 <= h) & (h < 5)
    r[mask] = x[mask]
    b[mask] = c

    mask = 5 <= h
    r[mask] = c
    b[mask] = x[mask]

    return out


def shuffled_hue(scale: List[int]) -> numpy.ndarray:
    palette = list(smooth_hue_palette(scale))
    random.Random(21).shuffle(palette)  # Return a fixed shuffle
    return numpy.array(palette)


def piece_wise_linear(scale: int, points: List[Tuple[int, Color]]) -> numpy.ndarray:
    """Create a palette that is piece-wise linear given some colors at points."""
    assert len(points) >= 2
    assert points[0][0] == 0
    assert points[-1][0] == 1
    assert all(i < j for i, j in zip(points[:-1], points[1:]))
    out = numpy.zeros((scale, 3))
    p1, c1 = points[0]
    p2, c2 = points[1]
    next_pt = 2

    for i in range(1, scale):  # Leave 0 as black.
        v = i / scale
        if v > p2:
            p1, c1 = p2, c2
            p2, c2 = points[next_pt]
            next_pt += 1
        frac = (v - p1) / (p2 - p1)
        out[i, :] = c1 * (1 - frac) + c2 * frac
    return out


def winter(scale: int) -> numpy.ndarray:
    return piece_wise_linear(
        scale, [(0, Color(0, 0.5, 0.4) * 255), (1, Color(1, 1, 0.4) * 255)]
    )


def hot(scale: int) -> numpy.ndarray:
    return piece_wise_linear(
        scale,
        [
            (0, Color(0.5, 0, 0) * 255),
            (0.2, Color(1, 0, 0) * 255),
            (0.6, Color(1, 1, 0) * 255),
            (1, Color(1, 1, 1) * 255),
        ],
    )


def height_map(scale: int) -> numpy.ndarray:
    return piece_wise_linear(
        scale,
        [
            (0, Color(0, 0, 0)),  # Abyss
            (40 / 255, Color(67, 109, 95)),  # Water, little below this height.
            (50 / 255, Color(168, 152, 129)),  # Beach
            (60 / 255, Color(154, 124, 90)),  # Sand, the mode height.
            (70 / 255, Color(117, 150, 96)),  # Grass
            (80 / 255, Color(166, 98, 97)),  # Dirt, should be the top.
            (1, Color(255, 255, 100)),  # Heaven. Shouldn't be seen.
        ],
    )


# Palette used to color player_relative features.
PLAYER_RELATIVE_PALETTE = numpy.array(
    [
        black,  # Background.
        Color(0, 142, 0),  # Self. (Green).
        yellow,  # Ally.
        Color(129, 166, 196),  # Neutral. (Cyan.)
        Color(113, 25, 34),  # Enemy. (Red).
    ]
)

PLAYER_ABSOLUTE_PALETTE = numpy.array(
    [
        black,  # Background
        Color(0, 142, 0),  # 1: Green
        Color(113, 25, 34),  # 2: Red
        Color(223, 215, 67),  # 3: Yellow
        Color(66, 26, 121),  # 4: Purple
        Color(222, 144, 50),  # 5: Orange
        Color(46, 72, 237),  # 6: Blue
        Color(207, 111, 176),  # 7: Pink
        Color(189, 251, 157),  # 8: Light green
        white * 0.1,  # 9: Does the game ever have more than 8 players?
        white * 0.1,  # 10: Does the game ever have more than 8 players?
        white * 0.1,  # 11: Does the game ever have more than 8 players?
        white * 0.1,  # 12: Does the game ever have more than 8 players?
        white * 0.1,  # 13: Does the game ever have more than 8 players?
        white * 0.1,  # 14: Does the game ever have more than 8 players?
        white * 0.1,  # 15: Does the game ever have more than 8 players?
        Color(129, 166, 196),  # 16 Neutral: Cyan
    ]
)

VISIBILITY_PALETTE = numpy.array(
    [
        black,  # Hidden
        white * 0.25,  # Fogged
        white * 0.6,  # Visible
    ]
)

CAMERA_PALETTE = numpy.array([black, white * 0.6])
CREEP_PALETTE = numpy.array([black, purple * 0.4])
POWER_PALETTE = numpy.array([black, cyan * 0.7])
SELECTED_PALETTE = numpy.array([black, green * 0.7])


def unit_type(scale: int | None = None):
    """Returns a palette that maps unit types to rgb colors."""
    return categorical(static_data.UNIT_TYPES, scale)


def buffs(scale: int | None = None):
    """Returns a palette that maps buffs to rgb colors."""
    return categorical(static_data.BUFFS, scale)


def _make_distinct_colors(n: int) -> numpy.ndarray:
    """Generate n perceptually distinct colors using golden-ratio hue spacing.

    Alternates between two lightness tiers (dark/light) so adjacent indices
    differ in both hue and lightness, maximising visual separation.
    Deterministic — same n always produces the same palette.
    """
    golden = 0.618033988749895
    h = 0.0
    result = []
    for i in range(n):
        lightness = 0.45 if i % 2 == 0 else 0.70
        r, g, b = colorsys.hls_to_rgb(h, lightness, 0.85)
        result.append([int(r * 255), int(g * 255), int(b * 255)])
        h = (h + golden) % 1.0
    return numpy.array(result, dtype=numpy.uint8)


def categorical(options: List[int], scale: int | None = None) -> numpy.ndarray:
    # Can specify a scale to match the api or to accept unknown unit types.
    palette_size = scale or max(options) + 1
    palette = shuffled_hue(palette_size)
    colors = _make_distinct_colors(len(options))
    for i, v in enumerate(options):
        palette[v] = colors[i]
    return palette


effects = numpy.array(
    [
        [0, 0, 0],
        [72, 173, 207],
        [203, 76, 49],
        [122, 98, 209],
        [109, 183, 67],
        [192, 80, 181],
        [86, 185, 138],
        [211, 63, 115],
        [81, 128, 60],
        [182, 135, 208],
        [182, 174, 73],
        [95, 123, 196],
        [220, 146, 71],
        [187, 102, 147],
        [138, 109, 48],
        [197, 103, 99],
    ]
)
