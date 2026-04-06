load("@com_google_protobuf//bazel:cc_proto_library.bzl", "cc_proto_library")
load("@com_google_protobuf//bazel:proto_library.bzl", "proto_library")
load("@com_google_protobuf//bazel:py_proto_library.bzl", "py_proto_library")

licenses(["notice"])

proto_library(
    name = "buffs_proto",
    srcs = ["buffs.proto"],
    strip_import_prefix = "/src",
)

cc_proto_library(
    name = "buffs_cc_proto",
    visibility = ["//visibility:public"],
    deps = [":buffs_proto"],
)

py_proto_library(
    name = "buffs_py_pb2",
    visibility = ["//visibility:public"],
    deps = [":buffs_proto"],
)

proto_library(
    name = "units_proto",
    srcs = ["units.proto"],
    strip_import_prefix = "/src",
)

cc_proto_library(
    name = "units_cc_proto",
    visibility = ["//visibility:public"],
    deps = [":units_proto"],
)

py_proto_library(
    name = "units_py_pb2",
    visibility = ["//visibility:public"],
    deps = [":units_proto"],
)

proto_library(
    name = "upgrades_proto",
    srcs = ["upgrades.proto"],
    strip_import_prefix = "/src",
)

cc_proto_library(
    name = "upgrades_cc_proto",
    visibility = ["//visibility:public"],
    deps = [":upgrades_proto"],
)

py_proto_library(
    name = "upgrades_py_pb2",
    visibility = ["//visibility:public"],
    deps = [":upgrades_proto"],
)
