load("//src/pysc2_evolved:build_defs.bzl", "pytype_library")

package(default_visibility = ["//visibility:public"])

licenses(["notice"])

pytype_library(
    name = "run_configs",
    srcs = ["__init__.py"],
    srcs_version = "PY3",
    deps = [
        ":lib",
        ":platforms",
        "//src/pysc2_evolved/lib:sc_process",
        "@absl_py//absl/flags",
    ],
)

pytype_library(
    name = "lib",
    srcs = ["lib.py"],
    srcs_version = "PY3",
    deps = [
        "//src/pysc2_evolved/lib:gfile",
    ],
)

pytype_library(
    name = "platforms",
    srcs = ["platforms.py"],
    deps = [
        ":lib",
        "//src/pysc2_evolved/lib:sc_process",
        "@absl_py//absl/flags",
        "@absl_py//absl/logging",
    ],
)
