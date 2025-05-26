#!/usr/bin/python
# Copyright 2022 DeepMind Technologies Ltd. All Rights Reserved.
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
"""Generate version information from replays."""

import logging
from pathlib import Path
from typing import Set

import click

from pysc2_evolved import run_configs
from pysc2_evolved.lib.get_replay_version import get_replay_version
from pysc2_evolved.run_configs.lib import RunConfig, Version


def read_replay_version(
    replay_path: str,
    run_config: RunConfig,
) -> Version | None:
    """Query a replay for information."""
    if replay_path.lower().endswith("sc2replay"):
        data = run_config.replay_data(replay_path)
        try:
            version = get_replay_version(data)
        except (ValueError, KeyError):
            # Either corrupt or just old.
            return None
        except Exception as e:  # pylint: disable=broad-except
            print("Invalid replay:", replay_path, e)
        else:
            return version


def replay_version_from_replay(replay_directory: Path) -> Set[Version]:
    run_config = run_configs.get()

    # Use a set over the full version struct to catch cases where Blizzard failed
    # to update the version field properly (eg 5.0.0).
    versions = set()

    set_of_replays_upper = set(replay_directory.rglob("*.SC2Replay"))
    set_of_replays_lower = set(replay_directory.rglob("*.sc2replay"))
    set_of_replays = set_of_replays_upper | set_of_replays_lower
    list_of_replays = list(set_of_replays)

    try:
        for replay_path in list_of_replays:
            version = read_replay_version(
                replay_path=str(replay_path),
                run_config=run_config,
            )
            versions.add(version)
    except KeyboardInterrupt:
        pass

    return versions


def save_versions_to_file(versions: Set[Version], output_file: Path) -> Path:
    """
    Save the versions to a file.
    """
    with output_file.open("w") as f:
        for version in sorted(versions):
            f.write(f"{version}\n")

    return output_file


@click.command(
    help="Acquires the version information from the replays placed within the given directory."
)
@click.option(
    "--replay_directory",
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=False,
        resolve_path=True,
        path_type=Path,
    ),
    required=True,
    help="Directory containing the replays to analyze.",
)
@click.option(
    "--output_file",
    type=click.Path(
        dir_okay=False,
        file_okay=True,
        resolve_path=True,
        path_type=Path,
    ),
    required=False,
    help="File to write the version information to. If not provided, prints to stdout.",
)
def main(replay_directory: Path, output_file: Path | None):
    replay_versions = get_replay_version(replay_directory=replay_directory)

    if output_file:
        if not replay_versions:
            logging.warning(
                "No replay versions found. Exiting without writing to file."
            )
            return

        save_versions_to_file(versions=replay_versions, output_file=output_file)

    for version in replay_versions:
        print(version)


if __name__ == "__main__":
    main()
