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
"""Tests for the point library."""

import pytest

from pysc2_evolved.lib import point


class FakePoint(object):
    def __init__(self):
        self.x = 5
        self.y = 8


@pytest.mark.minor
class TestPoint:
    def test_build(self):
        assert point.Point(5, 8) == point.Point.build(FakePoint())

    def test_assign_to(self):
        f = FakePoint()
        assert f.x == 5
        assert f.y == 8
        point.Point(1, 2).assign_to(f)
        assert f.x == 1
        assert f.y == 2

    def test_dist(self):
        a = point.Point(1, 1)
        b = point.Point(4, 5)
        assert a.dist(b) == 5

    def test_dist_sq(self):
        a = point.Point(1, 1)
        b = point.Point(4, 5)
        assert a.dist_sq(b) == 25

    def test_len(self):
        p = point.Point(3, 4)
        assert p.len() == 5

    def test_scale(self):
        p = point.Point(3, 4)
        assert p.scale(2).len() == pytest.approx(2)

    def test_scale_max_size(self):
        p = point.Point(3, 4)
        assert p == p.scale_max_size(p)
        assert point.Point(6, 8) == p.scale_max_size(point.Point(8, 8))
        assert point.Point(6, 8) == p.scale_max_size(point.Point(100, 8))
        assert point.Point(6, 8) == p.scale_max_size(point.Point(6, 100))

    def test_scale_min_size(self):
        p = point.Point(3, 4)
        assert p == p.scale_min_size(p)
        assert point.Point(6, 8) == p.scale_min_size(point.Point(6, 6))
        assert point.Point(6, 8) == p.scale_min_size(point.Point(2, 8))
        assert point.Point(6, 8) == p.scale_min_size(point.Point(6, 2))

    def test_min_dim(self):
        assert point.Point(5, 10).min_dim() == 5

    def test_max_dim(self):
        assert point.Point(5, 10).max_dim() == 10

    def test_transpose(self):
        assert point.Point(4, 3) == point.Point(3, 4).transpose()

    def test_round(self):
        p = point.Point(1.3, 2.6).round()
        assert point.Point(1, 3) == p
        assert isinstance(p.x, int)
        assert isinstance(p.y, int)

    def test_ceil(self):
        p = point.Point(1.3, 2.6).ceil()
        assert point.Point(2, 3) == p
        assert isinstance(p.x, int)
        assert isinstance(p.y, int)

    def test_floor(self):
        p = point.Point(1.3, 2.6).floor()
        assert point.Point(1, 2) == p
        assert isinstance(p.x, int)
        assert isinstance(p.y, int)

    def test_rotate(self):
        p = point.Point(0, 100)
        assert point.Point(-100, 0) == p.rotate_deg(90).round()
        assert point.Point(100, 0) == p.rotate_deg(-90).round()
        assert point.Point(0, -100) == p.rotate_deg(180).round()

    def test_contained_circle(self):
        assert point.Point(2, 2).contained_circle(point.Point(1, 1), 2)
        assert not point.Point(2, 2).contained_circle(point.Point(1, 1), 0.5)

    def test_bound(self):
        tl = point.Point(1, 2)
        br = point.Point(3, 4)
        assert tl == point.Point(0, 0).bound(tl, br)
        assert br == point.Point(10, 10).bound(tl, br)
        assert point.Point(1.5, 2) == point.Point(1.5, 0).bound(tl, br)


@pytest.mark.minor
class TestRect:
    def test_init(self):
        r = point.Rect(1, 2, 3, 4)
        assert r.t == 1
        assert r.l == 2
        assert r.b == 3
        assert r.r == 4
        assert r.tl == point.Point(2, 1)
        assert r.tr == point.Point(4, 1)
        assert r.bl == point.Point(2, 3)
        assert r.br == point.Point(4, 3)

    def test_init_bad(self):
        with pytest.raises(TypeError):
            point.Rect(4, 3, 2, 1)  # require t <= b, l <= r
        with pytest.raises(TypeError):
            point.Rect(1)
        with pytest.raises(TypeError):
            point.Rect(1, 2, 3)
        with pytest.raises(TypeError):
            point.Rect()

    def test_init_one_point(self):
        r = point.Rect(point.Point(1, 2))
        assert r.t == 0
        assert r.l == 0
        assert r.b == 2
        assert r.r == 1
        assert r.tl == point.Point(0, 0)
        assert r.tr == point.Point(1, 0)
        assert r.bl == point.Point(0, 2)
        assert r.br == point.Point(1, 2)
        assert r.size == point.Point(1, 2)
        assert r.center == point.Point(1, 2) / 2
        assert r.area == 2

    def test_init_two_points(self):
        r = point.Rect(point.Point(1, 2), point.Point(3, 4))
        assert r.t == 2
        assert r.l == 1
        assert r.b == 4
        assert r.r == 3
        assert r.tl == point.Point(1, 2)
        assert r.tr == point.Point(3, 2)
        assert r.bl == point.Point(1, 4)
        assert r.br == point.Point(3, 4)
        assert r.size == point.Point(2, 2)
        assert r.center == point.Point(2, 3)
        assert r.area == 4

    def test_init_two_points_reversed(self):
        r = point.Rect(point.Point(3, 4), point.Point(1, 2))
        assert r.t == 2
        assert r.l == 1
        assert r.b == 4
        assert r.r == 3
        assert r.tl == point.Point(1, 2)
        assert r.tr == point.Point(3, 2)
        assert r.bl == point.Point(1, 4)
        assert r.br == point.Point(3, 4)
        assert r.size == point.Point(2, 2)
        assert r.center == point.Point(2, 3)
        assert r.area == 4

    def test_area(self):
        r = point.Rect(point.Point(1, 1), point.Point(3, 4))
        assert r.area == 6

    def test_contains(self):
        r = point.Rect(point.Point(1, 1), point.Point(3, 3))
        assert r.contains_point(point.Point(2, 2))
        assert not r.contains_circle(point.Point(2, 2), 5)
        assert not r.contains_point(point.Point(4, 4))
        assert not r.contains_circle(point.Point(4, 4), 5)

    def test_intersects_circle(self):
        r = point.Rect(point.Point(1, 1), point.Point(3, 3))
        assert not r.intersects_circle(point.Point(0, 0), 0.5)
        assert not r.intersects_circle(point.Point(0, 0), 1)
        assert r.intersects_circle(point.Point(0, 0), 1.5)
        assert r.intersects_circle(point.Point(0, 0), 2)
