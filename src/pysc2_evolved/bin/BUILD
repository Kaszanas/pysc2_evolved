load("@my_deps//:requirements.bzl", "requirement")
load("//pysc2_evolved:build_defs.bzl", "pytype_binary", "pytype_strict_binary")

package(default_visibility = ["//visibility:public"])

licenses(["notice"])

pytype_binary(
    name = "replay_actions",
    srcs = ["replay_actions.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pysc2_evolved/lib:features",
        "//pysc2_evolved/lib:gfile",
        "//pysc2_evolved/lib:point",
        "//pysc2_evolved/lib:protocol",
        "//pysc2_evolved/lib:remote_controller",
        "//pysc2_evolved/lib:replay",
        "//pysc2_evolved/lib:static_data",
        "//pysc2_evolved/maps",  # build_cleaner: keep
        "//pysc2_evolved/run_configs",
        "@absl_py//absl:app",
        "@absl_py//absl/flags",
        "@s2client_proto//s2clientprotocol:sc2api_py_pb2",
    ],
)

pytype_binary(
    name = "gen_actions",
    srcs = ["gen_actions.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pysc2_evolved/lib:static_data",
        "//pysc2_evolved/maps",
        "//pysc2_evolved/run_configs",
        "@absl_py//absl:app",
        "@absl_py//absl/flags",
        "@s2client_proto//s2clientprotocol:sc2api_py_pb2",
    ],
)

pytype_binary(
    name = "gen_data",
    srcs = ["gen_data.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pysc2_evolved/lib:static_data",
        "//pysc2_evolved/maps",
        "//pysc2_evolved/run_configs",
        "@absl_py//absl:app",
        "@s2client_proto//s2clientprotocol:sc2api_py_pb2",
    ],
)

pytype_binary(
    name = "check_apm",
    srcs = ["check_apm.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pysc2_evolved/lib:actions",
        "//pysc2_evolved/lib:features",
        "//pysc2_evolved/lib:point",
        "//pysc2_evolved/lib:units",
        "//pysc2_evolved/maps",
        "//pysc2_evolved/run_configs",
        "@absl_py//absl:app",
        "@s2client_proto//s2clientprotocol:sc2api_py_pb2",
    ],
)

pytype_binary(
    name = "benchmark_observe",
    srcs = ["benchmark_observe.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pysc2_evolved/lib:replay",
        "//pysc2_evolved/lib:stopwatch",
        "//pysc2_evolved/maps",
        "//pysc2_evolved/run_configs",
        "@absl_py//absl:app",
        "@absl_py//absl/flags",
        "@s2client_proto//s2clientprotocol:sc2api_py_pb2",
    ],
)

pytype_binary(
    name = "benchmark_replay",
    srcs = ["benchmark_replay.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pysc2_evolved/lib:actions",
        "//pysc2_evolved/lib:features",
        "//pysc2_evolved/lib:point_flag",
        "//pysc2_evolved/lib:replay",
        "//pysc2_evolved/lib:stopwatch",
        "//pysc2_evolved/run_configs",
        "@absl_py//absl:app",
        "@absl_py//absl/flags",
        "@s2client_proto//s2clientprotocol:sc2api_py_pb2",
    ],
)

pytype_binary(
    name = "mem_leak_check",
    srcs = ["mem_leak_check.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "@absl_py//absl:app",
        "@absl_py//absl/flags",
        requirement("psutil"),  # build_cleaner: keep
        "//pysc2_evolved/lib:protocol",
        "//pysc2_evolved/maps",
        "//pysc2_evolved/run_configs",
        "@s2client_proto//s2clientprotocol:sc2api_py_pb2",
    ],
)

pytype_binary(
    name = "gen_versions",
    srcs = ["gen_versions.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "@absl_py//absl:app",
        requirement("requests"),
    ],
)

pytype_binary(
    name = "map_list",
    srcs = ["map_list.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pysc2_evolved/maps",
        "@absl_py//absl:app",
    ],
)

pytype_binary(
    name = "play",
    srcs = ["play.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pysc2_evolved/env:sc2_env",
        "//pysc2_evolved/lib:point_flag",
        "//pysc2_evolved/lib:renderer_human",
        "//pysc2_evolved/lib:replay",
        "//pysc2_evolved/lib:stopwatch",
        "//pysc2_evolved/maps",
        "//pysc2_evolved/run_configs",
        "@absl_py//absl:app",
        "@absl_py//absl/flags",
        "@s2client_proto//s2clientprotocol:sc2api_py_pb2",
    ],
)

pytype_binary(
    name = "play_vs_agent",
    srcs = ["play_vs_agent.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "@absl_py//absl:app",
        "@absl_py//absl/flags",
        "@absl_py//absl/logging",
        requirement("portpicker"),
        "//pysc2_evolved/agents",  # build_cleaner: keep
        "//pysc2_evolved/env:lan_sc2_env",
        "//pysc2_evolved/env:run_loop",
        "//pysc2_evolved/env:sc2_env",
        "//pysc2_evolved/lib:point_flag",
        "//pysc2_evolved/lib:renderer_human",
        "//pysc2_evolved/maps",
        "//pysc2_evolved/run_configs",
        "@s2client_proto//s2clientprotocol:sc2api_py_pb2",
    ],
)

pytype_binary(
    name = "agent_remote",
    srcs = ["agent_remote.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pysc2_evolved/agents",  # build_cleaner: keep
        "//pysc2_evolved/env:remote_sc2_env",
        "//pysc2_evolved/env:run_loop",
        "//pysc2_evolved/env:sc2_env",
        "//pysc2_evolved/lib:point_flag",
        "//pysc2_evolved/lib:portspicker",
        "//pysc2_evolved/lib:renderer_human",
        "//pysc2_evolved/maps",
        "//pysc2_evolved/run_configs",
        "@absl_py//absl:app",
        "@absl_py//absl/flags",
        "@absl_py//absl/logging",
        "@s2client_proto//s2clientprotocol:sc2api_py_pb2",
    ],
)

pytype_binary(
    name = "replay_info",
    srcs = ["replay_info.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pysc2_evolved/lib:gfile",
        "//pysc2_evolved/lib:remote_controller",
        "//pysc2_evolved/lib:replay",
        "//pysc2_evolved/run_configs",
        "@absl_py//absl:app",
        "@absl_py//absl/flags",
        "@s2client_proto//s2clientprotocol:common_py_pb2",
        "@s2client_proto//s2clientprotocol:sc2api_py_pb2",
    ],
)

pytype_binary(
    name = "agent",
    srcs = ["agent.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pysc2_evolved/agents",  # build_cleaner: keep
        "//pysc2_evolved/env:available_actions_printer",
        "//pysc2_evolved/env:run_loop",
        "//pysc2_evolved/env:sc2_env",
        "//pysc2_evolved/lib:point_flag",
        "//pysc2_evolved/lib:stopwatch",
        "//pysc2_evolved/maps",
        "@absl_py//absl:app",
        "@absl_py//absl/flags",
    ],
)

pytype_binary(
    name = "valid_actions",
    srcs = ["valid_actions.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pysc2_evolved/lib:actions",
        "//pysc2_evolved/lib:features",
        "//pysc2_evolved/lib:point_flag",
        "@absl_py//absl:app",
        "@absl_py//absl/flags",
    ],
)

pytype_binary(
    name = "compare_binaries",
    srcs = ["compare_binaries.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pysc2_evolved/lib:image_differencer",
        "//pysc2_evolved/lib:proto_diff",
        "//pysc2_evolved/lib:remote_controller",
        "//pysc2_evolved/lib:replay",
        "//pysc2_evolved/lib:stopwatch",
        "//pysc2_evolved/run_configs",
        "@absl_py//absl:app",
        "@absl_py//absl/flags",
        "@s2client_proto//s2clientprotocol:sc2api_py_pb2",
    ],
)

pytype_strict_binary(
    name = "battle_net_maps",
    srcs = ["battle_net_maps.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pysc2_evolved/run_configs",
        "@absl_py//absl:app",
    ],
)

pytype_strict_binary(
    name = "reencode_replays",
    srcs = ["reencode_replays.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "//pysc2_evolved/lib:replay",
        "//pysc2_evolved/run_configs",
        "@absl_py//absl:app",
        "@absl_py//absl/flags",
        "@s2client_proto//s2clientprotocol:sc2api_py_pb2",
    ],
)

pytype_strict_binary(
    name = "update_battle_net_cache",
    srcs = ["update_battle_net_cache.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        "@absl_py//absl:app",
        "@absl_py//absl/flags",
        requirement("mpyq"),
        "//pysc2_evolved/run_configs",
        "@s2protocol_archive//:versions",
    ],
)

pytype_strict_binary(
    name = "replay_version",
    srcs = ["replay_version.py"],
    deps = [
        "//pysc2_evolved/lib:replay",
        "//pysc2_evolved/run_configs",
        "@absl_py//absl:app",
    ],
)
