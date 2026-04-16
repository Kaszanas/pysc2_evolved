load("//src/pysc2_evolved:build_defs.bzl", "pytype_strict_library")
load("@pybind11_bazel//:build_defs.bzl", "pybind_extension")

package(default_visibility = ["//visibility:public"])

licenses(["notice"])

pybind_extension(
    name = "converter",
    srcs = ["converter.cc"],
    copts = select({
        "@platforms//os:windows": ["/EHsc"],
        "//conditions:default": ["-fexceptions"],
    }),
    features = ["-use_header_modules"],
    deps = [
        "//src/pysc2_evolved/env/converter/cc:converter",
        "//src/pysc2_evolved/env/converter/proto:converter_cc_proto",
        "@com_google_absl//absl/status:statusor",
        "@com_google_absl//absl/strings",
        "@dm_env_rpc_archive//:dm_env_rpc_cc_proto",
    ],
)

pytype_strict_library(
    name = "__init__",
    srcs = ["__init__.py"],
)
