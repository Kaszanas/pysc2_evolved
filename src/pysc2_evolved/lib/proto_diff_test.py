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
"""Tests for proto_diff.py."""

import pytest
from s2clientprotocol import sc2api_pb2 as sc_pb
from s2clientprotocol import score_pb2

from pysc2_evolved.lib import proto_diff


@pytest.mark.minor
class TestProtoPath:
    def test_creation_from_tuple(self):
        assert (
            str(proto_diff.ProtoPath(("observation", "actions")))
            == "observation.actions"
        )

    def test_creation_from_list(self):
        assert (
            str(proto_diff.ProtoPath(["observation", "actions"]))
            == "observation.actions"
        )

    def test_creation_from_generator(self):
        assert str(proto_diff.ProtoPath(a for a in "abc")) == "a.b.c"

    def test_string_repr(self):
        assert (
            str(proto_diff.ProtoPath(("observation", "actions", 1, "target")))
            == "observation.actions[1].target"
        )

    def test_ordering(self):
        assert proto_diff.ProtoPath(
            ("observation", "actions", 1, "game_loop")
        ) < proto_diff.ProtoPath(("observation", "actions", 1, "target"))

        assert proto_diff.ProtoPath(
            ("observation", "actions", 1)
        ) < proto_diff.ProtoPath(("observation", "actions", 1, "target"))

        assert proto_diff.ProtoPath(
            ("observation", "actions", 1)
        ) > proto_diff.ProtoPath(("observation",))

    def test_equals(self):
        a = proto_diff.ProtoPath(("observation", "actions", 1))
        b = proto_diff.ProtoPath(("observation", "actions", 1))
        assert a == b
        assert hash(a) == hash(b)

    def test_not_equal(self):
        a = proto_diff.ProtoPath(("observation", "actions", 1))
        b = proto_diff.ProtoPath(("observation", "actions", 2))
        assert a != b
        assert hash(a) != hash(b)

    def test_indexing(self):
        path = proto_diff.ProtoPath(("observation", "actions", 1))
        assert path[0] == "observation"
        assert path[1] == "actions"
        assert path[-2] == "actions"
        assert path[-1] == 1

    def test_get_field(self):
        proto = sc_pb.ResponseObservation(
            observation=sc_pb.Observation(game_loop=1, alerts=[sc_pb.AlertError])
        )

        game_loop = proto_diff.ProtoPath(("observation", "game_loop"))
        alert = proto_diff.ProtoPath(("observation", "alerts", 0))
        assert game_loop.get_field(proto) == 1
        assert alert.get_field(proto) == sc_pb.AlertError
        assert proto_diff.ProtoPath(game_loop.path[:-1]).get_field(
            proto
        ) == sc_pb.Observation(game_loop=1, alerts=[sc_pb.AlertError])

    def test_with_anonymous_array_indices(self):
        a = proto_diff.ProtoPath(("observation", "actions"))
        b = proto_diff.ProtoPath(("observation", "actions", 1))
        c = proto_diff.ProtoPath(("observation", "actions", 2))
        assert str(a) == "observation.actions"
        assert str(b.with_anonymous_array_indices()) == "observation.actions[*]"
        assert b.with_anonymous_array_indices() == c.with_anonymous_array_indices()


def _alert_formatter(path, proto_a, proto_b):
    field_a = path.get_field(proto_a)
    if path[-2] == "alerts":
        field_b = path.get_field(proto_b)
        return "{} -> {}".format(sc_pb.Alert.Name(field_a), sc_pb.Alert.Name(field_b))


@pytest.mark.minor
class TestProtoDiff:
    def test_no_diffs(self):
        a = sc_pb.ResponseObservation()
        b = sc_pb.ResponseObservation()
        diff = proto_diff.compute_diff(a, b)
        assert diff is None

    def test_added_field(self):
        a = sc_pb.ResponseObservation()
        b = sc_pb.ResponseObservation(observation=sc_pb.Observation(game_loop=1))
        diff = proto_diff.compute_diff(a, b)
        assert diff is not None
        assert len(diff.added) == 1, diff
        assert str(diff.added[0]) == "observation"
        assert diff.added == diff.all_diffs()
        assert diff.report() == "Added observation."

    def test_added_fields(self):
        a = sc_pb.ResponseObservation(
            observation=sc_pb.Observation(alerts=[sc_pb.AlertError])
        )
        b = sc_pb.ResponseObservation(
            observation=sc_pb.Observation(
                alerts=[sc_pb.AlertError, sc_pb.MergeComplete]
            ),
            player_result=[sc_pb.PlayerResult()],
        )
        diff = proto_diff.compute_diff(a, b)
        assert diff is not None
        assert len(diff.added) == 2, diff
        assert str(diff.added[0]) == "observation.alerts[1]"
        assert str(diff.added[1]) == "player_result"
        assert diff.added == diff.all_diffs()
        assert diff.report() == "Added observation.alerts[1].\nAdded player_result."

    def test_removed_field(self):
        a = sc_pb.ResponseObservation(observation=sc_pb.Observation(game_loop=1))
        b = sc_pb.ResponseObservation(observation=sc_pb.Observation())
        diff = proto_diff.compute_diff(a, b)
        assert diff is not None
        assert len(diff.removed) == 1, diff
        assert str(diff.removed[0]) == "observation.game_loop"
        assert diff.removed == diff.all_diffs()
        assert diff.report() == "Removed observation.game_loop."

    def test_removed_fields(self):
        a = sc_pb.ResponseObservation(
            observation=sc_pb.Observation(
                game_loop=1,
                score=score_pb2.Score(),
                alerts=[sc_pb.AlertError, sc_pb.MergeComplete],
            )
        )
        b = sc_pb.ResponseObservation(
            observation=sc_pb.Observation(alerts=[sc_pb.AlertError])
        )
        diff = proto_diff.compute_diff(a, b)
        assert diff is not None
        assert len(diff.removed) == 3, diff
        assert str(diff.removed[0]) == "observation.alerts[1]"
        assert str(diff.removed[1]) == "observation.game_loop"
        assert str(diff.removed[2]) == "observation.score"
        assert diff.removed == diff.all_diffs()
        assert diff.report() == (
            "Removed observation.alerts[1].\n"
            "Removed observation.game_loop.\n"
            "Removed observation.score."
        )

    def test_changed_field(self):
        a = sc_pb.ResponseObservation(observation=sc_pb.Observation(game_loop=1))
        b = sc_pb.ResponseObservation(observation=sc_pb.Observation(game_loop=2))
        diff = proto_diff.compute_diff(a, b)
        assert diff is not None
        assert len(diff.changed) == 1, diff
        assert str(diff.changed[0]) == "observation.game_loop"
        assert diff.changed == diff.all_diffs()
        assert diff.report() == "Changed observation.game_loop: 1 -> 2."

    def test_changed_fields(self):
        a = sc_pb.ResponseObservation(
            observation=sc_pb.Observation(
                game_loop=1, alerts=[sc_pb.AlertError, sc_pb.LarvaHatched]
            )
        )
        b = sc_pb.ResponseObservation(
            observation=sc_pb.Observation(
                game_loop=2, alerts=[sc_pb.AlertError, sc_pb.MergeComplete]
            )
        )
        diff = proto_diff.compute_diff(a, b)
        assert diff is not None
        assert len(diff.changed) == 2, diff
        assert str(diff.changed[0]) == "observation.alerts[1]"
        assert str(diff.changed[1]) == "observation.game_loop"
        assert diff.changed == diff.all_diffs()
        assert diff.report() == (
            "Changed observation.alerts[1]: 7 -> 8.\n"
            "Changed observation.game_loop: 1 -> 2."
        )

        assert diff.report([_alert_formatter]) == (
            "Changed observation.alerts[1]: LarvaHatched -> MergeComplete.\n"
            "Changed observation.game_loop: 1 -> 2."
        )

    def test_truncation(self):
        a = sc_pb.ResponseObservation(
            observation=sc_pb.Observation(
                game_loop=1, alerts=[sc_pb.AlertError, sc_pb.LarvaHatched]
            )
        )
        b = sc_pb.ResponseObservation(
            observation=sc_pb.Observation(
                game_loop=2, alerts=[sc_pb.AlertError, sc_pb.MergeComplete]
            )
        )
        diff = proto_diff.compute_diff(a, b)
        assert diff is not None
        assert diff.report([_alert_formatter], truncate_to=9) == (
            "Changed observation.alerts[1]: LarvaH....\n"
            "Changed observation.game_loop: 1 -> 2."
        )
        assert diff.report([_alert_formatter], truncate_to=-1) == (
            "Changed observation.alerts[1]: ....\n"
            "Changed observation.game_loop: ... -> ...."
        )
