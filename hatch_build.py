"""Hatchling build hook that includes compiled pybind11 extensions in the wheel.

Compiled extensions (.so on Linux, .pyd on Windows) are not tracked by git,
so hatchling's default VCS-based file selection excludes them.  This hook:
  1. Scans the source tree for any .so / .pyd files.
  2. Adds them to force_include so they are copied into the wheel verbatim.
  3. Sets pure_python = False so the wheel is tagged cp<N>-cp<N>-<platform>
     instead of py3-none-any.

Usage in CI:
    1. Build the extension with Bazel.
    2. Copy the output binary into the source tree (make copy_extensions_local).
    3. Run `uv build --wheel` — this hook fires and packages everything.
"""

import glob

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        if self.target_name != "wheel":
            return

        found = []
        for ext in ("so", "pyd"):
            found.extend(glob.glob(f"src/pysc2_evolved/**/*.{ext}", recursive=True))

        if not found:
            return

        build_data["pure_python"] = False
        for src_path in found:
            # Strip the leading "src/" so the wheel path mirrors the import path.
            # e.g. src/pysc2_evolved/env/.../converter.pyd
            #   -> pysc2_evolved/env/.../converter.pyd
            wheel_path = src_path.replace("\\", "/").removeprefix("src/")
            build_data["force_include"][src_path.replace("\\", "/")] = wheel_path
