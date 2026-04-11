# Copyright 2021 DeepMind Technologies Ltd. All rights reserved.
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
"""This replaces google's resources used for locating data deps."""

import importlib.resources
import os


def GetResourceFilename(path):
    """Locate a data resource file by its package-relative path.

    Accepts a forward-slash-separated path whose first component is the
    top-level package name, e.g.::

        "pysc2_evolved/lib/replay/test_data/replay_01.SC2Replay"

    Resolution order:
    1. ``importlib.resources`` — works when the package is installed (wheel or
       editable install).  Walks from the deepest possible package name toward
       the root until one resolves, then navigates the remaining components as
       subdirectories / files.
    2. ``src/<path>`` — fallback for running pytest directly from the project
       root against the source tree without an editable install.
    3. The path unchanged — last resort, preserves the original behaviour.
    """
    parts = path.replace("\\", "/").split("/")

    # Walk from the deepest candidate package name toward the shallowest.
    for split_at in range(len(parts), 0, -1):
        package_name = ".".join(parts[:split_at])
        subpath = parts[split_at:]
        try:
            ref = importlib.resources.files(package_name)
            for subpart in subpath:
                ref = ref.joinpath(subpart)
            resolved = str(ref)
            if os.path.exists(resolved):
                return resolved
        except (ModuleNotFoundError, ValueError, TypeError, AttributeError):
            continue

    # Fallback: src/ prefix for source-tree runs from the project root.
    src_path = os.path.join("src", path)
    if os.path.exists(src_path):
        return src_path

    return path
