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
"""Tests for lib.named_array."""

import collections
import enum
import pickle

import numpy as np
import pytest

from pysc2_evolved.lib import named_array


class TestEnum(enum.IntEnum):
    a = 0
    b = 1
    c = 2


class BadEnum(enum.IntEnum):
    a = 1
    b = 2
    c = 3


class TestNamedTuple(collections.namedtuple("TestNamedTuple", ["a", "b", "c"])):
    pass


class BadNamedTuple(collections.namedtuple("BadNamedTuple", ["a", "b"])):
    pass


def assert_array_equal(a, b):
    np.testing.assert_array_equal(a, b)


@pytest.mark.minor
class TestNamedDict:
    def test_named_dict(self):
        a = named_array.NamedDict(a=2, b=(1, 2))
        assert a["a"] == a.a
        assert a["b"] == a.b
        assert a["b"] is a.b
        assert a["a"] != a.b
        a.c = 3
        assert a["c"] == 3


@pytest.mark.minor
class TestNamedArray:
    @pytest.mark.parametrize(
        "names",
        [
            None,
            [None],
            ["a"],
            ["a", "b", "c", "d"],
            [["a", "b", "c", "d"]],
            [[1, "b", 3]],
            [BadEnum],
            [BadNamedTuple],
            [{"a": 0, "b": 1, "c": 2}],
            [{"a", "b", "c"}],
        ],
        ids=[
            "none",
            "none2",
            "short_list",
            "long_list",
            "long_list2",
            "ints",
            "bad_enum",
            "bad_namedtuple",
            "dict",
            "set",
        ],
    )
    def test_bad_names(self, names):
        with pytest.raises(ValueError):
            named_array.NamedNumpyArray([1, 3, 6], names)

    @pytest.mark.parametrize(
        "names",
        [
            ["a", "b", "c"],
            ("a", "b", "c"),
            [["a", "b", "c"]],
            (("a", "b", "c")),
            [("a", "b", "c")],
            TestNamedTuple,
            [TestNamedTuple],
            TestEnum,
            [TestEnum],
        ],
        ids=[
            "list",
            "tuple",
            "list2",
            "tuple2",
            "list_tuple",
            "named_tuple",
            "named_tuple2",
            "int_enum",
            "int_enum2",
        ],
    )
    def test_single_dimension(self, names):
        a = named_array.NamedNumpyArray([1, 3, 6], names)
        assert a[0] == 1
        assert a[1] == 3
        assert a[2] == 6
        assert a[-1] == 6
        assert a.a == 1
        assert a.b == 3
        assert a.c == 6
        with pytest.raises(AttributeError):
            a.d  # pylint: disable=pointless-statement
        assert a["a"] == 1
        assert a["b"] == 3
        assert a["c"] == 6
        with pytest.raises(KeyError):
            a["d"]  # pylint: disable=pointless-statement

        # New axis = None
        assert_array_equal(a, [1, 3, 6])
        assert_array_equal(a[np.newaxis], [[1, 3, 6]])
        assert_array_equal(a[None], [[1, 3, 6]])
        assert_array_equal(a[None, :], [[1, 3, 6]])
        assert_array_equal(a[:, None], [[1], [3], [6]])
        assert_array_equal(a[None, :, None], [[[1], [3], [6]]])
        assert_array_equal(a[None, a % 3 == 0, None], [[[3], [6]]])
        assert_array_equal(a[None][None], [[[1, 3, 6]]])
        assert_array_equal(a[None][0], [1, 3, 6])
        assert a[None, 0] == 1
        assert a[None, "a"] == 1
        assert a[None][0].a == 1
        assert a[None][0, "b"] == 3

        # range slicing
        assert_array_equal(a[0:2], [1, 3])
        assert_array_equal(a[1:3], [3, 6])
        assert_array_equal(a[0:2:], [1, 3])
        assert_array_equal(a[0:2:1], [1, 3])
        assert_array_equal(a[::2], [1, 6])
        assert_array_equal(a[::-1], [6, 3, 1])
        assert a[1:3][0] == 3
        assert a[1:3].b == 3
        assert a[1:3].c == 6

        # list slicing
        assert_array_equal(a[[0, 0]], [1, 1])
        assert_array_equal(a[[0, 1]], [1, 3])
        assert_array_equal(a[[1, 0]], [3, 1])
        assert_array_equal(a[[1, 2]], [3, 6])
        assert_array_equal(a[np.array([0, 2])], [1, 6])
        assert a[[1, 2]].b == 3
        assert a[[2, 0]].c == 6
        with pytest.raises(TypeError):
            # Duplicates lead to unnamed dimensions.
            a[[0, 0]].a  # pylint: disable=pointless-statement

        a[1] = 4
        assert a[1] == 4
        assert a.b == 4
        assert a["b"] == 4

        a[1:2] = 2
        assert a[1] == 2
        assert a.b == 2
        assert a["b"] == 2

        a[[1]] = 3
        assert a[1] == 3
        assert a.b == 3
        assert a["b"] == 3

        a.b = 5
        assert a[1] == 5
        assert a.b == 5
        assert a["b"] == 5

    def test_empty_array(self):
        named_array.NamedNumpyArray([], [None, ["a", "b"]])
        with pytest.raises(ValueError):
            # Must be the right length.
            named_array.NamedNumpyArray([], [["a", "b"]])
        with pytest.raises(ValueError):
            # Returning an empty slice is not supported, and it's not clear how or
            # even if it should be supported.
            named_array.NamedNumpyArray([], [["a", "b"], None])
        with pytest.raises(ValueError):
            # Scalar arrays are unsupported.
            named_array.NamedNumpyArray(1, [])

    def test_named_array_multi_first(self):
        a = named_array.NamedNumpyArray([[1, 3], [6, 8]], [["a", "b"], None])
        assert_array_equal(a.a, [1, 3])
        assert_array_equal(a[1], [6, 8])
        assert_array_equal(a["b"], [6, 8])
        assert_array_equal(a[::-1], [[6, 8], [1, 3]])
        assert_array_equal(a[::-1][::-1], [[1, 3], [6, 8]])
        assert_array_equal(a[::-1, ::-1], [[8, 6], [3, 1]])
        assert_array_equal(a[::-1][0], [6, 8])
        assert_array_equal(a[::-1, 0], [6, 1])
        assert_array_equal(a[::-1, 1], [8, 3])
        assert_array_equal(a[::-1].a, [1, 3])
        assert_array_equal(a[::-1].a[0], 1)
        assert_array_equal(a[::-1].b, [6, 8])
        assert_array_equal(a[[0, 0]], [[1, 3], [1, 3]])
        with pytest.raises(TypeError):
            a[[0, 0]].a  # pylint: disable=pointless-statement
        assert a[0, 1] == 3
        assert a[(0, 1)] == 3
        assert a["a", 0] == 1
        assert a["b", 0] == 6
        assert a["b", 1] == 8
        assert a.a[0] == 1
        assert_array_equal(a[a > 2], [3, 6, 8])
        assert_array_equal(a[a % 3 == 0], [3, 6])
        with pytest.raises(TypeError):
            a[0].a  # pylint: disable=pointless-statement

        # New axis = None
        assert_array_equal(a, [[1, 3], [6, 8]])
        assert_array_equal(a[np.newaxis], [[[1, 3], [6, 8]]])
        assert_array_equal(a[None], [[[1, 3], [6, 8]]])
        assert_array_equal(a[None, :], [[[1, 3], [6, 8]]])
        assert_array_equal(a[None, "a"], [[1, 3]])
        assert_array_equal(a[:, None], [[[1, 3]], [[6, 8]]])
        assert_array_equal(a[None, :, None], [[[[1, 3]], [[6, 8]]]])
        assert_array_equal(a[None, 0, None], [[[1, 3]]])
        assert_array_equal(a[None, "a", None], [[[1, 3]]])
        assert_array_equal(a[None][None], [[[[1, 3], [6, 8]]]])
        assert_array_equal(a[None][0], [[1, 3], [6, 8]])
        assert_array_equal(a[None][0].a, [1, 3])
        assert a[None][0].a[0] == 1
        assert a[None][0, "b", 1] == 8

    def test_named_array_multi_second(self):
        a = named_array.NamedNumpyArray([[1, 3], [6, 8]], [None, ["a", "b"]])
        assert_array_equal(a[0], [1, 3])
        assert a[0, 1] == 3
        assert a[0, "a"] == 1
        assert a[0, "b"] == 3
        assert a[1, "b"] == 8
        assert a[0].a == 1
        assert_array_equal(a[a > 2], [3, 6, 8])
        assert_array_equal(a[a % 3 == 0], [3, 6])
        with pytest.raises(TypeError):
            a.a  # pylint: disable=pointless-statement
        assert_array_equal(a[None, :, "a"], [[1, 6]])

    def test_masking(self):
        a = named_array.NamedNumpyArray(
            [[1, 2, 3, 4], [5, 6, 7, 8]], [None, list("abcd")]
        )
        assert_array_equal(a[a > 2], [3, 4, 5, 6, 7, 8])
        assert_array_equal(a[a < 4], [1, 2, 3])
        assert_array_equal(a[a % 2 == 0], [2, 4, 6, 8])
        assert_array_equal(a[a % 3 == 0], [3, 6])

    def test_slicing(self):
        a = named_array.NamedNumpyArray([1, 2, 3, 4, 5], list("abcde"))
        assert_array_equal(a[:], [1, 2, 3, 4, 5])
        assert_array_equal(a[::], [1, 2, 3, 4, 5])
        assert_array_equal(a[::2], [1, 3, 5])
        assert_array_equal(a[::-1], [5, 4, 3, 2, 1])
        assert a[:].a == 1
        assert a[::].b == 2
        assert a[::2].c == 3
        with pytest.raises(AttributeError):
            a[::2].d  # pylint: disable=pointless-statement
        assert a[::-1].e == 5
        assert_array_equal(a[a % 2 == 0], [2, 4])
        assert a[a % 2 == 0].b == 2

        a = named_array.NamedNumpyArray(
            [[1, 2, 3, 4], [5, 6, 7, 8]], [None, list("abcd")]
        )
        assert_array_equal(a[:], [[1, 2, 3, 4], [5, 6, 7, 8]])
        assert_array_equal(a[::], [[1, 2, 3, 4], [5, 6, 7, 8]])
        assert_array_equal(a[:, :], [[1, 2, 3, 4], [5, 6, 7, 8]])
        assert_array_equal(a[:, ...], [[1, 2, 3, 4], [5, 6, 7, 8]])
        assert_array_equal(a[..., ::], [[1, 2, 3, 4], [5, 6, 7, 8]])
        assert_array_equal(a[:, ::2], [[1, 3], [5, 7]])

        assert_array_equal(a[::-1], [[5, 6, 7, 8], [1, 2, 3, 4]])
        assert_array_equal(a[..., ::-1], [[4, 3, 2, 1], [8, 7, 6, 5]])
        assert_array_equal(a[:, ::-1], [[4, 3, 2, 1], [8, 7, 6, 5]])
        assert_array_equal(a[:, ::-2], [[4, 2], [8, 6]])
        assert_array_equal(a[:, -2::-2], [[3, 1], [7, 5]])
        assert_array_equal(a[::-1, -2::-2], [[7, 5], [3, 1]])
        assert_array_equal(a[..., 0, 0], 1)  # weird scalar arrays...

        a = named_array.NamedNumpyArray(
            [
                [[[0, 1], [2, 3]], [[4, 5], [6, 7]]],
                [[[8, 9], [10, 11]], [[12, 13], [14, 15]]],
            ],
            [["a", "b"], ["c", "d"], ["e", "f"], ["g", "h"]],
        )
        assert a.a.c.e.g == 0
        assert a.b.c.f.g == 10
        assert a.b.d.f.h == 15
        assert_array_equal(a[0, ..., 0], [[0, 2], [4, 6]])
        assert_array_equal(a[0, ..., 1], [[1, 3], [5, 7]])
        assert_array_equal(a[0, 0, ..., 1], [1, 3])
        assert_array_equal(a[0, ..., 1, 1], [3, 7])
        assert_array_equal(a[..., 1, 1], [[3, 7], [11, 15]])
        assert_array_equal(a[1, 0, ...], [[8, 9], [10, 11]])

        assert_array_equal(a["a", ..., "g"], [[0, 2], [4, 6]])
        assert_array_equal(a["a", ...], [[[0, 1], [2, 3]], [[4, 5], [6, 7]]])
        assert_array_equal(a[..., "g"], [[[0, 2], [4, 6]], [[8, 10], [12, 14]]])
        assert_array_equal(a["a", "c"], [[0, 1], [2, 3]])
        assert_array_equal(a["a", ...].c, [[0, 1], [2, 3]])
        assert_array_equal(a["a", ..., "g"].c, [0, 2])

        with pytest.raises(TypeError):
            a[np.array([[0, 1], [0, 1]])]  # pylint: disable=pointless-statement, expression-not-assigned

        with pytest.raises(IndexError):
            a[..., 0, ...]  # pylint: disable=pointless-statement

    def test_string(self):
        a = named_array.NamedNumpyArray([1, 3, 6], ["a", "b", "c"], dtype=np.int32)
        assert str(a) == "[1 3 6]"
        assert repr(a) == "NamedNumpyArray([1, 3, 6], ['a', 'b', 'c'], dtype=int32)"

        a = named_array.NamedNumpyArray([[1, 3], [6, 8]], [None, ["a", "b"]])
        assert str(a) == "[[1 3]\n [6 8]]"
        assert (
            repr(a)
            == "NamedNumpyArray([[1, 3],\n                 [6, 8]], [None, ['a', 'b']])"
        )

        a = named_array.NamedNumpyArray([[1, 3], [6, 8]], [["a", "b"], None])
        assert str(a) == "[[1 3]\n [6 8]]"
        assert (
            repr(a)
            == "NamedNumpyArray([[1, 3],\n                 [6, 8]], [['a', 'b'], None])"
        )

        a = named_array.NamedNumpyArray(
            [0, 0, 0, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [str(i) for i in range(13)],
            dtype=np.int32,
        )
        numpy_repr = np.array_repr(a)
        if "\n" in numpy_repr:  # ie numpy > 1.14
            assert repr(a) == (
                "NamedNumpyArray([ 0,  0,  0, 50,  0,  0,  0,  0,  0,  0,  0,  0,  0],\n"
                "                ['0', '1', '2', '3', '4', '...', '8', '9', '10', '11', '12'],\n"
                "                dtype=int32)"
            )
        else:
            assert repr(a) == (
                "NamedNumpyArray("
                "[ 0,  0,  0, 50,  0,  0,  0,  0,  0,  0,  0,  0,  0], "
                "['0', '1', '2', '3', '4', '...', '8', '9', '10', '11', '12'], "
                "dtype=int32)"
            )

        a = named_array.NamedNumpyArray(
            [list(range(50))] * 50, [None, ["a%s" % i for i in range(50)]]
        )
        assert "49" in str(a)
        assert "49" in repr(a)
        assert "a4" in repr(a)
        assert "a49" in repr(a)

        a = named_array.NamedNumpyArray(
            [list(range(50))] * 50, [["a%s" % i for i in range(50)], None]
        )
        assert "49" in str(a)
        assert "49" in repr(a)
        assert "a4" in repr(a)
        assert "a49" in repr(a)

    def test_pickle(self):
        arr = named_array.NamedNumpyArray([1, 3, 6], ["a", "b", "c"])
        pickled = pickle.loads(pickle.dumps(arr))
        assert np.all(arr == pickled)
        assert repr(pickled) == "NamedNumpyArray([1, 3, 6], ['a', 'b', 'c'])"
