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
"""Run an agent."""

import importlib
import threading
from dataclasses import dataclass
from typing import List, TypeVar

import click

from pysc2_evolved import maps
from pysc2_evolved.agents.base_agent import BaseAgent
from pysc2_evolved.env import available_actions_printer, run_loop, sc2_env
from pysc2_evolved.lib import stopwatch

ImplementsBaseAgent = TypeVar("ImplementsBaseAgent", bound=BaseAgent)


@dataclass
class RunThreadArgs:
    agent_classes: List[ImplementsBaseAgent]
    players: List[sc2_env.Agent]
    map_name: str
    visualize: bool

    battle_net_map: bool
    feature_screen_size: int
    feature_minimap_size: int
    rgb_screen_size: str
    rgb_minimap_size: str
    action_space: str
    use_feature_units: bool
    use_raw_units: bool
    step_mul: int
    game_steps_per_episode: int
    disable_fog: bool

    max_agent_steps: int
    max_episodes: int
    save_replay: bool


def run_thread(run_thread_args: RunThreadArgs):
    """Run one thread worth of the environment with agents."""
    with sc2_env.SC2Env(
        map_name=run_thread_args.map_name,
        battle_net_map=run_thread_args.battle_net_map,
        players=run_thread_args.players,
        agent_interface_format=sc2_env.parse_agent_interface_format(
            feature_screen=run_thread_args.feature_screen_size,
            feature_minimap=run_thread_args.feature_minimap_size,
            rgb_screen=run_thread_args.rgb_screen_size,
            rgb_minimap=run_thread_args.rgb_minimap_size,
            action_space=run_thread_args.action_space,
            use_feature_units=run_thread_args.use_feature_units,
            use_raw_units=run_thread_args.use_raw_units,
        ),
        step_mul=run_thread_args.step_mul,
        game_steps_per_episode=run_thread_args.game_steps_per_episode,
        disable_fog=run_thread_args.disable_fog,
        visualize=run_thread_args.visualize,
    ) as env:
        env = available_actions_printer.AvailableActionsPrinter(env)
        agents = [agent_cls() for agent_cls in run_thread_args.agent_classes]
        run_loop.run_loop(
            agents=agents,
            env=env,
            max_frames=run_thread_args.max_agent_steps,
            max_episodes=run_thread_args.max_episodes,
        )
        if run_thread_args.save_replay:
            env.save_replay(run_thread_args.agent_classes[0].__name__)


def run_agent(
    render: bool,
    feature_screen_size: int,
    feature_minimap_size: int,
    rgb_screen_size: str,
    rgb_minimap_size: str,
    action_space: str,
    use_feature_units: bool,
    use_raw_units: bool,
    enable_fog: bool,
    max_agent_steps: int,
    game_steps_per_episode: int,
    max_episodes: int,
    step_mul: int,
    agent: str,
    agent_name: str,
    agent_race: str,
    agent2: str,
    agent2_name: str,
    agent2_race: str,
    difficulty: str,
    bot_build: str,
    profile: bool,
    trace: bool,
    parallel: int,
    save_replay: bool,
    map_name: str,
    battle_net_map: bool,
):
    """
    Runs an agent in the StarCraft II environment, with the given configuration.

    Parameters
    ----------
    render : bool
        Whether to render with pygame.
    feature_screen_size : int
        Resolution for screen feature layers.
    feature_minimap_size : int
        Resolution for minimap feature layers.
    rgb_screen_size : tuple[int, int] | int
        Resolution for rendered screen, as "width,height" or size.
    rgb_minimap_size : tuple[int, int] | int
        Resolution for rendered minimap, as "width,height" or size.
    action_space : str
        Which action space to use.
    use_feature_units : bool
        _description_
    use_raw_units : bool
        _description_
    enable_fog : bool
        _description_
    max_agent_steps : int
        _description_
    game_steps_per_episode : int
        _description_
    max_episodes : int
        _description_
    step_mul : int
        _description_
    agent : str
        _description_
    agent_name : str
        Name of the agent in replays. Defaults to the class name.
    agent_race : str
        Race of the first agent.
    agent2 : str
        _description_
    agent2_name : str
        _description_
    agent2_race : str
        _description_
    difficulty : str
        _description_
    bot_build : str
        _description_
    profile : bool
        _description_
    trace : bool
        _description_
    parallel : int
        _description_
    save_replay : bool
        _description_
    map_name : str
        _description_
    battle_net_map : bool
        _description_
    """

    if trace:
        stopwatch.sw.trace()
    elif profile:
        stopwatch.sw.enable()

    map_inst = maps.get(map_name=map_name)

    agent_classes = []
    players = []

    agent_module, agent_name = agent.rsplit(".", 1)
    agent_cls = getattr(importlib.import_module(agent_module), agent_name)
    agent_classes.append(agent_cls)
    players.append(sc2_env.Agent(sc2_env.Race[agent_race], agent_name or agent_name))

    if map_inst.players >= 2:
        if agent2 == "Bot":
            players.append(
                sc2_env.Bot(
                    sc2_env.Race[agent2_race],
                    sc2_env.Difficulty[difficulty],
                    sc2_env.BotBuild[bot_build],
                )
            )
        else:
            agent_module, agent_name = agent2.rsplit(".", 1)
            agent_cls = getattr(importlib.import_module(agent_module), agent_name)
            agent_classes.append(agent_cls)
            players.append(
                sc2_env.Agent(sc2_env.Race[agent2_race], agent2_name or agent_name)
            )

    threads = []
    thread_args = RunThreadArgs(
        agent_classes=agent_classes,
        players=players,
        map_name=map_name,
        visualize=False,
        battle_net_map=battle_net_map,
        feature_screen_size=feature_screen_size,
        feature_minimap_size=feature_minimap_size,
        rgb_screen_size=rgb_screen_size,
        rgb_minimap_size=rgb_minimap_size,
        action_space=action_space,
        use_feature_units=use_feature_units,
        use_raw_units=use_raw_units,
        step_mul=step_mul,
        game_steps_per_episode=game_steps_per_episode,
        disable_fog=enable_fog,
        max_agent_steps=max_agent_steps,
        max_episodes=max_episodes,
        save_replay=save_replay,
    )
    for _ in range(parallel - 1):
        t = threading.Thread(target=run_thread, args=thread_args)
        threads.append(t)
        t.start()

    thread_args.visualize = render
    run_thread(run_thread_args=thread_args)

    for t in threads:
        t.join()

    if profile:
        print(stopwatch.sw)


@click.command(help="Runs an agent in StarCraft II environment.")
@click.option(
    "--render/--no_render",
    help="Whether to render with pygame.",
    type=bool,
    default=True,
    is_flag=True,
)
@click.option(
    "--feature_screen_size",
    help="Resolution for screen feature layers.",
    type=int,
    default=84,
)
@click.option(
    "--feature_minimap_size",
    help="Resolution for minimap feature layers.",
    type=int,
    default=64,
)
@click.option(
    "--rgb_screen_size",
    help="Resolution for rendered screen.",
    type=str,
    default=None,
)
@click.option(
    "--rgb_minimap_size",
    help="Resolution for rendered minimap.",
    type=int,
    default=None,
)
@click.option(
    "--action_space",
    help="Which action space to use.",
    type=click.Choice(sc2_env.ActionSpace._member_names_),
    default=None,
)
@click.option(
    "--use_feature_units/--no_feature_units",
    help="Whether to include feature units.",
    type=bool,
    default=False,
    is_flag=True,
)
@click.option(
    "--use_raw_units/--no_raw_units",
    help="Whether to include raw units.",
    type=bool,
    default=False,
    is_flag=True,
)
@click.option(
    "--enable_fog/--disable_fog",
    help="Whether to disable Fog of War.",
    type=bool,
    default=False,
    is_flag=True,
)
@click.option(
    "--max_agent_steps",
    help="Total agent steps.",
    type=int,
    default=0,
)
@click.option(
    "--game_steps_per_episode",
    help="Game steps per episode.",
    type=int,
    default=None,
)
@click.option(
    "--max_episodes",
    help="Total episodes.",
    type=int,
    default=0,
)
@click.option(
    "--step_mul",
    help="Game steps per agent step.",
    type=int,
    default=8,
)
@click.option(
    "--agent",
    help="Which agent to run, as a python path to an Agent class.",
    type=str,
    default="pysc2_evolved.agents.random_agent.RandomAgent",
)
@click.option(
    "--agent_name",
    help="Name of the agent in replays. Defaults to the class name.",
    type=str,
    default=None,
)
@click.option(
    "--agent_race",
    help="Agent 1's race.",
    type=click.Choice(sc2_env.Race._member_names_),
    default="random",
)
@click.option(
    "--agent2",
    help="Second agent, either Bot or agent class.",
    type=str,
    default="Bot",
)
@click.option(
    "--agent2_name",
    help="Name of the agent in replays. Defaults to the class name.",
    type=str,
    default=None,
)
@click.option(
    "--agent2_race",
    help="Agent 2's race.",
    type=click.Choice(sc2_env.Race._member_names_),
    default="random",
)
@click.option(
    "--difficulty",
    help="If agent2 is a built-in Bot, it's strength.",
    type=click.Choice(sc2_env.Difficulty._member_names_),
    default="very_easy",
)
@click.option(
    "--bot_build",
    help="Bot's build strategy.",
    type=click.Choice(sc2_env.BotBuild._member_names_),
    default="random",
)
@click.option(
    "--profile/--no_profile",
    help="Whether to turn on code profiling.",
    type=bool,
    default=False,
    is_flag=True,
)
@click.option(
    "--trace/--no_trace",
    help="Whether to trace the code execution.",
    type=bool,
    default=False,
    is_flag=True,
)
@click.option(
    "--parallel",
    help="How many instances to run in parallel.",
    type=int,
    default=1,
)
@click.option(
    "--save_replay/--no_save_replay",
    help="Whether to save a replay at the end.",
    type=bool,
    default=True,
    is_flag=True,
)
@click.option(
    "--map_name",
    help="Name of a map to use.",
    type=str,
    required=True,
)
@click.option(
    "--battle_net_map/--no_battle_net_map",
    help="Use the battle.net map version.",
    type=bool,
    default=False,
    is_flag=True,
)
def main(
    render: bool,
    feature_screen_size: int,
    feature_minimap_size: int,
    rgb_screen_size: str,
    rgb_minimap_size: int,
    action_space: str,
    use_feature_units: bool,
    use_raw_units: bool,
    enable_fog: bool,
    max_agent_steps: int,
    game_steps_per_episode: int,
    max_episodes: int,
    step_mul: int,
    agent: str,
    agent_name: str,
    agent_race: str,
    agent2: str,
    agent2_name: str,
    agent2_race: str,
    difficulty: str,
    bot_build: str,
    profile: bool,
    trace: bool,
    parallel: int,
    save_replay: bool,
    map_name: str,
    battle_net_map: bool,
):
    if isinstance(rgb_screen_size, str):
        if "," in rgb_screen_size:
            rgb_screen_size = tuple(map(int, rgb_screen_size.split(",")))
        else:
            rgb_screen_size = int(rgb_screen_size)

    run_agent(
        render=render,
        feature_screen_size=feature_screen_size,
        feature_minimap_size=feature_minimap_size,
        rgb_screen_size=rgb_screen_size,
        rgb_minimap_size=rgb_minimap_size,
        action_space=action_space,
        use_feature_units=use_feature_units,
        use_raw_units=use_raw_units,
        enable_fog=enable_fog,
        max_agent_steps=max_agent_steps,
        game_steps_per_episode=game_steps_per_episode,
        max_episodes=max_episodes,
        step_mul=step_mul,
        agent=agent,
        agent_name=agent_name,
        agent_race=agent_race,
        agent2=agent2,
        agent2_name=agent2_name,
        agent2_race=agent2_race,
        difficulty=difficulty,
        bot_build=bot_build,
        profile=profile,
        trace=trace,
        parallel=parallel,
        save_replay=save_replay,
        map_name=map_name,
        battle_net_map=battle_net_map,
    )


if __name__ == "__main__":
    main()
