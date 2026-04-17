#!/usr/bin/python
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
"""Dump out stats about all the actions that are in use in a set of replays."""

from __future__ import annotations

import collections
import enum
import logging
import multiprocessing
import os
import queue
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Tuple

import click
from s2clientprotocol import common_pb2 as sc_common
from s2clientprotocol import sc2api_pb2 as sc_pb

from pysc2_evolved import run_configs
from pysc2_evolved.lib import (
    features,
    gfile,
    point,
    protocol,
    remote_controller,
    static_data,
)
from pysc2_evolved.lib.get_replay_version import get_replay_version
from pysc2_evolved.lib.remote_controller import RemoteController
from pysc2_evolved.run_configs.lib import RunConfig
from pysc2_evolved.settings import LOGGING_FORMAT


def sorted_dict_str(d):
    return "{%s}" % ", ".join(
        "%s: %s" % (k, d[k]) for k in sorted(d, key=d.get, reverse=True)
    )


class ReplayStats(object):
    """Summary stats of the replays seen so far."""

    def __init__(self):
        self.replays = 0
        self.steps = 0
        self.camera_move = 0
        self.select_pt = 0
        self.select_rect = 0
        self.control_group = 0
        self.maps = collections.defaultdict(int)
        self.races = collections.defaultdict(int)
        self.unit_ids = collections.defaultdict(int)
        self.valid_abilities = collections.defaultdict(int)
        self.made_abilities = collections.defaultdict(int)
        self.valid_actions = collections.defaultdict(int)
        self.made_actions = collections.defaultdict(int)
        self.buffs = collections.defaultdict(int)
        self.upgrades = collections.defaultdict(int)
        self.effects = collections.defaultdict(int)
        self.crashing_replays = set()
        self.invalid_replays = set()

    def merge(self, other: ReplayStats):
        """Merge another ReplayStats into this one."""

        def merge_dict(a: Dict, b: Dict):
            for k, v in b.items():
                a[k] += v

        self.replays += other.replays
        self.steps += other.steps
        self.camera_move += other.camera_move
        self.select_pt += other.select_pt
        self.select_rect += other.select_rect
        self.control_group += other.control_group
        merge_dict(self.maps, other.maps)
        merge_dict(self.races, other.races)
        merge_dict(self.unit_ids, other.unit_ids)
        merge_dict(self.valid_abilities, other.valid_abilities)
        merge_dict(self.made_abilities, other.made_abilities)
        merge_dict(self.valid_actions, other.valid_actions)
        merge_dict(self.made_actions, other.made_actions)
        merge_dict(self.buffs, other.buffs)
        merge_dict(self.upgrades, other.upgrades)
        merge_dict(self.effects, other.effects)
        self.crashing_replays |= other.crashing_replays
        self.invalid_replays |= other.invalid_replays

    def __str__(self):
        def len_sorted_dict(s):
            return (len(s), sorted_dict_str(s))

        def len_sorted_list(s) -> Tuple[int, List]:
            return (len(s), sorted(s))

        new_abilities = (
            set(self.valid_abilities.keys()) | set(self.made_abilities.keys())
        ) - set(static_data.ABILITIES)
        new_units = set(self.unit_ids) - set(static_data.UNIT_TYPES)
        new_buffs = set(self.buffs) - set(static_data.BUFFS)
        new_upgrades = set(self.upgrades) - set(static_data.UPGRADES)
        return "\n\n".join(
            (
                "Replays: %s, Steps total: %s" % (self.replays, self.steps),
                "Camera move: %s, Select pt: %s, Select rect: %s, Control group: %s"
                % (
                    self.camera_move,
                    self.select_pt,
                    self.select_rect,
                    self.control_group,
                ),
                "Maps: %s\n%s" % len_sorted_dict(self.maps),
                "Races: %s\n%s" % len_sorted_dict(self.races),
                "Unit ids: %s\n%s" % len_sorted_dict(self.unit_ids),
                "New units: %s \n%s" % len_sorted_list(new_units),
                "Valid abilities: %s\n%s" % len_sorted_dict(self.valid_abilities),
                "Made abilities: %s\n%s" % len_sorted_dict(self.made_abilities),
                "New abilities: %s\n%s" % len_sorted_list(new_abilities),
                "Valid actions: %s\n%s" % len_sorted_dict(self.valid_actions),
                "Made actions: %s\n%s" % len_sorted_dict(self.made_actions),
                "Buffs: %s\n%s" % len_sorted_dict(self.buffs),
                "New buffs: %s\n%s" % len_sorted_list(new_buffs),
                "Upgrades: %s\n%s" % len_sorted_dict(self.upgrades),
                "New upgrades: %s\n%s" % len_sorted_list(new_upgrades),
                "Effects: %s\n%s" % len_sorted_dict(self.effects),
                "Crashing replays: %s\n%s" % len_sorted_list(self.crashing_replays),
                "Invalid replays: %s\n%s" % len_sorted_list(self.invalid_replays),
            )
        )


class ProcessStats(object):
    """Stats for a worker process."""

    # REVIEW: Check if the proc_id is an int:
    def __init__(self, step_mul: int, proc_id: int):
        self.step_mul = step_mul
        self.proc_id = proc_id
        self.time = time.time()
        self.stage = ""
        self.replay = ""
        self.replay_stats = ReplayStats()

    def update(self, stage: str):
        self.time = time.time()
        self.stage = stage

    def __str__(self):
        return (
            "[%2d] replay: %10s, replays: %5d, steps: %7d, game loops: %7s, "
            "last: %12s, %3d s ago"
            % (
                self.proc_id,
                self.replay,
                self.replay_stats.replays,
                self.replay_stats.steps,
                self.replay_stats.steps * self.step_mul,
                self.stage,
                time.time() - self.time,
            )
        )


def valid_replay(info, ping) -> bool:
    """Make sure the replay isn't corrupt, and is worth looking at."""
    if (
        info.HasField("error")
        or info.base_build != ping.base_build  # different game version
        or info.game_duration_loops < 1000
        or len(info.player_info) != 2
    ):
        # Probably corrupt, or just not interesting.
        return False
    for p in info.player_info:
        if p.player_apm < 10 or p.player_mmr < 1000:
            # Low APM = player just standing around.
            # Low MMR = corrupt replay or player who is weak.
            return False
    return True


class ReplayProcessor(multiprocessing.Process):
    """A Process that pulls replays and processes them."""

    def __init__(
        self,
        interface,
        step_mul: int,
        proc_id: int,
        run_config: RunConfig,
        replay_queue: multiprocessing.JoinableQueue,
        stats_queue: multiprocessing.Queue,
    ):
        super(ReplayProcessor, self).__init__()

        self.interface = interface
        self.step_mul = step_mul
        self.proc_id = proc_id

        self.run_config = run_config
        self.replay_queue = replay_queue

        # TODO: Most likely needs to be renamed to ObservationRecorderQueue
        # this will make sure that there is some nice customizability:
        self.stats_queue = stats_queue

        # TODO: Another self variable is needed e.g. self.observation_recorders: List[ObservationRecorder]
        # Then there is no need to be adding anything to self.stats.
        # This is because all of the statistics will be kept in the recorders that will have a method:
        # e.g. def record_from_observation(observation)

        # REVIEW: This will not be needed:
        self.stats = ProcessStats(step_mul=self.step_mul, proc_id=self.proc_id)

    def run(self):
        def exit_quietly(a, b):
            sys.exit()

        signal.signal(signal.SIGTERM, exit_quietly)  # Exit quietly.
        self._update_stage("spawn")
        replay_name = "none"
        while True:
            self._print("Starting up a new SC2 instance.")
            self._update_stage("launch")
            try:
                with self.run_config.start(
                    want_rgb=self.interface.HasField("render")
                ) as controller:
                    self._print("SC2 Started successfully.")
                    ping = controller.ping()
                    for _ in range(300):
                        try:
                            replay_path = self.replay_queue.get()
                        except queue.Empty:
                            self._update_stage("done")
                            self._print("Empty queue, returning")
                            return
                        try:
                            replay_name = os.path.basename(replay_path)[:10]
                            self.stats.replay = replay_name
                            self._print("Got replay: %s" % replay_path)
                            self._update_stage("open replay file")
                            replay_data = self.run_config.replay_data(replay_path)
                            self._update_stage("replay_info")
                            info = controller.replay_info(replay_data)
                            self._print(
                                (" Replay Info %s " % replay_name).center(60, "-")
                            )
                            self._print(info)
                            self._print("-" * 60)
                            if valid_replay(info, ping):
                                self.stats.replay_stats.maps[info.map_name] += 1
                                for player_info in info.player_info:
                                    race_name = sc_common.Race.Name(
                                        player_info.player_info.race_actual
                                    )
                                    self.stats.replay_stats.races[race_name] += 1
                                map_data = None
                                if info.local_map_path:
                                    self._update_stage("open map file")
                                    map_data = self.run_config.map_data(
                                        map_name=info.local_map_path
                                    )
                                for player_id in [1, 2]:
                                    self._print(
                                        "Starting %s from player %s's perspective"
                                        % (replay_name, player_id)
                                    )
                                    self.process_replay(
                                        controller=controller,
                                        replay_data=replay_data,
                                        map_data=map_data,
                                        player_id=player_id,
                                    )
                            else:
                                self._print("Replay is invalid.")
                                self.stats.replay_stats.invalid_replays.add(replay_name)
                        finally:
                            self.replay_queue.task_done()
                    self._update_stage("shutdown")
            except (
                protocol.ConnectionError,
                protocol.ProtocolError,
                remote_controller.RequestError,
            ):
                self.stats.replay_stats.crashing_replays.add(replay_name)
            except KeyboardInterrupt:
                return

    def _print(self, s):
        for line in str(s).strip().splitlines():
            print("[%s] %s" % (self.stats.proc_id, line))

    def _update_stage(self, stage: str):
        self.stats.update(stage)
        self.stats_queue.put(self.stats)

    # REVIEW: Make sure that the player ID is an integer:
    def process_replay(
        self,
        controller: RemoteController,
        step_mul: int,
        replay_data,
        map_data,
        player_id: int,
    ):
        """Process a single replay, updating the stats."""
        self._update_stage("start_replay")
        controller.start_replay(
            sc_pb.RequestStartReplay(
                replay_data=replay_data,
                map_data=map_data,
                options=self.interface,
                observed_player_id=player_id,
            )
        )

        feat = features.features_from_game_info(controller.game_info())

        self.stats.replay_stats.replays += 1
        self._update_stage("step")
        controller.step()

        # TODO: Make this a little bit more general,
        # pass a callable that takes in the observation and does with it whatever:
        # Another case would be to just create different implementations of the ReplayProcessor
        # and treat it as a base class:
        while True:
            self.stats.replay_stats.steps += 1
            self._update_stage("observe")
            obs = controller.observe()

            for action in obs.actions:
                action_feature_layer = action.action_feature_layer
                if action_feature_layer.HasField("unit_command"):
                    self.stats.replay_stats.made_abilities[
                        action_feature_layer.unit_command.ability_id
                    ] += 1
                if action_feature_layer.HasField("camera_move"):
                    self.stats.replay_stats.camera_move += 1
                if action_feature_layer.HasField("unit_selection_point"):
                    self.stats.replay_stats.select_pt += 1
                if action_feature_layer.HasField("unit_selection_rect"):
                    self.stats.replay_stats.select_rect += 1
                if action.action_ui.HasField("control_group"):
                    self.stats.replay_stats.control_group += 1

                try:
                    func = feat.reverse_action(action).function
                except ValueError:
                    func = -1
                self.stats.replay_stats.made_actions[func] += 1

            for valid in obs.observation.abilities:
                self.stats.replay_stats.valid_abilities[valid.ability_id] += 1

            for u in obs.observation.raw_data.units:
                self.stats.replay_stats.unit_ids[u.unit_type] += 1
                for b in u.buff_ids:
                    self.stats.replay_stats.buffs[b] += 1

            for u in obs.observation.raw_data.player.upgrade_ids:
                self.stats.replay_stats.upgrades[u] += 1

            for e in obs.observation.raw_data.effects:
                self.stats.replay_stats.effects[e.effect_id] += 1

            for ability_id in feat.available_actions(obs.observation):
                self.stats.replay_stats.valid_actions[ability_id] += 1

            if obs.player_result:
                break

            self._update_stage("step")
            controller.step(step_mul)


# REVIEW: Thus handles the things entering from the stats_queue
# Needs to be refactored to handle persistence of all of the planned
# ObservationRecorder types.
# Most likely some sort of an interface like PersistenceTypeInterface
# with PersistenceTypeStrategy or Factory
# with implementations such as DBPersistence, DiskPersistence.
# The goal is to save the data of all of the replays per directory on which the
# ReplayProcessor was ran.
def stats_printer(parallel: int, step_mul: int, stats_queue: multiprocessing.Queue):
    """A thread that consumes stats_queue and prints them every 10 seconds."""
    proc_stats = [ProcessStats(step_mul=step_mul, proc_id=i) for i in range(parallel)]
    print_time = start_time = time.time()
    width = 107

    running = True
    while running:
        print_time += 10

        while time.time() < print_time:
            try:
                s = stats_queue.get(True, print_time - time.time())
                if s is None:  # Signal to print and exit NOW!
                    running = False
                    break
                proc_stats[s.proc_id] = s
            except queue.Empty:
                pass

        replay_stats = ReplayStats()
        for s in proc_stats:
            replay_stats.merge(s.replay_stats)

        print((" Summary %0d secs " % (print_time - start_time)).center(width, "="))
        print(replay_stats)
        print(" Process stats ".center(width, "-"))
        print("\n".join(str(s) for s in proc_stats))
        print("=" * width)


def replay_queue_filler(
    replay_queue: multiprocessing.JoinableQueue,
    replay_list: List[str],
):
    """A thread that fills the replay_queue with replay filenames."""
    for replay_path in replay_list:
        replay_queue.put(replay_path)


def replay_actions(
    replays: Path,
    sc2_version: str | None,
    parallel: int,
    step_mul: int,
):
    size = point.Point(16, 16)
    interface = sc_pb.InterfaceOptions(
        raw=True,
        score=False,
        feature_layer=sc_pb.SpatialCameraSetup(width=24),
    )
    size.assign_to(interface.feature_layer.resolution)
    size.assign_to(interface.feature_layer.minimap_resolution)

    """Dump stats about all the actions that are in use in a set of replays."""
    run_config = run_configs.get()

    if not gfile.Exists(replays):
        sys.exit("{} doesn't exist.".format(replays))

    stats_queue = multiprocessing.Queue()
    stats_thread = threading.Thread(
        target=stats_printer,
        args=(
            parallel,
            step_mul,
            stats_queue,
        ),
    )
    try:
        # For some reason buffering everything into a JoinableQueue makes the
        # program not exit, so save it into a list then slowly fill it into the
        # queue in a separate thread. Grab the list synchronously so we know there
        # is work in the queue before the SC2 processes actually run, otherwise
        # The replay_queue.join below succeeds without doing any work, and exits.
        print("Getting replay list:", replays)
        replay_list = sorted(run_config.replay_paths(replays))
        print(len(replay_list), "replays found.")
        if not replay_list:
            return

        if not sc2_version:  # ie not set explicitly.
            version = get_replay_version(run_config.replay_data(replay_list[0]))
            run_config = run_configs.get(version=version)
            print("Assuming version:", version.game_version)

        print()

        stats_thread.start()
        replay_queue = multiprocessing.JoinableQueue(parallel * 10)
        replay_queue_thread = threading.Thread(
            target=replay_queue_filler, args=(replay_queue, replay_list)
        )
        replay_queue_thread.daemon = True
        replay_queue_thread.start()

        for i in range(min(len(replay_list), parallel)):
            p = ReplayProcessor(
                interface=interface,
                step_mul=step_mul,
                proc_id=i,
                run_config=run_config,
                replay_queue=replay_queue,
                stats_queue=stats_queue,
            )
            p.daemon = True
            p.start()
            time.sleep(1)  # Stagger startups, otherwise they seem to conflict somehow

        replay_queue.join()  # Wait for the queue to empty.
    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, exiting.")
    finally:
        stats_queue.put(None)  # Tell the stats_thread to print and exit.
        if stats_thread.is_alive():
            stats_thread.join()


class LogLevel(str, enum.Enum):
    """Log levels for the application."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@click.command(help="")
@click.option(
    "--replays",
    type=click.Path(
        exists=True,
        file_okay=False,
        resolve_path=True,
        path_type=Path,
    ),
    help="Path to a directory of replays.",
)
@click.option(
    "--sc2_version",
    type=str,
    default="",
    help="The version of SC2 to use. If not set, the latest version will be used.",
)
@click.option(
    "--parallel",
    type=int,
    default=1,
    help="How many instances to run in parallel.",
)
@click.option(
    "--step_mul",
    type=int,
    default=8,
    help="How many game steps per observation.",
)
@click.option(
    "--log",
    type=LogLevel,
    default=LogLevel.INFO,
    help="Set the log level.",
)
def main(
    replays: Path,
    sc2_version: str,
    parallel: int,
    step_mul: int,
    log: LogLevel,
):
    numeric_level = getattr(logging, log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {numeric_level}")
    logging.basicConfig(format=LOGGING_FORMAT, level=numeric_level)

    replay_actions(
        replays=replays,
        sc2_version=sc2_version,
        parallel=parallel,
        step_mul=step_mul,
    )


if __name__ == "__main__":
    main()
