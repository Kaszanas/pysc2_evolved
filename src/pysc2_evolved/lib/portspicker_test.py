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
"""Tests for portspicker.py."""

import pytest

from pysc2_evolved.lib import portspicker


@pytest.mark.minor
class TestPorts:
    @pytest.mark.parametrize("num_ports", range(1, 10))
    def test_non_contiguous_reservation(self, num_ports):
        reserved = portspicker.pick_unused_ports(num_ports)
        assert len(reserved) == num_ports
        portspicker.return_ports(reserved)

    @pytest.mark.parametrize("num_ports", range(2, 5))
    def test_contiguous_reservation(self, num_ports):
        reserved = portspicker.pick_contiguous_unused_ports(num_ports)
        assert len(reserved) == num_ports
        portspicker.return_ports(reserved)

    def test_invalid_reservation(self):
        with pytest.raises(ValueError):
            portspicker.pick_unused_ports(0)

    def test_invalid_contiguous_reservation(self):
        with pytest.raises(ValueError):
            portspicker.pick_contiguous_unused_ports(0)
