// Copyright 2021 DeepMind Technologies Ltd. All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS-IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "pysc2_evolved/env/converter/cc/game_data/uint8_lookup.h"

#include <algorithm>
#include <array>
#include <cstdint>
#include <vector>

#include "glog/logging.h"
#include "absl/container/flat_hash_map.h"
#include "pysc2_evolved/env/converter/cc/game_data/proto/buffs.pb.h"
#include "pysc2_evolved/env/converter/cc/game_data/proto/units.pb.h"
#include "pysc2_evolved/env/converter/cc/game_data/proto/upgrades.pb.h"

namespace pysc2_evolved {
namespace {

// Data taken from uint8_unit_lookup.UNIT_LIST.
std::array<int, 367> kUnitsList = {{
    Protoss::Colossus,
    Terran::TechLab,
    Terran::Reactor,
    Zerg::InfestedTerran,
    Zerg::BanelingCocoon,
    Zerg::Baneling,
    Protoss::Mothership,
    Terran::PointDefenseDrone,
    Zerg::Changeling,
    Zerg::ChangelingZealot,
    Zerg::ChangelingMarineShield,
    Zerg::ChangelingMarine,
    Zerg::ChangelingZerglingWings,
    Zerg::ChangelingZergling,
    Terran::CommandCenter,
    Terran::SupplyDepot,
    Terran::Refinery,
    Terran::Barracks,
    Terran::EngineeringBay,
    Terran::MissileTurret,
    Terran::Bunker,
    Terran::SensorTower,
    Terran::GhostAcademy,
    Terran::Factory,
    Terran::Starport,
    Terran::Armory,
    Terran::FusionCore,
    Terran::AutoTurret,
    Terran::SiegeTankSieged,
    Terran::SiegeTank,
    Terran::VikingAssault,
    Terran::VikingFighter,
    Terran::CommandCenterFlying,
    Terran::BarracksTechLab,
    Terran::BarracksReactor,
    Terran::FactoryTechLab,
    Terran::FactoryReactor,
    Terran::StarportTechLab,
    Terran::StarportReactor,
    Terran::FactoryFlying,
    Terran::StarportFlying,
    Terran::SCV,
    Terran::BarracksFlying,
    Terran::SupplyDepotLowered,
    Terran::Marine,
    Terran::Reaper,
    Terran::Ghost,
    Terran::Marauder,
    Terran::Thor,
    Terran::Hellion,
    Terran::Medivac,
    Terran::Banshee,
    Terran::Raven,
    Terran::Battlecruiser,
    Terran::Nuke,
    Protoss::Nexus,
    Protoss::Pylon,
    Protoss::Assimilator,
    Protoss::Gateway,
    Protoss::Forge,
    Protoss::FleetBeacon,
    Protoss::TwilightCouncil,
    Protoss::PhotonCannon,
    Protoss::Stargate,
    Protoss::TemplarArchive,
    Protoss::DarkShrine,
    Protoss::RoboticsBay,
    Protoss::RoboticsFacility,
    Protoss::CyberneticsCore,
    Protoss::Zealot,
    Protoss::Stalker,
    Protoss::HighTemplar,
    Protoss::DarkTemplar,
    Protoss::Sentry,
    Protoss::Phoenix,
    Protoss::Carrier,
    Protoss::VoidRay,
    Protoss::WarpPrism,
    Protoss::Observer,
    Protoss::Immortal,
    Protoss::Probe,
    Protoss::Interceptor,
    Zerg::Hatchery,
    Zerg::CreepTumor,
    Zerg::Extractor,
    Zerg::SpawningPool,
    Zerg::EvolutionChamber,
    Zerg::HydraliskDen,
    Zerg::Spire,
    Zerg::UltraliskCavern,
    Zerg::InfestationPit,
    Zerg::NydusNetwork,
    Zerg::BanelingNest,
    Zerg::RoachWarren,
    Zerg::SpineCrawler,
    Zerg::SporeCrawler,
    Zerg::Lair,
    Zerg::Hive,
    Zerg::GreaterSpire,
    Zerg::Cocoon,
    Zerg::Drone,
    Zerg::Zergling,
    Zerg::Overlord,
    Zerg::Hydralisk,
    Zerg::Mutalisk,
    Zerg::Ultralisk,
    Zerg::Roach,
    Zerg::Infestor,
    Zerg::Corruptor,
    Zerg::BroodLordCocoon,
    Zerg::BroodLord,
    Zerg::BanelingBurrowed,
    Zerg::DroneBurrowed,
    Zerg::HydraliskBurrowed,
    Zerg::RoachBurrowed,
    Zerg::ZerglingBurrowed,
    Zerg::InfestedTerranBurrowed,
    Zerg::QueenBurrowed,
    Zerg::Queen,
    Zerg::InfestorBurrowed,
    Zerg::OverseerCocoon,
    Zerg::Overseer,
    Terran::PlanetaryFortress,
    Zerg::UltraliskBurrowed,
    Terran::OrbitalCommand,
    Protoss::WarpGate,
    Terran::OrbitalCommandFlying,
    Protoss::ForceField,
    Protoss::WarpPrismPhasing,
    Zerg::CreepTumorBurrowed,
    Zerg::CreepTumorQueen,
    Zerg::SpineCrawlerUprooted,
    Zerg::SporeCrawlerUprooted,
    Protoss::Archon,
    Zerg::NydusCanal,
    Zerg::BroodlingEscort,
    Neutral::RichMineralField,
    Neutral::RichMineralField750,
    Neutral::XelNagaTower,
    Zerg::InfestedTerranCocoon,
    Zerg::Larva,
    Terran::MULE,
    Zerg::Broodling,
    Protoss::Adept,
    Neutral::KarakFemale,
    Neutral::UtilityBot,
    Neutral::Scantipede,
    Neutral::MineralField,
    Neutral::VespeneGeyser,
    Neutral::SpacePlatformGeyser,
    Neutral::RichVespeneGeyser,
    Neutral::DestructibleDebris6x6,
    Neutral::DestructibleRock6x6,
    Neutral::DestructibleDebrisRampDiagonalHugeULBR,
    Neutral::DestructibleDebrisRampDiagonalHugeBLUR,
    Neutral::UnbuildableBricksDestructible,
    Neutral::UnbuildablePlatesDestructible,
    Neutral::MineralField750,
    Terran::Hellbat,
    Neutral::CollapsibleTerranTowerDebris,
    Neutral::DebrisRampLeft,
    Neutral::DebrisRampRight,
    Protoss::MothershipCore,
    Zerg::Locust,
    Neutral::CollapsibleRockTowerDebris,
    Zerg::SwarmHostBurrowed,
    Zerg::SwarmHost,
    Protoss::Oracle,
    Protoss::Tempest,
    Terran::WidowMine,
    Zerg::Viper,
    Terran::WidowMineBurrowed,
    Zerg::LurkerCocoon,
    Zerg::Lurker,
    Zerg::LurkerBurrowed,
    Zerg::LurkerDen,
    Neutral::CollapsibleTerranTowerPushUnitRampLeft,
    Neutral::CollapsibleTerranTowerPushUnitRampRight,
    Neutral::CollapsibleRockTowerPushUnit,
    Neutral::CollapsibleTerranTowerPushUnit,
    Neutral::CollapsibleRockTowerDiagonal,
    Neutral::CollapsibleTerranTowerDiagonal,
    Neutral::CollapsibleTerranTowerRampLeft,
    Neutral::CollapsibleTerranTowerRampRight,
    Neutral::ProtossVespeneGeyser,
    Neutral::DestructibleRockEx1DiagonalHugeBLUR,
    Neutral::LabMineralField,
    Neutral::LabMineralField750,
    Zerg::RavagerCocoon,
    Zerg::Ravager,
    Terran::Liberator,
    Zerg::RavagerBurrowed,
    Terran::ThorHighImpactMode,
    Terran::Cyclone,
    Zerg::LocustFlying,
    Protoss::Disruptor,
    Protoss::StasisTrap,
    Protoss::DisruptorPhased,
    Terran::LiberatorAG,
    Neutral::PurifierRichMineralField,
    Neutral::PurifierRichMineralField750,
    Protoss::AdeptPhaseShift,
    Zerg::ParasiticBombDummy,
    Terran::KD8Charge,
    Neutral::BattleStationMineralField,
    Neutral::BattleStationMineralField750,
    Neutral::PurifierVespeneGeyser,
    Neutral::ShakurasVespeneGeyser,
    Neutral::PurifierMineralField,
    Neutral::PurifierMineralField750,
    Zerg::OverlordTransportCocoon,
    Zerg::OverlordTransport,
    Protoss::PylonOvercharged,
    Protoss::ShieldBattery,
    Protoss::ObserverSurveillanceMode,
    Zerg::OverseerOversightMode,
    Terran::RepairDrone,
    Terran::GhostAlternate,
    Terran::GhostNova,
    Neutral::UnbuildableRocksDestructible,
    Neutral::CollapsibleRockTowerDebrisRampRight,
    Neutral::CollapsibleRockTowerDebrisRampLeft,
    Neutral::CollapsibleRockTowerPushUnitRampRight,
    Neutral::CollapsibleRockTowerPushUnitRampLeft,
    Neutral::DestructibleCityDebrisHugeDiagonalBLUR,
    Neutral::DestructibleRockEx14x4,
    Neutral::DestructibleRockEx16x6,
    Neutral::LabBot,
    Neutral::CollapsibleRockTowerRampRight,
    Neutral::CollapsibleRockTowerRampLeft,
    Neutral::XelNagaDestructibleBlocker8NE,
    Neutral::XelNagaDestructibleBlocker8SW,
    Neutral::CarrionBird,
    Neutral::DestructibleRampDiagonalHugeBLUR,
    Neutral::DestructibleRockEx1DiagonalHugeULBR,
    Neutral::DestructibleRockEx1HorizontalHuge,
    Neutral::DestructibleRockEx1VerticalHuge,
    Neutral::InhibitorZoneMedium,
    Neutral::InhibitorZoneSmall,
    Neutral::MineralField450,
    Protoss::AssimilatorRich,
    Terran::RefineryRich,
    Zerg::ExtractorRich,
    Neutral::DestructibleRock2x4Vertical,  // 366
    Neutral::DestructibleRock2x4Horizontal,  // 367
    Neutral::DestructibleRock2x6Vertical,  // 368
    Neutral::DestructibleRock2x6Horizontal,  // 369
    Neutral::DestructibleRock4x4,  // 370
    Neutral::DestructibleRampVerticalHuge,  // 374
    Neutral::DestructibleRampHorizontalHuge,  // 375
    Zerg::NydusCanalAttacker,  // 491
    Zerg::NydusCanalCreeper,  // 492
    Neutral::UnbuildableBricksSmallUnit,  // 602
    Neutral::UnbuildablePlatesSmallUnit,  // 603
    Neutral::UnbuildablePlatesUnit,  // 604
    Neutral::UnbuildableRocksSmallUnit,  // 605
    Neutral::DestructibleRock6x6Weak,  // 613
    Neutral::DestructibleCityDebris2x4Vertical,  // 624
    Neutral::DestructibleCityDebris2x4Horizontal,  // 625
    Neutral::DestructibleCityDebris2x6Vertical,  // 626
    Neutral::DestructibleCityDebris2x6Horizontal,  // 627
    Neutral::DestructibleCityDebrisHugeDiagonalULBR,  // 631
    Neutral::DestructibleRockEx12x4Vertical,  // 634
    Neutral::DestructibleRockEx12x4Horizontal,  // 635
    Neutral::DestructibleRockEx12x6Vertical,  // 636
    Neutral::DestructibleRockEx12x6Horizontal,  // 637
    Neutral::DestructibleIce2x4Vertical,  // 644
    Neutral::DestructibleIce2x4Horizontal,  // 645
    Neutral::DestructibleIce2x6Vertical,  // 646
    Neutral::DestructibleIce2x6Horizontal,  // 647
    Neutral::DestructibleIceDiagonalHugeULBR,  // 650
    Neutral::DestructibleIceVerticalHuge,  // 652
    Neutral::DestructibleIceHorizontalHuge,  // 653
    Neutral::UnbuildableBricksUnit,  // 656
    Neutral::UnbuildableRocksUnit,  // 657
    Neutral::CollapsiblePurifierTowerDebris,  // 747
    Neutral::CollapsiblePurifierTowerPushUnit,  // 798
    Neutral::DestructibleExpeditionGate6x6,  // 836
    Neutral::DestructibleZergInfestation3x3,  // 837
    Neutral::XelNagaDestructibleRampBlocker6S,  // 861
    Neutral::XelNagaDestructibleRampBlocker6SE,  // 862
    Neutral::XelNagaDestructibleRampBlocker6E,  // 863
    Neutral::XelNagaDestructibleRampBlocker6NE,  // 864
    Neutral::XelNagaDestructibleRampBlocker6N,  // 865
    Neutral::XelNagaDestructibleRampBlocker6NW,  // 866
    Neutral::XelNagaDestructibleRampBlocker6W,  // 867
    Neutral::XelNagaDestructibleRampBlocker6SW,  // 868
    Neutral::XelNagaDestructibleRampBlocker8S,  // 869
    Neutral::XelNagaDestructibleRampBlocker8SE,  // 870
    Neutral::XelNagaDestructibleRampBlocker8E,  // 871
    Neutral::XelNagaDestructibleRampBlocker8NE,  // 872
    Neutral::XelNagaDestructibleRampBlocker8N,  // 873
    Neutral::XelNagaDestructibleRampBlocker8NW,  // 874
    Neutral::XelNagaDestructibleRampBlocker8W,  // 875
    Neutral::XelNagaDestructibleRampBlocker8SW,  // 876
    Neutral::CollapsiblePurifierTowerDiagonal,  // 882
    Terran::SupplyDepotDrop,  // 900
    Terran::BarracksTechReactor,  // 958
    Terran::FactoryTechReactor,  // 959
    Terran::StarportTechReactor,  // 960
    Terran::BattlecruiserHeliosMorph,  // 978
    Neutral::SpacePlatformCliffDoorOpen0,  // 980
    Neutral::SpacePlatformCliffDoor0,  // 981
    Neutral::SpacePlatformCliffDoorOpen1,  // 982
    Neutral::SpacePlatformCliffDoor1,  // 983
    Neutral::DestructibleGateDiagonalBLURLowered,  // 984
    Neutral::DestructibleGateDiagonalULBRLowered,  // 985
    Neutral::DestructibleGateStraightHorizontalBFLowered,  // 986
    Neutral::DestructibleGateStraightHorizontalLowered,  // 987
    Neutral::DestructibleGateStraightVerticalLFLowered,  // 988
    Neutral::DestructibleGateStraightVerticalLowered,  // 989
    Neutral::DestructibleGateDiagonalBLUR,  // 990
    Neutral::DestructibleGateDiagonalULBR,  // 991
    Neutral::DestructibleGateStraightHorizontalBF,  // 992
    Neutral::DestructibleGateStraightHorizontal,  // 993
    Neutral::DestructibleGateStraightVerticalLF,  // 994
    Neutral::DestructibleGateStraightVertical,  // 995
    Terran::BattlecruiserHelios,  // 1024
    Neutral::SpacePlatformDestructibleJumboBlocker,  // 1205
    Neutral::SpacePlatformDestructibleLargeBlocker,  // 1206
    Neutral::SpacePlatformDestructibleMediumBlocker,  // 1207
    Neutral::SpacePlatformDestructibleSmallBlocker,  // 1208
    Neutral::DestructibleKorhalFlag,  // 1233
    Neutral::DestructibleKorhalPodium,  // 1234
    Neutral::DestructibleKorhalTree,  // 1235
    Neutral::DestructibleKorhalFoliage,  // 1236
    Neutral::DestructibleSandbags,  // 1237
    Neutral::InfestationSpire,  // 1751
    Neutral::SpacePlatformVentsUnit,  // 1752
    Neutral::DestructibleWallCorner45ULBL,  // 1801
    Neutral::DestructibleWallCorner45ULUR,  // 1802
    Neutral::DestructibleWallCorner45URBR,  // 1803
    Neutral::DestructibleWallCorner45,  // 1804
    Neutral::DestructibleWallCorner45UR90L,  // 1805
    Neutral::DestructibleWallCorner45UL90B,  // 1806
    Neutral::DestructibleWallCorner45BL90R,  // 1807
    Neutral::DestructibleWallCorner45BR90T,  // 1808
    Neutral::DestructibleWallCorner90L45BR,  // 1809
    Neutral::DestructibleWallCorner90T45BL,  // 1810
    Neutral::DestructibleWallCorner90R45UL,  // 1811
    Neutral::DestructibleWallCorner90B45UR,  // 1812
    Neutral::DestructibleWallCorner90TR,  // 1813
    Neutral::DestructibleWallCorner90BR,  // 1814
    Neutral::DestructibleWallCorner90LB,  // 1815
    Neutral::DestructibleWallCorner90LT,  // 1816
    Neutral::DestructibleWallDiagonalBLUR,  // 1817
    Neutral::DestructibleWallDiagonalBLURLF,  // 1818
    Neutral::DestructibleWallDiagonalULBRLF,  // 1819
    Neutral::DestructibleWallDiagonalULBR,  // 1820
    Neutral::DestructibleWallStraightVertical,  // 1821
    Neutral::DestructibleWallVerticalLF,  // 1822
    Neutral::DestructibleWallStraightHorizontal,  // 1823
    Neutral::DestructibleWallStraightHorizontalBF,  // 1824
    Neutral::XelNagaDestructibleBlocker6S,  // 1893
    Neutral::XelNagaDestructibleBlocker6SE,  // 1894
    Neutral::XelNagaDestructibleBlocker6E,  // 1895
    Neutral::XelNagaDestructibleBlocker6NE,  // 1896
    Neutral::XelNagaDestructibleBlocker6N,  // 1897
    Neutral::XelNagaDestructibleBlocker6NW,  // 1898
    Neutral::XelNagaDestructibleBlocker6W,  // 1899
    Neutral::XelNagaDestructibleBlocker6SW,  // 1900
    Neutral::XelNagaDestructibleBlocker8S,  // 1901
    Neutral::XelNagaDestructibleBlocker8SE,  // 1902
    Neutral::XelNagaDestructibleBlocker8E,  // 1903
    Neutral::XelNagaDestructibleBlocker8N,  // 1905
    Neutral::XelNagaDestructibleBlocker8NW,  // 1906
    Neutral::XelNagaDestructibleBlocker8W,  // 1907
}};

// These units are units that map onto other existing units (or units that
// don't matter in the case of destructible billboards).
const absl::flat_hash_map<int, int>& RedundantUnits() {
  static const auto* redundant_units = new absl::flat_hash_map<int, int>({
      {Neutral::DestructibleIce4x4, Neutral::DestructibleRockEx14x4},
      {Neutral::DestructibleIceDiagonalHugeBLUR,
       Neutral::DestructibleRampDiagonalHugeBLUR},
      {Neutral::CleaningBot, Neutral::LabBot},
      {Neutral::Lyote, Neutral::KarakFemale},
      {Neutral::DestructibleIce6x6, Neutral::DestructibleRock6x6},
      {Neutral::DestructibleCityDebris6x6, Neutral::DestructibleRock6x6},
      {Neutral::DestructibleDebris4x4, Neutral::DestructibleRockEx14x4},
      // Destructible billboards are immobile doodads floating off the map.
      {Neutral::DestructibleBillboardTall, Neutral::KarakFemale},
      {Neutral::CollapsibleTerranTower,
       Neutral::CollapsibleTerranTowerRampLeft},
      {Neutral::CollapsibleRockTower, Neutral::CollapsibleRockTowerRampLeft},
      {Neutral::ReptileCrate, Neutral::KarakFemale},
      {Neutral::Crabeetle, Neutral::KarakFemale},
      {Neutral::Debris2x2NonConjoined, Neutral::DebrisRampLeft},
      {Neutral::DestructibleCityDebris4x4, Neutral::DestructibleRockEx14x4},
      {Neutral::DestructibleRampDiagonalHugeULBR,
       Neutral::DestructibleRockEx1DiagonalHugeULBR},
      {Neutral::Dog, Neutral::KarakFemale},
      {Neutral::InhibitorZoneMedium, Neutral::InhibitorZoneSmall},
  });
  return *redundant_units;
}

// Data taken from uint8_buff_types.BUFF_LIST.
std::array<int, 47> kBuffsList = {
    {Buffs::BansheeCloak,
     Buffs::BlindingCloud,
     Buffs::BlindingCloudStructure,
     Buffs::CarryHarvestableVespeneGeyserGas,
     Buffs::CarryHarvestableVespeneGeyserGasProtoss,
     Buffs::CarryHarvestableVespeneGeyserGasZerg,
     Buffs::CarryHighYieldMineralFieldMinerals,
     Buffs::CarryMineralFieldMinerals,
     Buffs::ChannelSnipeCombat,
     Buffs::Charging,
     Buffs::ChronoBoostEnergyCost,
     Buffs::CloakFieldEffect,
     Buffs::Contaminated,
     Buffs::EMPDecloak,
     Buffs::FungalGrowth,
     Buffs::GhostCloak,
     Buffs::GhostHoldFire,
     Buffs::GhostHoldFireB,
     Buffs::GravitonBeam,
     Buffs::GuardianShield,
     Buffs::ImmortalOverload,
     Buffs::LockOn,
     Buffs::LurkerHoldFire,
     Buffs::LurkerHoldFireB,
     Buffs::MedivacSpeedBoost,
     Buffs::NeuralParasite,
     Buffs::OracleRevelation,
     Buffs::OracleStasisTrapTarget,
     Buffs::OracleWeapon,
     Buffs::ParasiticBomb,
     Buffs::ParasiticBombSecondaryUnitSearch,
     Buffs::ParasiticBombUnitKU,
     Buffs::PowerUserWarpable,
     Buffs::PsiStorm,
     Buffs::QueenSpawnLarvaTimer,
     Buffs::RavenScramblerMissile,
     Buffs::RavenShredderMissileArmorReduction,
     Buffs::RavenShredderMissileTint,
     Buffs::Slow,
     Buffs::Stimpack,
     Buffs::StimpackMarauder,
     Buffs::SupplyDrop,
     Buffs::TemporalField,
     Buffs::ViperConsumeStructure,
     Buffs::VoidRaySwarmDamageBoost,
     Buffs::VoidRaySpeedUpgrade,
     Buffs::InhibitorZoneTemporalField}};

// Data taken from uint8_upgrade_fixed_length.UPGRADES_LIST.
std::array<int, 91> kUpgradesList = {
    {Upgrades::ResonatingGlaives,
     Upgrades::CloakingField,
     Upgrades::HyperflightRotors,
     Upgrades::WeaponRefit,
     Upgrades::Blink,
     Upgrades::Burrow,
     Upgrades::GravitonCatapult,
     Upgrades::CentrificalHooks,
     Upgrades::Charge,
     Upgrades::ChitinousPlating,
     Upgrades::CycloneRapidFireLaunchers,
     Upgrades::ShadowStrike,
     Upgrades::AdaptiveTalons,
     Upgrades::DrillingClaws,
     Upgrades::GroovedSpines,
     Upgrades::MuscularAugments,
     Upgrades::ExtendedThermalLance,
     Upgrades::GlialReconstitution,
     Upgrades::GraviticDrive,
     Upgrades::HiSecAutoTracking,
     Upgrades::InfernalPreigniter,
     Upgrades::PathogenGlands,
     Upgrades::AdvancedBallistics,
     Upgrades::HighCapacityFuelTanks,
     Upgrades::NeosteelFrame,
     Upgrades::NeuralParasite,
     Upgrades::GraviticBooster,
     Upgrades::PneumatizedCarapace,
     Upgrades::PersonalCloaking,
     Upgrades::AnionPulseCrystals,
     Upgrades::ProtossAirArmorsLevel1,
     Upgrades::ProtossAirArmorsLevel2,
     Upgrades::ProtossAirArmorsLevel3,
     Upgrades::ProtossAirWeaponsLevel1,
     Upgrades::ProtossAirWeaponsLevel2,
     Upgrades::ProtossAirWeaponsLevel3,
     Upgrades::ProtossGroundArmorsLevel1,
     Upgrades::ProtossGroundArmorsLevel2,
     Upgrades::ProtossGroundArmorsLevel3,
     Upgrades::ProtossGroundWeaponsLevel1,
     Upgrades::ProtossGroundWeaponsLevel2,
     Upgrades::ProtossGroundWeaponsLevel3,
     Upgrades::ProtossShieldsLevel1,
     Upgrades::ProtossShieldsLevel2,
     Upgrades::ProtossShieldsLevel3,
     Upgrades::PsiStorm,
     Upgrades::ConcussiveShells,
     Upgrades::CorvidReactor,
     Upgrades::CombatShield,
     Upgrades::SmartServos,
     Upgrades::Stimpack,
     Upgrades::TerranStructureArmor,
     Upgrades::TerranInfantryArmorsLevel1,
     Upgrades::TerranInfantryArmorsLevel2,
     Upgrades::TerranInfantryArmorsLevel3,
     Upgrades::TerranInfantryWeaponsLevel1,
     Upgrades::TerranInfantryWeaponsLevel2,
     Upgrades::TerranInfantryWeaponsLevel3,
     Upgrades::TerranShipWeaponsLevel1,
     Upgrades::TerranShipWeaponsLevel2,
     Upgrades::TerranShipWeaponsLevel3,
     Upgrades::TerranVehicleAndShipArmorsLevel1,
     Upgrades::TerranVehicleAndShipArmorsLevel2,
     Upgrades::TerranVehicleAndShipArmorsLevel3,
     Upgrades::TerranVehicleWeaponsLevel1,
     Upgrades::TerranVehicleWeaponsLevel2,
     Upgrades::TerranVehicleWeaponsLevel3,
     Upgrades::TunnelingClaws,
     Upgrades::WarpGateResearch,
     Upgrades::ZergFlyerArmorsLevel1,
     Upgrades::ZergFlyerArmorsLevel2,
     Upgrades::ZergFlyerArmorsLevel3,
     Upgrades::ZergFlyerWeaponsLevel1,
     Upgrades::ZergFlyerWeaponsLevel2,
     Upgrades::ZergFlyerWeaponsLevel3,
     Upgrades::ZergGroundArmorsLevel1,
     Upgrades::ZergGroundArmorsLevel2,
     Upgrades::ZergGroundArmorsLevel3,
     Upgrades::AdrenalGlands,
     Upgrades::MetabolicBoost,
     Upgrades::ZergMeleeWeaponsLevel1,
     Upgrades::ZergMeleeWeaponsLevel2,
     Upgrades::ZergMeleeWeaponsLevel3,
     Upgrades::ZergMissileWeaponsLevel1,
     Upgrades::ZergMissileWeaponsLevel2,
     Upgrades::ZergMissileWeaponsLevel3,
     26,   // This is some upgrade that was in 4.1.2
     292,  // This is another upgrade in 4.1.2
     Upgrades::AnabolicSynthesis,
     Upgrades::LockOn,
     Upgrades::EnhancedShockwaves}};

template <int32_t size>
absl::flat_hash_map<int, uint8_t> BuildTable(
    const std::array<int, size>& list) {
  absl::flat_hash_map<int, uint8_t> table;
  table[0] = 0;  // 0 corresponds to the ground (no units).
  for (int i = 0; i < list.size(); i++) {
    table[list[i]] = i + 1;
  }
  return table;
}

template <int32_t size>
int LookUp(int data, const std::array<int32_t, size> list,
           const absl::flat_hash_map<int, int>& redundant_list = {}) {
  static absl::flat_hash_map<int, uint8_t>* lookup_table =
      new absl::flat_hash_map<int, uint8_t>(BuildTable<list.size()>(list));

  if (!redundant_list.empty()) {
    auto redundant = redundant_list.find(data);
    if (redundant != redundant_list.end()) {
      data = redundant->second;
    }
  }

  auto it = lookup_table->find(data);

  CHECK(it != lookup_table->end()) << " Could not find " << data;

  return it->second;
}

}  // namespace

int PySc2ToUint8(int data) {
  return LookUp<kUnitsList.size()>(data, kUnitsList, RedundantUnits());
}

int PySc2ToUint8Buffs(int data) {
  return LookUp<kBuffsList.size()>(data, kBuffsList);
}

int PySc2ToUint8Upgrades(int data) {
  return LookUp<kUpgradesList.size()>(data, kUpgradesList);
}

int MaximumUnitTypeId() {
  return kUnitsList.size();  // note that the indices have 1 added, hence no -1
}

int MaximumBuffId() {
  return kBuffsList.size();  // note that the indices have 1 added, hence no -1
}

int Uint8ToPySc2(int utype) {
  CHECK_GT(utype, 0);
  CHECK_LE(utype, kUnitsList.size());
  return kUnitsList[utype - 1];
}

int Uint8ToPySc2Upgrades(int upgrade_type) {
  CHECK_GT(upgrade_type, 0);
  CHECK_LE(upgrade_type, kUpgradesList.size());
  return kUpgradesList[upgrade_type - 1];
}

int EffectIdIdentity(int effect_id) { return effect_id; }

}  // namespace pysc2_evolved
