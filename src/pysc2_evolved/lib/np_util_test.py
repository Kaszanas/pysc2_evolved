#!/usr/bin/python
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Tests for np_util.py."""

import numpy as np
import pytest

from pysc2_evolved.lib import np_util


@pytest.mark.minor
class TestNpUtil:
    @pytest.mark.parametrize(
        "lhs,rhs,expected",
        [
            ([1, 2, 3, 4], [1, 2, 3, 4], ""),
            ([[1, 2], [3, 4]], [[1, 2], [3, 4]], ""),
            (
                [1, 2, 3, 4],
                [1, 3, 2, 4],
                "2 element(s) changed - [1]: 2 -> 3; [2]: 3 -> 2",
            ),
            (
                [[1, 2], [3, 4]],
                [[1, 3], [2, 4]],
                "2 element(s) changed - [0][1]: 2 -> 3; [1][0]: 3 -> 2",
            ),
        ],
        ids=["no_diff_1d", "no_diff_2d", "diff_1d", "diff_2d"],
    )
    def test_summarize_array_diffs(self, lhs, rhs, expected):
        a = np.array(lhs)
        b = np.array(rhs)
        result = np_util.summarize_array_diffs(a, b)
        assert result == expected
