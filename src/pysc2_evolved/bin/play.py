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
"""Run SC2 to play a game or a replay."""

import getpass
import platform
import sys
import time

import click
from s2clientprotocol import common_pb2
from s2clientprotocol import sc2api_pb2 as sc_pb

from pysc2_evolved import maps, run_configs
from pysc2_evolved.env import sc2_env
from pysc2_evolved.lib import renderer_human, stopwatch
from pysc2_evolved.lib.get_replay_version import get_replay_version


def play(
    render: bool,
    realtime: bool,
    full_screen: bool,
    fps: float,
    step_mul: int,
    render_sync: bool,
    feature_screen_size: int,
    feature_minimap_size: int,
    feature_camera_width: int,
    rgb_screen_size: str,
    rgb_minimap_size: str,
    window_size: str,
    video: str,
    max_game_steps: int,
    max_episode_steps: int,
    user_name: str,
    user_race: str,
    bot_race: str,
    difficulty: str,
    bot_build: str,
    disable_fog: bool,
    observed_player: int,
    profile: bool,
    trace: bool,
    save_replay: bool,
    map_name: str,
    battle_net_map: bool,
    map_path: str,
    replay: str,
):
    """Run SC2 to play a game or a replay."""
    if trace:
        stopwatch.sw.trace()
    elif profile:
        stopwatch.sw.enable()

    if (map_name and replay) or (not map_name and not replay):
        sys.exit("Must supply either a map or replay.")

    if replay and not replay.lower().endswith("sc2replay"):
        sys.exit("Replay must end in .SC2Replay.")

    if realtime and replay:
        # TODO(tewalds): Support realtime in replays once the game supports it.
        sys.exit("realtime isn't possible for replays yet.")

    if render and (realtime or full_screen):
        sys.exit("disable pygame rendering if you want realtime or full_screen.")

    if platform.system() == "Linux" and (realtime or full_screen):
        sys.exit("realtime and full_screen only make sense on Windows/MacOS.")

    if not render and render_sync:
        sys.exit("render_sync only makes sense with pygame rendering on.")

    run_config = run_configs.get()

    interface = sc_pb.InterfaceOptions()
    interface.raw = render
    interface.raw_affects_selection = True
    interface.raw_crop_to_playable_area = True
    interface.score = True
    interface.show_cloaked = True
    interface.show_burrowed_shadows = True
    interface.show_placeholders = True
    if feature_screen_size and feature_minimap_size:
        interface.feature_layer.width = feature_camera_width
        interface.feature_layer.resolution.CopyFrom(
            common_pb2.Size2DI(x=feature_screen_size, y=feature_screen_size)
        )
        interface.feature_layer.minimap_resolution.CopyFrom(
            common_pb2.Size2DI(x=feature_minimap_size, y=feature_minimap_size)
        )
        interface.feature_layer.crop_to_playable_area = True
        interface.feature_layer.allow_cheating_layers = True
    if render and rgb_screen_size and rgb_minimap_size:
        interface.render.resolution.CopyFrom(
            common_pb2.Size2DI(
                x=int(rgb_screen_size.split(",")[0]),
                y=int(rgb_screen_size.split(",")[1]),
            )
        )
        interface.render.minimap_resolution.CopyFrom(
            common_pb2.Size2DI(
                x=int(rgb_minimap_size),
                y=int(rgb_minimap_size),
            )
        )

    max_episode_steps = max_episode_steps

    if map_name:
        create = sc_pb.RequestCreateGame(realtime=realtime, disable_fog=disable_fog)
        try:
            map_inst = maps.get(map_name)
        except maps.lib.NoMapError:
            if battle_net_map:
                create.battlenet_map_name = map_name
            else:
                raise
        else:
            if map_inst.game_steps_per_episode:
                max_episode_steps = map_inst.game_steps_per_episode
            if battle_net_map:
                create.battlenet_map_name = map_inst.battle_net
            else:
                create.local_map.map_path = map_inst.path
                create.local_map.map_data = map_inst.data(run_config)

        create.player_setup.add(type=sc_pb.Participant)
        create.player_setup.add(
            type=sc_pb.Computer,
            race=sc2_env.Race[bot_race],
            difficulty=sc2_env.Difficulty[difficulty],
            ai_build=sc2_env.BotBuild[bot_build],
        )
        join = sc_pb.RequestJoinGame(
            options=interface,
            race=sc2_env.Race[user_race],
            player_name=user_name,
        )
        version = None
    else:
        replay_data = run_config.replay_data(replay)
        start_replay = sc_pb.RequestStartReplay(
            replay_data=replay_data,
            options=interface,
            disable_fog=disable_fog,
            observed_player_id=observed_player,
        )
        version = get_replay_version(replay_data)
        run_config = run_configs.get(version=version)  # Replace the run config.

    with run_config.start(
        full_screen=full_screen,
        window_size=window_size,
        want_rgb=interface.HasField("render"),
    ) as controller:
        if map_name:
            controller.create_game(create)
            controller.join_game(join)
        else:
            info = controller.replay_info(replay_data)
            print(" Replay info ".center(60, "-"))
            print(info)
            print("-" * 60)
            map_path = map_path or info.local_map_path
            if map_path:
                start_replay.map_data = run_config.map_data(
                    map_path, len(info.player_info)
                )
            controller.start_replay(start_replay)

        if render:
            renderer = renderer_human.RendererHuman(
                fps=fps,
                step_mul=step_mul,
                render_sync=render_sync,
                video=video,
            )
            renderer.run(
                run_config,
                controller,
                max_game_steps=max_game_steps,
                game_steps_per_episode=max_episode_steps,
                save_replay=save_replay,
            )
        else:  # Still step forward so the Mac/Windows renderer works.
            try:
                while True:
                    frame_start_time = time.time()
                    if not realtime:
                        controller.step(step_mul)
                    obs = controller.observe()

                    if obs.player_result:
                        break
                    time.sleep(max(0, frame_start_time + 1 / fps - time.time()))
            except KeyboardInterrupt:
                pass
            print("Score: ", obs.observation.score.score)
            print("Result: ", obs.player_result)
            if map_name and save_replay:
                replay_save_loc = run_config.save_replay(
                    controller.save_replay(), "local", map_name
                )
                print("Replay saved to:", replay_save_loc)
                # Save scores so we know how the human player did.
                with open(replay_save_loc.replace("SC2Replay", "txt"), "w") as f:
                    f.write("{}\n".format(obs.observation.score.score))

    if profile:
        print(stopwatch.sw)


@click.command(help="Run SC2 to play a game or a replay.")
@click.option(
    "--render/--no_render",
    help="Whether to render with pygame.",
    type=bool,
    default=True,
    is_flag=True,
)
@click.option(
    "--realtime/--no_realtime",
    help="Whether to run in realtime mode.",
    type=bool,
    default=False,
    is_flag=True,
)
@click.option(
    "--full_screen/--no_full_screen",
    help="Whether to run full screen.",
    type=bool,
    default=False,
    is_flag=True,
)
@click.option(
    "--fps",
    help="Frames per second to run the game.",
    type=float,
    default=22.4,
)
@click.option(
    "--step_mul",
    help="Game steps per observation.",
    type=int,
    default=1,
)
@click.option(
    "--render_sync/--no_render_sync",
    help="Turn on sync rendering.",
    type=bool,
    default=False,
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
    "--feature_camera_width",
    help="Width of the feature layer camera.",
    type=int,
    default=24,
)
@click.option(
    "--rgb_screen_size",
    help="Resolution for rendered screen.",
    type=str,
    default="256,192",
)
@click.option(
    "--rgb_minimap_size",
    help="Resolution for rendered minimap.",
    type=str,
    default="128",
)
@click.option(
    "--window_size",
    help="Screen size if not full screen.",
    type=str,
    default="640,480",
)
@click.option(
    "--video",
    help="Path to render a video of observations.",
    type=str,
    default=None,
)
@click.option(
    "--max_game_steps",
    help="Total game steps to run.",
    type=int,
    default=0,
)
@click.option(
    "--max_episode_steps",
    help="Total game steps per episode.",
    type=int,
    default=0,
)
@click.option(
    "--user_name",
    help="Name of the human player for replays.",
    type=str,
    default=getpass.getuser(),
)
@click.option(
    "--user_race",
    help="User's race",
    type=click.Choice(sc2_env.Race._member_names_, case_sensitive=False),
    default="random",
)
@click.option(
    "--bot_race",
    help="Bot's race",
    type=click.Choice(sc2_env.Race._member_names_, case_sensitive=False),
    default="random",
)
@click.option(
    "--difficulty",
    help="Bot's strength",
    type=click.Choice(sc2_env.Difficulty._member_names_, case_sensitive=False),
    default="very_easy",
)
@click.option(
    "--bot_build",
    help="Bot's build strategy",
    type=click.Choice(sc2_env.BotBuild._member_names_, case_sensitive=False),
    default="random",
)
@click.option(
    "--disable_fog/--enable_fog",
    help="Disable fog of war.",
    type=bool,
    default=False,
    is_flag=True,
)
@click.option(
    "--observed_player",
    help="Which player to observe.",
    type=int,
    default=1,
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
    "--save_replay/--no_save_replay",
    help="Whether to save a replay at the end.",
    type=bool,
    default=False,
    is_flag=True,
)
@click.option(
    "--map_name",
    help="Name of a map to use to play.",
    type=str,
    default=None,
)
@click.option(
    "--battle_net_map/--no_battle_net_map",
    help="Use the battle.net map version.",
    type=bool,
    default=False,
    is_flag=True,
)
@click.option(
    "--map_path",
    help="Override the map for this replay.",
    type=str,
    default=None,
)
@click.option(
    "--replay",
    help="Path to the replay to show.",
    type=str,
    default=None,
)
def main(
    render: bool,
    realtime: bool,
    full_screen: bool,
    fps: float,
    step_mul: int,
    render_sync: bool,
    feature_screen_size: int,
    feature_minimap_size: int,
    feature_camera_width: int,
    rgb_screen_size: str,
    rgb_minimap_size: str,
    window_size: str,
    video: str,
    max_game_steps: int,
    max_episode_steps: int,
    user_name: str,
    user_race: str,
    bot_race: str,
    difficulty: str,
    bot_build: str,
    disable_fog: bool,
    observed_player: int,
    profile: bool,
    trace: bool,
    save_replay: bool,
    map_name: str,
    battle_net_map: bool,
    map_path: str,
    replay: str,
):
    play(
        render=render,
        realtime=realtime,
        full_screen=full_screen,
        fps=fps,
        step_mul=step_mul,
        render_sync=render_sync,
        feature_screen_size=feature_screen_size,
        feature_minimap_size=feature_minimap_size,
        feature_camera_width=feature_camera_width,
        rgb_screen_size=rgb_screen_size,
        rgb_minimap_size=rgb_minimap_size,
        window_size=window_size,
        video=video,
        max_game_steps=max_game_steps,
        max_episode_steps=max_episode_steps,
        user_name=user_name,
        user_race=user_race,
        bot_race=bot_race,
        difficulty=difficulty,
        bot_build=bot_build,
        disable_fog=disable_fog,
        observed_player=observed_player,
        profile=profile,
        trace=trace,
        save_replay=save_replay,
        map_name=map_name,
        battle_net_map=battle_net_map,
        map_path=map_path,
        replay=replay,
    )


# def entry_point():  # Needed so setup.py scripts work.
#     app.run(play)


if __name__ == "__main__":
    main()
