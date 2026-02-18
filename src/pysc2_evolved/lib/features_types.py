import enum


class FeatureType(enum.Enum):
    SCALAR = 1
    CATEGORICAL = 2


class PlayerRelative(enum.IntEnum):
    """The values for the `player_relative` feature layers."""

    NONE = 0
    SELF = 1
    ALLY = 2
    NEUTRAL = 3
    ENEMY = 4


class Visibility(enum.IntEnum):
    """Values for the `visibility` feature layers."""

    HIDDEN = 0
    SEEN = 1
    VISIBLE = 2


class Effects(enum.IntEnum):
    """Values for the `effects` feature layer."""

    # pylint: disable=invalid-name
    none = 0
    PsiStorm = 1
    GuardianShield = 2
    TemporalFieldGrowing = 3
    TemporalField = 4
    ThermalLance = 5
    ScannerSweep = 6
    NukeDot = 7
    LiberatorDefenderZoneSetup = 8
    LiberatorDefenderZone = 9
    BlindingCloud = 10
    CorrosiveBile = 11
    LurkerSpines = 12
    # pylint: enable=invalid-name


class ScoreCumulative(enum.IntEnum):
    """Indices into the `score_cumulative` observation."""

    score = 0
    idle_production_time = 1
    idle_worker_time = 2
    total_value_units = 3
    total_value_structures = 4
    killed_value_units = 5
    killed_value_structures = 6
    collected_minerals = 7
    collected_vespene = 8
    collection_rate_minerals = 9
    collection_rate_vespene = 10
    spent_minerals = 11
    spent_vespene = 12


class ScoreByCategory(enum.IntEnum):
    """Indices for the `score_by_category` observation's first dimension."""

    food_used = 0
    killed_minerals = 1
    killed_vespene = 2
    lost_minerals = 3
    lost_vespene = 4
    friendly_fire_minerals = 5
    friendly_fire_vespene = 6
    used_minerals = 7
    used_vespene = 8
    total_used_minerals = 9
    total_used_vespene = 10


class ScoreCategories(enum.IntEnum):
    """Indices for the `score_by_category` observation's second dimension."""

    none = 0
    army = 1
    economy = 2
    technology = 3
    upgrade = 4


class ScoreByVital(enum.IntEnum):
    """Indices for the `score_by_vital` observation's first dimension."""

    total_damage_dealt = 0
    total_damage_taken = 1
    total_healed = 2


class ScoreVitals(enum.IntEnum):
    """Indices for the `score_by_vital` observation's second dimension."""

    life = 0
    shields = 1
    energy = 2


class Player(enum.IntEnum):
    """Indices into the `player` observation."""

    player_id = 0
    minerals = 1
    vespene = 2
    food_used = 3
    food_cap = 4
    food_army = 5
    food_workers = 6
    idle_worker_count = 7
    army_count = 8
    warp_gate_count = 9
    larva_count = 10


class UnitLayer(enum.IntEnum):
    """Indices into the unit layers in the observations."""

    unit_type = 0
    player_relative = 1
    health = 2
    shields = 3
    energy = 4
    transport_slots_taken = 5
    build_progress = 6


class UnitCounts(enum.IntEnum):
    """Indices into the `unit_counts` observations."""

    unit_type = 0
    count = 1


class FeatureUnit(enum.IntEnum):
    """Indices for the `feature_unit` observations."""

    unit_type = 0
    alliance = 1
    health = 2
    shield = 3
    energy = 4
    cargo_space_taken = 5
    build_progress = 6
    health_ratio = 7
    shield_ratio = 8
    energy_ratio = 9
    display_type = 10
    owner = 11
    x = 12
    y = 13
    facing = 14
    radius = 15
    cloak = 16
    is_selected = 17
    is_blip = 18
    is_powered = 19
    mineral_contents = 20
    vespene_contents = 21
    cargo_space_max = 22
    assigned_harvesters = 23
    ideal_harvesters = 24
    weapon_cooldown = 25
    order_length = 26  # If zero, the unit is idle.
    order_id_0 = 27
    order_id_1 = 28
    tag = 29  # Unique identifier for a unit (only populated for raw units).
    hallucination = 30
    buff_id_0 = 31
    buff_id_1 = 32
    addon_unit_type = 33
    active = 34
    is_on_screen = 35
    order_progress_0 = 36
    order_progress_1 = 37
    order_id_2 = 38
    order_id_3 = 39
    is_in_cargo = 40
    buff_duration_remain = 41
    buff_duration_max = 42
    attack_upgrade_level = 43
    armor_upgrade_level = 44
    shield_upgrade_level = 45


class EffectPos(enum.IntEnum):
    """Positions of the active effects."""

    effect = 0
    alliance = 1
    owner = 2
    radius = 3
    x = 4
    y = 5


class Radar(enum.IntEnum):
    """Positions of the Sensor towers."""

    x = 0
    y = 1
    radius = 2


class ProductionQueue(enum.IntEnum):
    """Indices for the `production_queue` observations."""

    ability_id = 0
    build_progress = 1


class Passthrough:
    """Alternative to `Features` which passes actions and observations through."""

    def observation_spec(self):
        return {}

    def transform_obs(self, observation):
        return observation

    def action_spec(self):
        return {}

    def transform_action(self, observation, action, skip_available):
        del observation
        del skip_available
        return action

    def available_actions(self, observation):
        del observation
        raise NotImplementedError("available_actions isn't supported for passthrough")

    def reverse_action(self, action):
        del action
        raise NotImplementedError("reverse_action isn't supported for passthrough")
