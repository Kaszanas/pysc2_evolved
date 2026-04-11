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
"""Verify that the observations match the observation spec."""

import pytest

from pysc2_evolved.agents import random_agent
from pysc2_evolved.env import sc2_env
from pysc2_evolved.tests import utils


@pytest.mark.sc2
class TestObservationSpec(utils.TestCase):
    def test_observation_matches_obs_spec(self):
        with sc2_env.SC2Env(
            map_name="Simple64",
            players=[
                sc2_env.Agent(sc2_env.Race.random),
                sc2_env.Bot(sc2_env.Race.random, sc2_env.Difficulty.easy),
            ],
            agent_interface_format=sc2_env.AgentInterfaceFormat(
                feature_dimensions=sc2_env.Dimensions(screen=(84, 87), minimap=(64, 67))
            ),
        ) as env:
            multiplayer_obs_spec = env.observation_spec()
            assert isinstance(multiplayer_obs_spec, tuple)
            assert len(multiplayer_obs_spec) == 1
            obs_spec = multiplayer_obs_spec[0]

            multiplayer_action_spec = env.action_spec()
            assert isinstance(multiplayer_action_spec, tuple)
            assert len(multiplayer_action_spec) == 1
            action_spec = multiplayer_action_spec[0]

            agent = random_agent.RandomAgent()
            agent.setup(obs_spec, action_spec)

            multiplayer_obs = env.reset()
            agent.reset()
            for _ in range(100):
                assert isinstance(multiplayer_obs, tuple)
                assert len(multiplayer_obs) == 1
                raw_obs = multiplayer_obs[0]
                obs = raw_obs.observation
                self._check_observation_matches_spec(obs, obs_spec)

                act = agent.step(raw_obs)
                multiplayer_act = (act,)
                multiplayer_obs = env.step(multiplayer_act)

    def test_heterogeneous_observations(self):
        with sc2_env.SC2Env(
            map_name="Simple64",
            players=[
                sc2_env.Agent(sc2_env.Race.random),
                sc2_env.Agent(sc2_env.Race.random),
            ],
            agent_interface_format=[
                sc2_env.AgentInterfaceFormat(
                    feature_dimensions=sc2_env.Dimensions(
                        screen=(84, 87), minimap=(64, 67)
                    )
                ),
                sc2_env.AgentInterfaceFormat(
                    rgb_dimensions=sc2_env.Dimensions(screen=128, minimap=64)
                ),
            ],
        ) as env:
            obs_specs = env.observation_spec()
            assert isinstance(obs_specs, tuple)
            assert len(obs_specs) == 2

            actions_specs = env.action_spec()
            assert isinstance(actions_specs, tuple)
            assert len(actions_specs) == 2

            agents = []
            for obs_spec, action_spec in zip(obs_specs, actions_specs):
                agent = random_agent.RandomAgent()
                agent.setup(obs_spec, action_spec)
                agent.reset()
                agents.append(agent)

            time_steps = env.reset()
            for _ in range(100):
                assert isinstance(time_steps, tuple)
                assert len(time_steps) == 2

                actions = []
                for i, agent in enumerate(agents):
                    time_step = time_steps[i]
                    obs = time_step.observation
                    self._check_observation_matches_spec(obs, obs_specs[i])
                    actions.append(agent.step(time_step))

                time_steps = env.step(actions)

    def _check_observation_matches_spec(self, obs, obs_spec):
        assert set(obs_spec.keys()) == set(obs.keys())
        for k, o in obs.items():
            if k == "map_name":
                assert isinstance(o, str)
                continue

            descr = "%s: spec: %s != obs: %s" % (k, obs_spec[k], o.shape)

            if o.shape == (0,):  # Empty tensor can't have a shape.
                assert 0 in obs_spec[k], descr
            else:
                assert len(obs_spec[k]) == len(o.shape), descr
                for a, b in zip(obs_spec[k], o.shape):
                    if a != 0:
                        assert a == b, descr
