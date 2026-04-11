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
"""Tests for stopwatch."""

import os

import mock
import pytest

from pysc2_evolved.lib import stopwatch


def ham_dist(str1, str2):
    """Hamming distance. Count the number of differences between str1 and str2."""
    assert len(str1) == len(str2)
    return sum(c1 != c2 for c1, c2 in zip(str1, str2))


@pytest.mark.minor
class TestStat:
    def test_range(self):
        stat = stopwatch.Stat()
        stat.add(1)
        stat.add(5)
        stat.add(3)
        assert stat.num == 3
        assert stat.sum == 9
        assert stat.min == 1
        assert stat.max == 5
        assert stat.avg == 3

    def test_parse(self):
        stat = stopwatch.Stat()
        stat.add(1)
        stat.add(3)
        out = str(stat)
        assert (
            out
            == "sum: 4.0000, avg: 2.0000, dev: 1.0000, min: 1.0000, max: 3.0000, num: 2"
        )
        # Allow a few small rounding errors
        assert ham_dist(out, str(stopwatch.Stat.parse(out))) < 5


@pytest.mark.minor
class TestStopwatch:
    @mock.patch("time.time")
    def test_stopwatch(self, mock_time):
        mock_time.return_value = 0
        sw = stopwatch.StopWatch()
        with sw("one"):
            mock_time.return_value += 0.002
        with sw("one"):
            mock_time.return_value += 0.004
        with sw("two"):
            with sw("three"):
                mock_time.return_value += 0.006

        @sw.decorate
        def four():
            mock_time.return_value += 0.004

        four()

        @sw.decorate("five")
        def foo():
            mock_time.return_value += 0.005

        foo()

        out = str(sw)

        # The names should be in sorted order.
        names = [line.split(None)[0] for line in out.splitlines()[1:]]
        assert names == ["five", "four", "one", "two", "two.three"]

        one_line = out.splitlines()[3].split(None)
        assert one_line[5] < one_line[6]  # min < max
        assert one_line[7] == "2"  # num
        # Can't test the rest since they'll be flaky.

        # Allow a few small rounding errors for the round trip.
        round_trip = str(stopwatch.StopWatch.parse(out))
        assert ham_dist(out, round_trip) < 15, "%s != %s" % (out, round_trip)

    def test_divide_zero(self):
        sw = stopwatch.StopWatch()
        with sw("zero"):
            pass

        # Just make sure this doesn't have a divide by 0 for when the total is 0.
        assert "zero" in str(sw)

    @mock.patch.dict(os.environ, {"SC2_NO_STOPWATCH": "1"})
    def test_decorator_disabled(self):
        sw = stopwatch.StopWatch()
        assert round == sw.decorate(round)
        assert round == sw.decorate("name")(round)

    @mock.patch.dict(os.environ, {"SC2_NO_STOPWATCH": ""})
    def test_decorator_enabled(self):
        sw = stopwatch.StopWatch()
        assert round != sw.decorate(round)
        assert round != sw.decorate("name")(round)

    def test_speed(self):
        count = 100

        def run():
            for _ in range(count):
                with sw("name"):
                    pass

        sw = stopwatch.StopWatch()
        for _ in range(10):
            sw.enable()
            with sw("enabled"):
                run()

            sw.trace()
            with sw("trace"):
                run()

            sw.enable()  # To catch "disabled".
            with sw("disabled"):
                sw.disable()
                run()

        # No asserts. Succeed but print the timings.
        print(sw)
