load("//src/pysc2_evolved:build_defs.bzl", "pytype_strict_library")
load("@pybind11_bazel//:build_defs.bzl", "pybind_extension")

package(default_visibility = ["//visibility:public"])

licenses(["notice"])

pybind_extension(
    name = "uint8_lookup",
    srcs = ["uint8_lookup.cc"],
    deps = ["//src/pysc2_evolved/env/converter/cc/game_data:uint8_lookup"],
)

py_test(
    name = "uint8_lookup_test",
    srcs = ["uint8_lookup_test.py"],
    data = select({
        "@platforms//os:windows": [":uint8_lookup.pyd"],
        "//conditions:default": [":uint8_lookup.so"],
    }),
    legacy_create_init = False,
    deps = [
        "//src/pysc2_evolved/env/converter/cc/game_data/proto:buffs_py_pb2",
        "//src/pysc2_evolved/env/converter/cc/game_data/proto:units_py_pb2",
        "//src/pysc2_evolved/env/converter/cc/game_data/proto:upgrades_py_pb2",
        "@absl_py//absl/testing:absltest",
    ],
)

pytype_strict_library(
    name = "__init__",
    srcs = ["__init__.py"],
)
