"""Hatchling build hook that marks the wheel as non-pure-Python.

When a pre-compiled pybind11 extension (.so on Linux, .pyd on Windows) is
present in the source tree the wheel must carry a CPython/platform tag
(e.g. cp311-cp311-linux_x86_64) rather than the generic py3-none-any tag.
Setting pure_python = False causes hatchling to derive the correct tag from
the current interpreter and platform automatically.

Usage in CI:
    1. Build the extension with Bazel.
    2. Copy the output binary into the source tree.
    3. Run `uv build --wheel` — this hook fires and tags the wheel correctly.
"""

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        if self.target_name == "wheel":
            build_data["pure_python"] = False
