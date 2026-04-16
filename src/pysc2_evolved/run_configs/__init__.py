# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Configs for various ways to run starcraft."""

from typing import Dict

from pysc2_evolved.lib import sc_process
from pysc2_evolved.run_configs import lib as lib
from pysc2_evolved.run_configs import platforms as platforms

# REVIEW: REMOVE THIS:
# flags.DEFINE_string(
#     "sc2_run_config", None, "Which run_config to use to spawn the binary."
# )
# FLAGS = flags.FLAGS


def get(
    version: lib.Version | str = None, sc2_run_config: lib.RunConfig | None = None
) -> lib.RunConfig:
    """Get the config chosen by the flags."""
    configs: Dict[str, lib.RunConfig] = {
        c.name(): c for c in lib.RunConfig.all_subclasses() if c.priority()
    }

    if not configs:
        raise sc_process.SC2LaunchError("No valid run_configs found.")

    # REVIEW: This needs to be refactored, NO GLOBAL FLAGS OR GLOBAL STATE LIKE THAT:
    if not sc2_run_config:  # Find the highest priority as default.

        def get_priority(c):
            return c.priority()

        max_priority_run_config = max(configs.values(), key=get_priority)

        run_config = max_priority_run_config(version=version)

        return run_config

    try:
        return configs[sc2_run_config](version=version)
    except KeyError:
        raise sc_process.SC2LaunchError(
            "Invalid run_config. Valid configs are: %s"
            % (", ".join(sorted(configs.keys())))
        )
