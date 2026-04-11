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
"""Test for sc2_env."""

import pytest

from pysc2_evolved.env import sc2_env


@pytest.mark.minor
class TestNameCroppingAndDeduplication:
    @pytest.mark.parametrize(
        "names,expected_output",
        [
            ([], []),
            (["agent_1"], ["agent_1"]),
            (
                ["very_long_agent_name_experimental_1"],
                ["very_long_agent_name_experimenta"],
            ),
            (["agent_1", "agent_2"], ["agent_1", "agent_2"]),
            (
                [
                    "a_very_long_agent_name_experimental",
                    "b_very_long_agent_name_experimental",
                ],
                ["a_very_long_agent_name_experimen", "b_very_long_agent_name_experimen"],
            ),
            (["agent_1", "agent_1"], ["(1) agent_1", "(2) agent_1"]),
            (
                [
                    "very_long_agent_name_experimental_c123",
                    "very_long_agent_name_experimental_c456",
                ],
                ["(1) very_long_agent_name_experim", "(2) very_long_agent_name_experim"],
            ),
        ],
        ids=[
            "empty",
            "single_no_crop",
            "single_cropped",
            "no_dupes_no_crop",
            "no_dupes_cropped",
            "dupes_no_crop",
            "dupes_cropped",
        ],
    )
    def test(self, names, expected_output):
        assert sc2_env.crop_and_deduplicate_names(names) == expected_output
