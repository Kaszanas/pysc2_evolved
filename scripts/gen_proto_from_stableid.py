#!/usr/bin/env python3
# Copyright 2024 pysc2_evolved contributors.
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
"""Sync unit/buff/upgrade IDs from stableid.json into proto, Python, and C++ files.

Downloads (or reads) stableid.json from s2client-proto and updates:
  - src/pysc2_evolved/env/converter/cc/game_data/proto/units.proto
  - src/pysc2_evolved/lib/units.py
  - src/pysc2_evolved/env/converter/cc/game_data/uint8_lookup.cc
      (new units appended to kUnitsList; array size constant updated)
  - src/pysc2_evolved/lib/static_data.py
      (new IDs appended to UNIT_TYPES, BUFFS, UPGRADES)
  - src/pysc2_evolved/env/converter/cc/game_data/proto/buffs.proto   (if new buffs)
  - src/pysc2_evolved/env/converter/cc/game_data/proto/upgrades.proto (if new upgrades)

Usage:
  python scripts/gen_proto_from_stableid.py [--stableid PATH] [--dry-run]
"""

import argparse
import json
import re
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

STABLEID_URL = (
    "https://raw.githubusercontent.com/Blizzard/s2client-proto/master/stableid.json"
)

REPO_ROOT = Path(__file__).resolve().parent.parent

UNITS_PROTO = (
    REPO_ROOT
    / "src/pysc2_evolved/env/converter/cc/game_data/proto/units.proto"
)
BUFFS_PROTO = (
    REPO_ROOT
    / "src/pysc2_evolved/env/converter/cc/game_data/proto/buffs.proto"
)
UPGRADES_PROTO = (
    REPO_ROOT
    / "src/pysc2_evolved/env/converter/cc/game_data/proto/upgrades.proto"
)
UNITS_PY = REPO_ROOT / "src/pysc2_evolved/lib/units.py"
UINT8_LOOKUP_CC = (
    REPO_ROOT
    / "src/pysc2_evolved/env/converter/cc/game_data/uint8_lookup.cc"
)
STATIC_DATA_PY = REPO_ROOT / "src/pysc2_evolved/lib/static_data.py"

RACES = ["Neutral", "Protoss", "Terran", "Zerg"]

# ---------------------------------------------------------------------------
# Non-melee unit filter
#
# stableid.json includes campaign, co-op, and debug units that should not be
# added to the melee lookup tables.  Any unit whose name contains one of the
# substrings below (or starts with one of the prefixes) is treated as
# non-melee and skipped.  Pass --include-all to disable this filter.
# ---------------------------------------------------------------------------

_NON_MELEE_SUBSTRINGS = [
    "Dummy",            # test / animation dummies
    "ACGluescreen",     # co-op glue-screen animations
    "ACGlue",           # same family
    "Placeholder",      # internal placeholders
    "CoOp",             # co-op specific
    "_Caverns_",        # XelNaga Caverns campaign level
    "TempleDoor",       # campaign doors
    "TemplePortal",     # campaign portals
    "Prison",           # campaign prison structures (XelNagaPrison*)
    "Fireworks",        # campaign event effects
    "RedstoneLava",     # campaign map (Outbreak)
    "StereoscopicOptions",  # debug unit
    "System_Snapshot",  # debug unit
    "WreckedBattlecruiser",  # campaign cinematic piece
    "LightBridge",      # campaign bridge prop
    "SILiberator",      # co-op Stukov liberator
    "Zagara",           # co-op commander units
    "Fenix",            # co-op commander units
    "Stukov",           # co-op commander units
    "Vorazun",          # co-op commander units
    "Karax",            # co-op commander units (NB: "Karak" prefix is OK, "Karax" is co-op)
    "Alarak",           # co-op commander units
    "Dehaka",           # co-op commander units
    "Abathur",          # co-op commander units
    "Artanis",          # co-op commander units
    "Swann",            # co-op commander units
    "Raynor",           # co-op commander units
    "Mengsk",           # co-op commander units
    "Horner",           # co-op commander units
    "Tychus",           # co-op commander units
    "HanAndHorner",     # co-op commander units
    "Kerrigan",         # co-op commander units (beyond standard GhostNova)
    "Missile",          # internal projectile entities (FungalGrowthMissile, etc.)
    "Tentacle",         # internal projectile/visual effects
    "PathingBlocker",   # internal pathing helpers
    "CreepBlocker",     # internal creep pathing
    "HelperEmitter",    # debug visual helper
    "MultiKill",        # achievement-tracking object
    "CommentatorBot",   # AI commentary helpers
    "RepulserField",    # campaign area-denial field
    "DefenseWall",      # campaign-specific fortification props
    "Campaign",         # explicit campaign-only units
    "SkinPreview",      # cosmetic skin preview units
    "Wreckage",         # destroyed unit cinematic props
    "LaserLines",       # GhostLaserLines — visual effect unit
    "Noodle",           # NukeNoodlesCommercial — campaign nuke effect
    "HiveMind",         # HiveMindEmulator — campaign only
    "SlotBag",          # campaign inventory bag items (4SlotBag, 10SlotBag, …)
    "GenerateCreep",    # internal creep-generation keybind dummy
    "Golfball",         # map editor test prop (ShapeGolfball)
    "TrafficSignal",    # city map decoration
    "Streetlight",      # city map decoration
    "SearchLight",      # city map decoration
    "Searchlight",      # city map decoration (alt capitalisation)
    "Bullhorn",         # city map decoration
    "SpacePlatformSign",    # space platform map decoration
    "SpacePlatformBarrier", # space platform map decoration
    "StoreFront",       # city map decoration
    "BillboardScroll",  # scrolling billboard prop
    "SignsDirection",   # directional sign prop
    "SignsConstruct",   # construction sign prop
    "SignsFunny",       # funny sign prop
    "SignsIcons",       # icon sign prop
    "SignsWarning",     # warning sign prop
    "Garage",           # city map prop (Destructible Garage)
    "WolfStatue",       # map deco prop
    "GlobeStatue",      # map deco prop
    "PurifierBlast",    # campaign visual effect
    "NagaHealingShrine",  # campaign shrine (XelNagaHealingShrine)
    "NagaShrine",       # campaign shrine
    "NagaTemple",       # campaign temple
    "NagaVault",        # campaign vault
    "NagaWorldship",    # campaign worldship
]

_NON_MELEE_PREFIXES = [
    "Item",             # campaign items (ItemGravityBombs, ItemMedkit, …)
    "Ball",             # the single test unit named exactly "Ball"
    "Beacon",           # army-command rally beacon helpers
    "Shape",            # geometry test shapes (ShapeGolfball, ShapeSphere, …)
    "AutoTest",         # automated test helpers
    "BraxisAlpha",      # Braxis Holdout map-specific destructibles
    "Ursadak",          # non-melee exotic critters
    "Karak",            # non-melee critters (KarakMale, etc.)
                        # Note: KarakFemale IS in proto but as a redundant-unit alias
]

# KarakFemale is a special case: it IS in units.proto (used as redundant-unit target),
# so it is kept via the existing-classification path and won't be re-added.
# New Karak variants (KarakMale, etc.) are filtered out by the "Karak" prefix above.

_NON_MELEE_SUFFIXES = [
    "Weapon",           # internal weapon/projectile entities
    "LMWeapon",         # LM-variant weapon projectiles
    "WeaponM2",         # multipart weapon projectiles
    "WeaponM3",
    "ReleaseMissile",   # larva / unit release projectiles
    "ReleaseWeapon",    # same family
    "Placement",        # build placement helpers (ReaperPlacement, …)
    "Keybind",          # internal keybind dummies
]

# Units whose exact names are non-melee singletons.
_NON_MELEE_EXACT = frozenset([
    "Ursadon",              # campaign critter
    "Sheep",                # decorative critter
    "Cow",                  # decorative critter
    "FungalGrowthMissile",  # covered by Missile substring, listed for clarity
])


def is_melee_candidate(name: str) -> bool:
    """Return True if a unit is likely to appear in standard melee play."""
    if name in _NON_MELEE_EXACT:
        return False
    for sub in _NON_MELEE_SUBSTRINGS:
        if sub in name:
            return False
    for prefix in _NON_MELEE_PREFIXES:
        if name == prefix or name.startswith(prefix):
            return False
    for suffix in _NON_MELEE_SUFFIXES:
        if name.endswith(suffix):
            return False
    return True


# Keywords that indicate a unit belongs to Neutral (terrain/resource/critter).
NEUTRAL_KEYWORDS = [
    "Mineral",
    "Vespene",
    "Geyser",
    "Destructible",
    "XelNaga",
    "Inhibitor",
    "Collapsible",
    "Debris",
    "Unbuildable",
    "LabBot",
    "BattleStation",
    "Purifier",
    "Shakuras",
    "SpacePlatform",
    "ReptileCrate",
    "Crabeetle",
    "CarrionBird",
    "UtilityBot",
    "KarakFemale",
    "Scantipede",
    "CleaningBot",
    "LabMineral",
    "RichMineral",
    "RichVespene",
]


# ---------------------------------------------------------------------------
# stableid.json loading
# ---------------------------------------------------------------------------


def fetch_stableid(path: Optional[Path]) -> dict:
    """Load stableid.json from a local file or the internet."""
    if path is not None:
        with open(path) as f:
            return json.load(f)
    print(f"Downloading stableid.json from {STABLEID_URL} ...")
    with urllib.request.urlopen(STABLEID_URL) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# Proto parsing helpers
# ---------------------------------------------------------------------------


def parse_units_proto(proto_path: Path) -> Dict[int, Tuple[str, str]]:
    """Return {id: (name, race)} from all enums in units.proto."""
    text = proto_path.read_text()
    result: Dict[int, Tuple[str, str]] = {}
    for race in RACES:
        pattern = rf"enum {race} \{{([^}}]*)\}}"
        m = re.search(pattern, text, re.DOTALL)
        if not m:
            continue
        for line in m.group(1).splitlines():
            line = line.strip().rstrip(";")
            if not line or line.startswith("//"):
                continue
            parts = line.split("=")
            if len(parts) != 2:
                continue
            name = parts[0].strip()
            val_str = parts[1].strip()
            if not val_str.lstrip("-").isdigit():
                continue
            val = int(val_str)
            if val == 0:
                continue  # skip Unknown* sentinel
            result[val] = (name, race)
    return result


def parse_single_enum(proto_path: Path, enum_name: str) -> Dict[int, str]:
    """Return {id: name} for one enum in a proto file (skips value 0)."""
    text = proto_path.read_text()
    pattern = rf"enum {enum_name} \{{([^}}]*)\}}"
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return {}
    result: Dict[int, str] = {}
    for line in m.group(1).splitlines():
        line = line.strip().rstrip(";")
        if not line or line.startswith("//"):
            continue
        parts = line.split("=")
        if len(parts) != 2:
            continue
        name = parts[0].strip()
        val_str = parts[1].strip()
        if not val_str.lstrip("-").isdigit():
            continue
        val = int(val_str)
        if val == 0:
            continue
        result[val] = name
    return result


# ---------------------------------------------------------------------------
# Race classification
# ---------------------------------------------------------------------------


def _build_known_names(existing: Dict[int, Tuple[str, str]]) -> Dict[str, str]:
    """Return {unit_name: race} from already-classified units."""
    return {name: race for name, race in existing.values()}


# Manual race overrides for units where heuristic classification fails.
# These are checked before the prefix scan to ensure correctness.
RACE_OVERRIDES: Dict[str, str] = {
    # SentryGun/SentryGunUnderground are Terran campaign turrets, not Protoss.
    # The prefix scan picks Protoss because 'Sentry' (6 chars) is a Protoss unit.
    "SentryGun": "Terran",
    "SentryGunUnderground": "Terran",
    # ThornLizard is a neutral critter, not Terran.
    # The prefix scan picks Terran because 'Thor' (4 chars) is a Terran unit.
    "ThornLizard": "Neutral",
    # Viking (id 1940) is a Terran unit variant.
    # The heuristic returns Neutral because VikingAssault/VikingFighter are longer
    # than 'Viking' so name.startswith(known) never fires.
    "Viking": "Terran",
}


def classify_unit(
    uid: int,
    name: str,
    existing: Dict[int, Tuple[str, str]],
    known_names: Dict[str, str],
) -> str:
    """Determine which race enum this unit belongs to.

    Priority:
      1. Already classified in units.proto  → keep existing race.
      2. Manual RACE_OVERRIDES entry        → use override.
      3. Exact name match in known_names    → use that race.
      4. Name starts with a known non-Neutral unit name (≥7 chars) → use that race.
         Minimum length of 7 prevents short names like 'Thor' (Terran) matching
         'ThornLizard', or 'Sentry' (Protoss) matching 'SentryGun'.
      5. Name contains a Neutral keyword    → Neutral.
      6. Default                            → Neutral.
    """
    if uid in existing:
        return existing[uid][1]
    if name in RACE_OVERRIDES:
        return RACE_OVERRIDES[name]
    if name in known_names:
        return known_names[name]
    # Prefix scan — longest match wins; only accept known_name of 7+ chars.
    best_match: Optional[Tuple[int, str]] = None
    for known_name, race in known_names.items():
        if race == "Neutral":
            continue
        if len(known_name) >= 7 and name.startswith(known_name):
            if best_match is None or len(known_name) > best_match[0]:
                best_match = (len(known_name), race)
    if best_match is not None:
        return best_match[1]
    for kw in NEUTRAL_KEYWORDS:
        if kw in name:
            return "Neutral"
    return "Neutral"


# ---------------------------------------------------------------------------
# kUnitsList parsing
# ---------------------------------------------------------------------------


def parse_kunits_list(cc_path: Path) -> List[Tuple[str, str]]:
    """Return ordered list of (race, name) from kUnitsList in uint8_lookup.cc."""
    text = cc_path.read_text()
    m = re.search(
        r"std::array<int,\s*\d+>\s*kUnitsList\s*=\s*\{\{(.*?)\}\};",
        text,
        re.DOTALL,
    )
    if not m:
        raise ValueError("Could not find kUnitsList in uint8_lookup.cc")
    entries: List[Tuple[str, str]] = []
    for line in m.group(1).splitlines():
        # Strip inline comments before any other processing.
        if "//" in line:
            line = line[: line.index("//")]
        line = line.strip().rstrip(",").strip()
        if not line:
            continue
        if "::" in line:
            race, name = line.split("::", 1)
            entries.append((race.strip(), name.strip()))
    return entries


def parse_redundant_keys(cc_path: Path) -> Set[Tuple[str, str]]:
    """Return (race, name) pairs that are *keys* in RedundantUnits().

    These units are already handled by remapping — they don't need their own
    slot in kUnitsList.
    """
    text = cc_path.read_text()
    m = re.search(
        r"RedundantUnits\(\).*?return \*redundant_units;",
        text,
        re.DOTALL,
    )
    if not m:
        return set()
    # Each entry looks like: {Race::Name, Race::OtherName},
    keys: Set[Tuple[str, str]] = set()
    for pair in re.findall(r"\{(\w+)::(\w+),\s*\w+::\w+\}", m.group(0)):
        keys.add((pair[0], pair[1]))
    return keys


# ---------------------------------------------------------------------------
# File updaters
# ---------------------------------------------------------------------------


def update_units_proto(
    proto_path: Path,
    classified: Dict[int, Tuple[str, str]],
    dry_run: bool,
) -> int:
    """Rewrite units.proto with classified units. Returns count of new entries.

    Only adds new units that are:
      1. Already present in the proto (always kept), OR
      2. A family member (≥10-char prefix match) of any existing proto entry, AND
      3. A melee candidate (passes is_melee_candidate).

    This mirrors the kUnitsList selection criterion and keeps the proto small —
    the original hand-curated proto has ~263 entries out of 1943 in stableid.json.
    """
    text = proto_path.read_text()

    # Collect ALL existing entries across all race enums for family membership check.
    all_existing_proto: List[Tuple[str, str]] = []  # (race, name)
    for race in RACES:
        pat = rf"enum {race} \{{([^}}]*)\}}"
        m0 = re.search(pat, text, re.DOTALL)
        if not m0:
            continue
        for line in m0.group(1).splitlines():
            line = line.strip().rstrip(";")
            if not line or line.startswith("//"):
                continue
            parts = line.split("=")
            if len(parts) == 2 and parts[1].strip().lstrip("-").isdigit():
                all_existing_proto.append((race, parts[0].strip()))

    by_race: Dict[str, Dict[int, str]] = {r: {} for r in RACES}
    for uid, (name, race) in classified.items():
        by_race[race][uid] = name

    new_text = text
    added = 0

    for race in RACES:
        pattern = rf"(enum {race} \{{)([^}}]*)(\}})"
        m = re.search(pattern, new_text, re.DOTALL)
        if not m:
            continue

        # Collect existing entries from this enum block.
        existing_in_enum: Dict[int, str] = {}
        for line in m.group(2).splitlines():
            line = line.strip().rstrip(";")
            if not line or line.startswith("//"):
                continue
            parts = line.split("=")
            if len(parts) != 2:
                continue
            ename = parts[0].strip()
            val_str = parts[1].strip()
            if not val_str.lstrip("-").isdigit():
                continue
            existing_in_enum[int(val_str)] = ename

        # Merge new entries: keep all existing; add new only if family member.
        merged: Dict[int, str] = {}
        used_in_race: Set[str] = set()
        for uid in sorted(existing_in_enum):
            name = existing_in_enum[uid]
            if not _is_valid_identifier(name) or name in used_in_race:
                continue
            merged[uid] = name
            used_in_race.add(name)

        for uid, name in by_race[race].items():
            # Skip digit-leading names (convention: append digits, e.g. SomeUnit8).
            if name and name[0].isdigit():
                continue
            if not _is_valid_identifier(name):
                continue
            if uid in merged or name in used_in_race:
                continue
            # Only add new units that are family members of existing proto entries
            # AND pass the melee-candidate filter.
            if not is_melee_candidate(name):
                continue
            if not _is_family_member(name, all_existing_proto, min_prefix=10):
                continue
            merged[uid] = name
            used_in_race.add(name)
            added += 1

        # Rebuild enum body: Unknown* sentinel first, rest sorted by value.
        unknown = f"Unknown{race}"
        lines = [f"  {unknown} = 0;"]
        for uid in sorted(k for k in merged if k != 0):
            lines.append(f"  {merged[uid]} = {uid};")
        enum_body = "\n".join(lines) + "\n"

        new_enum = m.group(1) + "\n" + enum_body + m.group(3)
        new_text = new_text[: m.start()] + new_enum + new_text[m.end() :]

    if not dry_run:
        proto_path.write_text(new_text)
    return added


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _is_valid_identifier(name: str) -> bool:
    """Return True if *name* is a valid C++/Python/proto identifier."""
    return bool(_IDENTIFIER_RE.match(name))


_DIGIT_PREFIX_RE = re.compile(r'^(\d+(?:mm)?)(.+)$')


def _safe_name(name: str) -> str:
    """Move a leading digit+unit prefix (e.g. '250mm', '330mm', '4') to the end.

    '250mmStrikeCannons' -> 'StrikeCannons250mm'
    '330mmBarrageCannons' -> 'BarrageCannons330mm'
    '4SlotBag' -> 'SlotBag4'
    Returns the original name unchanged if it already starts with a letter.
    """
    if not name or not name[0].isdigit():
        return name
    m = _DIGIT_PREFIX_RE.match(name)
    if m:
        return m.group(2) + m.group(1)
    return name


def _generate_units_py(classified: Dict[int, Tuple[str, str]], original: str) -> str:
    """Regenerate the four IntEnum classes in units.py."""
    # Build by_race sorted by uid so lower (original) IDs win on name conflicts.
    by_race: Dict[str, Dict[int, str]] = {r: {} for r in RACES}
    used_names: Dict[str, Set[str]] = {r: set() for r in RACES}  # race → set of names
    for uid, (name, race) in sorted(classified.items()):
        # Skip digit-leading names — they are not valid Python identifiers.
        # Convention if ever needed: append digits (e.g. SomeUnit8), but in
        # practice all such names are filtered by is_melee_candidate already.
        if name and name[0].isdigit():
            continue
        if not _is_valid_identifier(name):
            continue
        if name in used_names[race]:
            continue  # duplicate name — skip higher-uid variant
        by_race[race][uid] = name
        used_names[race].add(name)

    # Preserve everything up to the first class definition.
    header_end = re.search(r"^class \w+\(enum\.IntEnum\):", original, re.MULTILINE)
    header = original[: header_end.start()] if header_end else ""

    blocks = []
    for race in RACES:
        lines = [f"class {race}(enum.IntEnum):", f'    """{race} units."""', ""]
        # Sort alphabetically by name.
        for name in sorted(by_race[race].values()):
            uid = next(k for k, v in by_race[race].items() if v == name)
            lines.append(f"    {name} = {uid}")
        blocks.append("\n".join(lines))

    # Preserve the get_unit_type helper that follows the classes.
    helper_match = re.search(r"\ndef get_unit_type", original)
    helper = original[helper_match.start() :] if helper_match else ""

    return header + "\n\n".join(blocks) + "\n" + helper


def update_units_py(
    py_path: Path,
    classified: Dict[int, Tuple[str, str]],
    existing_classified: Dict[int, Tuple[str, str]],
    dry_run: bool,
) -> int:
    """Regenerate units.py. Returns count of new entries."""
    original = py_path.read_text()
    new_text = _generate_units_py(classified, original)
    added = len(classified) - len(existing_classified)
    if not dry_run:
        py_path.write_text(new_text)
    return max(added, 0)


def _is_family_member(name: str, existing_entries: List[Tuple[str, str]], min_prefix: int = 10) -> bool:
    """Return True if *name* shares >= *min_prefix* leading chars with any existing entry."""
    for _, ename in existing_entries:
        count = 0
        for a, b in zip(name, ename):
            if a != b:
                break
            count += 1
        if count >= min_prefix:
            return True
    return False


def update_uint8_lookup_cc(
    cc_path: Path,
    classified: Dict[int, Tuple[str, str]],
    dry_run: bool,
) -> int:
    """Append new units to kUnitsList in uint8_lookup.cc. Returns count added.

    Only units that are "siblings" of existing kUnitsList entries (sharing a
    10+ character name prefix) or that are race-classified (Protoss/Terran/Zerg)
    are added.  Pure Neutral units with no family match are skipped to keep the
    observation feature-vector size changes minimal.
    """
    text = cc_path.read_text()

    existing_entries = parse_kunits_list(cc_path)
    # Deduplicate while preserving order (first occurrence wins).
    # This corrects corruption from earlier script runs that re-added entries.
    _seen_entries: Set[Tuple[str, str]] = set()
    _deduped: List[Tuple[str, str]] = []
    for _entry in existing_entries:
        if _entry not in _seen_entries:
            _seen_entries.add(_entry)
            _deduped.append(_entry)
    existing_entries = _deduped

    existing_set: Set[Tuple[str, str]] = set(existing_entries)
    redundant_keys = parse_redundant_keys(cc_path)

    new_entries: List[Tuple[int, str, str]] = []
    for uid, (name, race) in sorted(classified.items()):
        key = (race, name)
        if key in existing_set or key in redundant_keys:
            continue
        # For race units always add; for Neutral require family membership.
        if race != "Neutral" or _is_family_member(name, existing_entries):
            new_entries.append((uid, name, race))

    if not new_entries:
        return 0

    new_size = len(existing_entries) + len(new_entries)

    # Build the replacement array body.
    all_lines = [f"    {race}::{name}," for race, name in existing_entries]
    for uid, name, race in new_entries:
        all_lines.append(f"    {race}::{name},  // {uid}")

    array_body = "\n".join(all_lines)
    new_array = (
        f"std::array<int, {new_size}> kUnitsList = {{{{\n"
        f"{array_body}\n"
        f"}}}};"
    )

    new_text = re.sub(
        r"std::array<int,\s*\d+>\s*kUnitsList\s*=\s*\{\{.*?\}\};",
        new_array,
        text,
        flags=re.DOTALL,
    )

    if not dry_run:
        cc_path.write_text(new_text)
    return len(new_entries)


def _update_list_in_py(text: str, list_name: str, new_ids: Set[int]) -> Tuple[str, int]:
    """Add *new_ids* to a Python integer list variable in *text*."""
    pattern = rf"({list_name}\s*=\s*\[)(.*?)(\])"
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return text, 0

    existing = {int(tok) for tok in re.findall(r"\d+", m.group(2))}
    added_ids = new_ids - existing
    if not added_ids:
        return text, 0

    all_ids = sorted(existing | added_ids)
    body = "".join(f"\n    {i}," for i in all_ids) + "\n"
    replacement = m.group(1) + body + m.group(3)
    return text[: m.start()] + replacement + text[m.end() :], len(added_ids)


def update_static_data_py(
    py_path: Path,
    unit_ids: Set[int],
    buff_ids: Set[int],
    upgrade_ids: Set[int],
    dry_run: bool,
) -> int:
    """Update UNIT_TYPES, BUFFS, UPGRADES in static_data.py."""
    text = py_path.read_text()
    total = 0
    text, n = _update_list_in_py(text, "UNIT_TYPES", unit_ids)
    total += n
    text, n = _update_list_in_py(text, "BUFFS", buff_ids)
    total += n
    text, n = _update_list_in_py(text, "UPGRADES", upgrade_ids)
    total += n
    if not dry_run:
        py_path.write_text(text)
    return total


def _rewrite_proto_enum(
    text: str,
    enum_name: str,
    all_entries: Dict[int, str],
    unknown_name: str,
) -> str:
    """Replace the body of *enum_name* in *text* with *all_entries* sorted by value."""
    pattern = rf"(enum {enum_name} \{{)([^}}]*)(\}})"
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return text
    lines = [f"  {unknown_name} = 0;"]
    for uid in sorted(k for k in all_entries if k != 0):
        lines.append(f"  {all_entries[uid]} = {uid};")
    enum_body = "\n".join(lines) + "\n"
    new_enum = m.group(1) + "\n" + enum_body + m.group(3)
    return text[: m.start()] + new_enum + text[m.end() :]


def update_buffs_proto(
    proto_path: Path,
    stableid_buffs: Dict[int, str],
    dry_run: bool,
) -> int:
    existing = parse_single_enum(proto_path, "Buffs")
    existing_names_lower = {n.lower() for n in existing.values()}
    new_entries = {}
    for uid, name in stableid_buffs.items():
        if uid in existing:
            continue
        name = _safe_name(name)
        if not _is_valid_identifier(name):
            continue
        if name.lower() in existing_names_lower:
            name = f"{name}{uid}"  # disambiguate: keep the ID, rename to avoid case conflict
        new_entries[uid] = name
        existing_names_lower.add(name.lower())
    if not new_entries:
        return 0
    merged = {**existing, **new_entries}
    text = proto_path.read_text()
    text = _rewrite_proto_enum(text, "Buffs", merged, "UnknownBuff")
    if not dry_run:
        proto_path.write_text(text)
    return len(new_entries)


def update_upgrades_proto(
    proto_path: Path,
    stableid_upgrades: Dict[int, str],
    dry_run: bool,
) -> int:
    existing = parse_single_enum(proto_path, "Upgrades")
    existing_names_lower = {n.lower() for n in existing.values()}
    new_entries = {}
    for uid, name in stableid_upgrades.items():
        if uid in existing:
            continue
        name = _safe_name(name)
        if not _is_valid_identifier(name):
            continue
        if name.lower() in existing_names_lower:
            name = f"{name}{uid}"  # disambiguate: keep the ID, rename to avoid case conflict
        existing_names_lower.add(name.lower())
        new_entries[uid] = name
    if not new_entries:
        return 0
    merged = {**existing, **new_entries}
    text = proto_path.read_text()
    # Upgrades enum has no Unknown* sentinel.
    pattern = rf"(enum Upgrades \{{)([^}}]*)(\}})"
    mm = re.search(pattern, text, re.DOTALL)
    if mm:
        lines = [f"  {merged[uid]} = {uid};" for uid in sorted(merged)]
        enum_body = "\n".join(lines) + "\n"
        text = text[: mm.start()] + mm.group(1) + "\n" + enum_body + mm.group(3) + text[mm.end() :]
    if not dry_run:
        proto_path.write_text(text)
    return len(new_entries)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stableid",
        type=Path,
        metavar="PATH",
        help="Path to a local stableid.json (default: download from GitHub)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report changes without writing any files",
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Disable the melee-unit filter and include all stableid units",
    )
    args = parser.parse_args()

    data = fetch_stableid(args.stableid)

    # Build ID→name maps from stableid.json (skip null/unknown entries).
    def _keep_unit(uid: int, name: str) -> bool:
        if uid == 0 or not name or name in ("NotAUnit", ""):
            return False
        if not args.include_all and not is_melee_candidate(name):
            return False
        return True

    stableid_units: Dict[int, str] = {
        u["id"]: u["name"]
        for u in data.get("Units", [])
        if _keep_unit(u["id"], u.get("name", ""))
    }
    stableid_buffs: Dict[int, str] = {
        b["id"]: b["name"]
        for b in data.get("Buffs", [])
        if b.get("name") and b["name"] not in ("Null", "") and b["id"] != 0
    }
    stableid_upgrades: Dict[int, str] = {
        u["id"]: u["name"]
        for u in data.get("Upgrades", [])
        if u.get("name") and u["name"] not in ("Null", "") and u["id"] != 0
    }

    print(
        f"stableid.json: {len(stableid_units)} units, "
        f"{len(stableid_buffs)} buffs, "
        f"{len(stableid_upgrades)} upgrades"
    )

    existing = parse_units_proto(UNITS_PROTO)
    print(f"Existing proto: {len(existing)} classified units across all races")

    known_names = _build_known_names(existing)

    # Build a set of all names already used in the proto to detect conflicts.
    existing_names: Set[str] = {name for name, _ in existing.values()}

    # Build a flat list of (race, name) tuples for the family-membership check.
    # This mirrors what update_units_proto uses internally.
    all_existing_proto: List[Tuple[str, str]] = [
        (race, name) for name, race in existing.values()
    ]

    # Classify every unit from stableid.json.
    # For units already in the proto, preserve their existing name and race —
    # stableid.json sometimes uses different internal names (e.g. "HellionTank"
    # vs the proto's "Hellbat").  Only truly new IDs get the stableid name.
    # Skip stableid units whose names would duplicate an existing enum member
    # (these are usually campaign/variant units sharing a name with a melee unit).
    # Also skip any unit that would not pass the family-membership filter in
    # update_units_proto, so that classified stays consistent with the proto.
    classified: Dict[int, Tuple[str, str]] = {}
    new_units: List[Tuple[int, str, str]] = []
    for uid, name in stableid_units.items():
        if uid in existing:
            classified[uid] = existing[uid]  # keep proto name + race
        else:
            if name in existing_names:
                # Duplicate name — skip to avoid proto/Python enum conflicts.
                continue
            if name and name[0].isdigit():
                continue  # skip digit-leading names
            # Only add units that are family members of existing proto entries.
            if not args.include_all and not _is_family_member(
                name, all_existing_proto, min_prefix=10
            ):
                continue
            race = classify_unit(uid, name, existing, known_names)
            classified[uid] = (name, race)
            new_units.append((uid, name, race))

    new_units.sort(key=lambda x: x[0])

    if new_units:
        print(f"\nNew units to add ({len(new_units)}):")
        for uid, name, race in new_units:
            print(f"  [{race}] {name} = {uid}")
    else:
        print("\nNo new units found.")

    existing_buffs = parse_single_enum(BUFFS_PROTO, "Buffs")
    new_buffs = {uid: name for uid, name in stableid_buffs.items() if uid not in existing_buffs}
    if new_buffs:
        print(f"\nNew buffs to add ({len(new_buffs)}):")
        for uid, name in sorted(new_buffs.items()):
            print(f"  {name} = {uid}")

    existing_upgrades = parse_single_enum(UPGRADES_PROTO, "Upgrades")
    new_upgrades = {
        uid: name for uid, name in stableid_upgrades.items() if uid not in existing_upgrades
    }
    if new_upgrades:
        print(f"\nNew upgrades to add ({len(new_upgrades)}):")
        for uid, name in sorted(new_upgrades.items()):
            print(f"  {name} = {uid}")

    # Determine which units would go into kUnitsList.
    existing_cc_entries = parse_kunits_list(UINT8_LOOKUP_CC)
    redundant_cc_keys = parse_redundant_keys(UINT8_LOOKUP_CC)
    existing_cc_set: Set[Tuple[str, str]] = set(existing_cc_entries)
    kulist_additions: List[Tuple[int, str, str]] = []
    for uid, (name, race) in sorted(classified.items()):
        key = (race, name)
        if key in existing_cc_set or key in redundant_cc_keys:
            continue
        if race != "Neutral" or _is_family_member(name, existing_cc_entries):
            kulist_additions.append((uid, name, race))

    if kulist_additions:
        print(f"\nkUnitsList additions ({len(kulist_additions)}):")
        for uid, name, race in kulist_additions:
            print(f"  {race}::{name}  // {uid}")
    else:
        print("\nNo kUnitsList additions needed.")

    if args.dry_run:
        print("\n[dry-run] No files written.")
        return

    n = update_units_proto(UNITS_PROTO, classified, dry_run=False)
    print(f"\nUpdated {UNITS_PROTO.name}: +{n} entries")

    n = update_units_py(UNITS_PY, classified, existing, dry_run=False)
    print(f"Updated {UNITS_PY.name}: +{n} entries")

    n = update_uint8_lookup_cc(UINT8_LOOKUP_CC, classified, dry_run=False)
    print(f"Updated uint8_lookup.cc kUnitsList: +{n} entries")

    kulist_unit_ids = {uid for uid, _, _ in kulist_additions}
    n = update_static_data_py(
        STATIC_DATA_PY,
        kulist_unit_ids,
        set(stableid_buffs.keys()),
        set(stableid_upgrades.keys()),
        dry_run=False,
    )
    print(f"Updated static_data.py: +{n} IDs")

    if new_buffs:
        n = update_buffs_proto(BUFFS_PROTO, stableid_buffs, dry_run=False)
        print(f"Updated {BUFFS_PROTO.name}: +{n} entries")

    if new_upgrades:
        n = update_upgrades_proto(UPGRADES_PROTO, stableid_upgrades, dry_run=False)
        print(f"Updated {UPGRADES_PROTO.name}: +{n} entries")

    print("\nDone. Next steps:")
    print("  make bazel_build_converter_local")
    print("  make bazel_test_converter_local")
    print("  python scripts/smoke_test_converter.py")


if __name__ == "__main__":
    main()
