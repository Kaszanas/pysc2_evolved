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

import collections
import datetime
import os
from typing import Any, Dict, Generator, List

from pysc2_evolved.lib import gfile, sc_process


class Version(
    collections.namedtuple(
        "Version", ["game_version", "build_version", "data_version", "binary"]
    )
):
    """Represents a single version of the game."""

    __slots__ = ()


def version_dict(versions: List[Version]) -> Dict[str, Version]:
    """
    Converts a list of Version objects into a dictionary keyed by the game version string.

    Parameters
    ----------
    versions : List[Version]
        A list of version objects to be converted into a dictionary.

    Returns
    -------
    Dict[str, Version]
        Dictionary where the keys are game version strings and the values are Version objects.
    """

    return {ver.game_version: ver for ver in versions}


# https://github.com/Blizzard/s2client-proto/blob/master/buildinfo/versions.json
# Generate with bin/gen_versions.py or bin/replay_version.py.
VERSIONS = version_dict(
    [
        Version(
            game_version="3.13.0",
            build_version=52910,
            data_version="8D9FEF2E1CF7C6C9CBE4FBCA830DDE1C",
            binary=None,
        ),
        Version(
            game_version="3.14.0",
            build_version=53644,
            data_version="CA275C4D6E213ED30F80BACCDFEDB1F5",
            binary=None,
        ),
        Version(
            game_version="3.15.0",
            build_version=54518,
            data_version="BBF619CCDCC80905350F34C2AF0AB4F6",
            binary=None,
        ),
        Version(
            game_version="3.15.1",
            build_version=54518,
            data_version="6EB25E687F8637457538F4B005950A5E",
            binary=None,
        ),
        Version(
            game_version="3.16.0",
            build_version=55505,
            data_version="60718A7CA50D0DF42987A30CF87BCB80",
            binary=None,
        ),
        Version(
            game_version="3.16.1",
            build_version=55958,
            data_version="5BD7C31B44525DAB46E64C4602A81DC2",
            binary=None,
        ),
        Version(
            game_version="3.17.0",
            build_version=56787,
            data_version="DFD1F6607F2CF19CB4E1C996B2563D9B",
            binary=None,
        ),
        Version(
            game_version="3.17.1",
            build_version=56787,
            data_version="3F2FCED08798D83B873B5543BEFA6C4B",
            binary=None,
        ),
        Version(
            game_version="3.17.2",
            build_version=56787,
            data_version="C690FC543082D35EA0AAA876B8362BEA",
            binary=None,
        ),
        Version(
            game_version="3.18.0",
            build_version=57507,
            data_version="1659EF34997DA3470FF84A14431E3A86",
            binary=None,
        ),
        Version(
            game_version="3.19.0",
            build_version=58400,
            data_version="2B06AEE58017A7DF2A3D452D733F1019",
            binary=None,
        ),
        Version(
            game_version="3.19.1",
            build_version=58400,
            data_version="D9B568472880CC4719D1B698C0D86984",
            binary=None,
        ),
        Version(
            game_version="4.0.0",
            build_version=59587,
            data_version="9B4FD995C61664831192B7DA46F8C1A1",
            binary=None,
        ),
        Version(
            game_version="4.0.2",
            build_version=59587,
            data_version="B43D9EE00A363DAFAD46914E3E4AF362",
            binary=None,
        ),
        Version(
            game_version="4.1.0",
            build_version=60196,
            data_version="1B8ACAB0C663D5510941A9871B3E9FBE",
            binary=None,
        ),
        Version(
            game_version="4.1.1",
            build_version=60321,
            data_version="5C021D8A549F4A776EE9E9C1748FFBBC",
            binary=None,
        ),
        Version(
            game_version="4.1.2",
            build_version=60321,
            data_version="33D9FE28909573253B7FC352CE7AEA40",
            binary=None,
        ),
        Version(
            game_version="4.1.3",
            build_version=60321,
            data_version="F486693E00B2CD305B39E0AB254623EB",
            binary=None,
        ),
        Version(
            game_version="4.1.4",
            build_version=60321,
            data_version="2E2A3F6E0BAFE5AC659C4D39F13A938C",
            binary=None,
        ),
        Version(
            game_version="4.2.0",
            build_version=62347,
            data_version="C0C0E9D37FCDBC437CE386C6BE2D1F93",
            binary=None,
        ),
        Version(
            game_version="4.2.1",
            build_version=62848,
            data_version="29BBAC5AFF364B6101B661DB468E3A37",
            binary=None,
        ),
        Version(
            game_version="4.2.2",
            build_version=63454,
            data_version="3CB54C86777E78557C984AB1CF3494A0",
            binary=None,
        ),
        Version(
            game_version="4.2.3",
            build_version=63454,
            data_version="5E3A8B21E41B987E05EE4917AAD68C69",
            binary=None,
        ),
        Version(
            game_version="4.2.4",
            build_version=63454,
            data_version="7C51BC7B0841EACD3535E6FA6FF2116B",
            binary=None,
        ),
        Version(
            game_version="4.3.0",
            build_version=64469,
            data_version="C92B3E9683D5A59E08FC011F4BE167FF",
            binary=None,
        ),
        Version(
            game_version="4.3.1",
            build_version=65094,
            data_version="E5A21037AA7A25C03AC441515F4E0644",
            binary=None,
        ),
        Version(
            game_version="4.3.2",
            build_version=65384,
            data_version="B6D73C85DFB70F5D01DEABB2517BF11C",
            binary=None,
        ),
        Version(
            game_version="4.4.0",
            build_version=65895,
            data_version="BF41339C22AE2EDEBEEADC8C75028F7D",
            binary=None,
        ),
        Version(
            game_version="4.4.1",
            build_version=66668,
            data_version="C094081D274A39219061182DBFD7840F",
            binary=None,
        ),
        Version(
            game_version="4.5.0",
            build_version=67188,
            data_version="2ACF84A7ECBB536F51FC3F734EC3019F",
            binary=None,
        ),
        Version(
            game_version="4.5.1",
            build_version=67188,
            data_version="6D239173B8712461E6A7C644A5539369",
            binary=None,
        ),
        Version(
            game_version="4.6.0",
            build_version=67926,
            data_version="7DE59231CBF06F1ECE9A25A27964D4AE",
            binary=None,
        ),
        Version(
            game_version="4.6.1",
            build_version=67926,
            data_version="BEA99B4A8E7B41E62ADC06D194801BAB",
            binary=None,
        ),
        Version(
            game_version="4.6.2",
            build_version=69232,
            data_version="B3E14058F1083913B80C20993AC965DB",
            binary=None,
        ),
        Version(
            game_version="4.7.0",
            build_version=70154,
            data_version="8E216E34BC61ABDE16A59A672ACB0F3B",
            binary=None,
        ),
        Version(
            game_version="4.7.1",
            build_version=70154,
            data_version="94596A85191583AD2EBFAE28C5D532DB",
            binary=None,
        ),
        Version(
            game_version="4.8.0",
            build_version=71061,
            data_version="760581629FC458A1937A05ED8388725B",
            binary=None,
        ),
        Version(
            game_version="4.8.1",
            build_version=71523,
            data_version="FCAF3F050B7C0CC7ADCF551B61B9B91E",
            binary=None,
        ),
        Version(
            game_version="4.8.2",
            build_version=71663,
            data_version="FE90C92716FC6F8F04B74268EC369FA5",
            binary=None,
        ),
        Version(
            game_version="4.8.3",
            build_version=72282,
            data_version="0F14399BBD0BA528355FF4A8211F845B",
            binary=None,
        ),
        Version(
            game_version="4.8.4",
            build_version=73286,
            data_version="CD040C0675FD986ED37A4CA3C88C8EB5",
            binary=None,
        ),
        Version(
            game_version="4.8.5",
            build_version=73559,
            data_version="B2465E73AED597C74D0844112D582595",
            binary=None,
        ),
        Version(
            game_version="4.8.6",
            build_version=73620,
            data_version="AA18FEAD6573C79EF707DF44ABF1BE61",
            binary=None,
        ),
        Version(
            game_version="4.9.0",
            build_version=74071,
            data_version="70C74A2DCA8A0D8E7AE8647CAC68ACCA",
            binary=None,
        ),
        Version(
            game_version="4.9.1",
            build_version=74456,
            data_version="218CB2271D4E2FA083470D30B1A05F02",
            binary=None,
        ),
        Version(
            game_version="4.9.2",
            build_version=74741,
            data_version="614480EF79264B5BD084E57F912172FF",
            binary=None,
        ),
        Version(
            game_version="4.9.3",
            build_version=75025,
            data_version="C305368C63621480462F8F516FB64374",
            binary=None,
        ),
        Version(
            game_version="4.10.0",
            build_version=75689,
            data_version="B89B5D6FA7CBF6452E721311BFBC6CB2",
            binary=None,
        ),
        Version(
            game_version="4.10.1",
            build_version=75800,
            data_version="DDFFF9EC4A171459A4F371C6CC189554",
            binary=None,
        ),
        Version(
            game_version="4.10.2",
            build_version=76052,
            data_version="D0F1A68AA88BA90369A84CD1439AA1C3",
            binary=None,
        ),
        Version(
            game_version="4.10.3",
            build_version=76114,
            data_version="CDB276D311F707C29BA664B7754A7293",
            binary=None,
        ),
        Version(
            game_version="4.10.4",
            build_version=76811,
            data_version="FF9FA4EACEC5F06DEB27BD297D73ED67",
            binary=None,
        ),
        Version(
            game_version="4.11.0",
            build_version=77379,
            data_version="70E774E722A58287EF37D487605CD384",
            binary=None,
        ),
        Version(
            game_version="4.11.1",
            build_version=77379,
            data_version="F92D1127A291722120AC816F09B2E583",
            binary=None,
        ),
        Version(
            game_version="4.11.2",
            build_version=77535,
            data_version="FC43E0897FCC93E4632AC57CBC5A2137",
            binary=None,
        ),
        Version(
            game_version="4.11.3",
            build_version=77661,
            data_version="A15B8E4247434B020086354F39856C51",
            binary=None,
        ),
        Version(
            game_version="4.11.4",
            build_version=78285,
            data_version="69493AFAB5C7B45DDB2F3442FD60F0CF",
            binary=None,
        ),
        Version(
            game_version="4.12.0",
            build_version=79998,
            data_version="B47567DEE5DC23373BFF57194538DFD3",
            binary=None,
        ),
        Version(
            game_version="4.12.1",
            build_version=80188,
            data_version="44DED5AED024D23177C742FC227C615A",
            binary=None,
        ),
        Version(
            game_version="5.0.0",
            build_version=80949,
            data_version="9AE39C332883B8BF6AA190286183ED72",
            binary=None,
        ),
        Version(
            game_version="5.0.1",
            build_version=81009,
            data_version="0D28678BC32E7F67A238F19CD3E0A2CE",
            binary=None,
        ),
        Version(
            game_version="5.0.2",
            build_version=81102,
            data_version="DC0A1182FB4ABBE8E29E3EC13CF46F68",
            binary=None,
        ),
        Version(
            game_version="5.0.3",
            build_version=81433,
            data_version="5FD8D4B6B52723B44862DF29F232CF31",
            binary=None,
        ),
        Version(
            game_version="5.0.4",
            build_version=82457,
            data_version="D2707E265785612D12B381AF6ED9DBF4",
            binary=None,
        ),
        Version(
            game_version="5.0.5",
            build_version=82893,
            data_version="D795328C01B8A711947CC62AA9750445",
            binary=None,
        ),
        Version(
            game_version="5.0.6",
            build_version=83830,
            data_version="B4745D6A4F982A3143C183D8ACB6C3E3",
            binary=None,
        ),
        Version(
            game_version="5.0.7",
            build_version=84643,
            data_version="A389D1F7DF9DD792FBE980533B7119FF",
            binary=None,
        ),
        Version(
            game_version="5.0.8",
            build_version=86383,
            data_version="22EAC562CD0C6A31FB2C2C21E3AA3680",
            binary=None,
        ),
        Version(
            game_version="5.0.9",
            build_version=87702,
            data_version="F799E093428D419FD634CCE9B925218C",
            binary=None,
        ),
        Version(
            game_version="5.0.10",
            build_version=88500,
            data_version="F38043A301B034A78AD13F558257DCF8",
            binary=None,
        ),
        Version(
            game_version="5.0.11",
            build_version=90136,
            data_version="207F9DD45D02C9E6D19F868E0239E72D",
            binary=None,
        ),
        # REVIEW: This game engine version is missing from the CASC Viewer:
        # Version(
        #     game_version="5.0.12",
        #     build_version=91115,
        #     data_version="7857A76754FEB47C823D18993C476BF0",
        #     binary=None,
        # ),
        # REVIEW: This game engine version is missing from the CASC Viewer:
        # REVIEW: Blizzard botched their update system, these game versions
        # REVIEW: were removed from local storage.
        # Version(
        #     game_version="5.0.13",
        #     build_version=92440,
        #     data_version="79F6D78E27ED069D2D84FB14288B88B9",
        #     binary=None,
        # ),
        Version(
            game_version="5.0.14",
            build_version=93272,
            data_version="52920A9D89C7F63235945D10F3C73C64",
            binary=None,
        ),
    ]
)


class RunConfig(object):
    """Base class for different run configs."""

    def __init__(
        self,
        replay_dir: str,
        data_dir: str,
        tmp_dir: str,
        version: Version | str,
        cwd=None,
        env=None,
    ):
        """
        Initialize the runconfig with the various directories needed.

        Args:
          replay_dir: Where to find replays. Might not be accessible to SC2.
          data_dir: Where SC2 should find the data and battle.net cache.
          tmp_dir: The temporary directory. None is system default.
          version: The game version to run, a string.
          cwd: Where to set the current working directory.
          env: What to pass as the environment variables.
        """
        self.replay_dir = replay_dir
        self.data_dir = data_dir
        self.tmp_dir = tmp_dir
        self.cwd = cwd
        self.env = env
        self.version = self._get_version(version)

    def map_data(self, map_name: str, players: int | None = None) -> bytes:
        """Return the map data for a map by name or path."""
        map_names = [map_name]
        if players:
            map_names.append(
                os.path.join(
                    os.path.dirname(map_name),
                    "(%s)%s" % (players, os.path.basename(map_name)),
                )
            )
        for name in map_names:
            path = os.path.join(self.data_dir, "Maps", name)
            if gfile.Exists(path):
                with gfile.Open(path, "rb") as f:
                    return f.read()
        raise ValueError(f"Map {map_name} not found in {self.data_dir}/Maps.")

    def abs_replay_path(self, replay_path: str) -> str:
        """Return the absolute path to the replay, outside the sandbox."""

        # return os.path.join(self.replay_dir, replay_path)
        abs_replay_path = os.path.abspath(replay_path)
        return abs_replay_path

    def replay_data(self, replay_path: str) -> bytes:
        """Return the replay data given a path to the replay."""
        with gfile.Open(self.abs_replay_path(replay_path), "rb") as f:
            return f.read()

    def replay_paths(self, replay_dir: str) -> Generator[str, Any, None]:
        """A generator yielding the full path to the replays under `replay_dir`."""
        replay_dir = self.abs_replay_path(replay_dir)
        if replay_dir.lower().endswith(".sc2replay"):
            yield replay_dir
            return
        for f in gfile.ListDir(replay_dir):
            if f.lower().endswith(".sc2replay"):
                yield os.path.join(replay_dir, f)

    # REVIEW: Make sure that replay_data is bytes and not something else.
    def save_replay(
        self,
        replay_data: bytes,
        replay_dir: str,
        prefix: str | None = None,
    ) -> str:
        """Save a replay to a directory, returning the path to the replay.

        Args:
          replay_data: The result of controller.save_replay(), ie the binary data.
          replay_dir: Where to save the replay. This can be absolute or relative.
          prefix: Optional prefix for the replay filename.

        Returns:
          The full path where the replay is saved.

        Raises:
          ValueError: If the prefix contains the path seperator.
        """
        if not prefix:
            replay_filename = ""
        elif os.path.sep in prefix:
            raise ValueError(
                "Prefix '%s' contains '%s', use replay_dir instead."
                % (prefix, os.path.sep)
            )
        else:
            replay_filename = prefix + "_"
        now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
        replay_filename += "%s.SC2Replay" % now.isoformat("-").replace(":", "-")
        replay_dir = self.abs_replay_path(replay_dir)
        if not gfile.Exists(replay_dir):
            gfile.MakeDirs(replay_dir)
        replay_path = os.path.join(replay_dir, replay_filename)
        with gfile.Open(replay_path, "wb") as f:
            f.write(replay_data)
        return replay_path

    # REVIEW: version seems to be unused in all of the child classes that implement this:
    def start(self, version=None, **kwargs) -> "sc_process.StarcraftProcess":
        """Launch the game. Find the version and run sc_process.StarcraftProcess."""
        raise NotImplementedError()

    @classmethod
    def all_subclasses(cls):
        """An iterator over all subclasses of `cls`."""
        for s in cls.__subclasses__():
            yield s
            for c in s.all_subclasses():
                yield c

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    @classmethod
    def priority(cls) -> int | None:
        """None means this isn't valid. Run the one with the max priority."""
        return None

    def get_versions(self, containing: str | None = None) -> Dict[str, Version]:
        """Return a dict of all versions that can be run."""
        if containing is not None and containing not in VERSIONS:
            raise ValueError(
                f"Unknown game version: {containing}. Known versions: {sorted(VERSIONS.keys())}"
            )
        return VERSIONS

    def _get_version(self, game_version: Version | str) -> Version:
        """Get the full details for the specified game version."""
        if isinstance(game_version, Version):
            if not game_version.game_version:
                raise ValueError(
                    "Version '%r' supplied without a game version." % (game_version,)
                )
            if (
                game_version.data_version
                and game_version.binary
                and game_version.build_version
            ):
                return game_version
            # Some fields might be missing from serialized versions. Look them up.
            game_version = game_version.game_version
        if game_version.count(".") == 1:
            game_version += ".0"
        versions = self.get_versions(containing=game_version)
        return versions[game_version]
