import enum
from typing import Union

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

ARMY = 9999
ECO = 9998

EGG = UnitTypeId.EGG
LARVA = UnitTypeId.LARVA

OVERLORD = UnitTypeId.OVERLORD
DRONE = UnitTypeId.DRONE
HATCHERY = UnitTypeId.HATCHERY
SPAWNINGPOOL = UnitTypeId.SPAWNINGPOOL
ROACHWARREN = UnitTypeId.ROACHWARREN
HYDRADEN = UnitTypeId.HYDRALISKDEN
QUEEN = UnitTypeId.QUEEN
EXTRACTOR = UnitTypeId.EXTRACTOR
SPIRE = UnitTypeId.SPIRE
LAIR = UnitTypeId.LAIR
HIVE = UnitTypeId.HIVE
EVO = UnitTypeId.EVOLUTIONCHAMBER

LING = UnitTypeId.ZERGLING
ROACH = UnitTypeId.ROACH
HYDRA = UnitTypeId.HYDRALISK
MUTALISK = UnitTypeId.MUTALISK

MINERAL_FIELD = UnitTypeId.MINERALFIELD
VESPENE_GEYSER = UnitTypeId.VESPENEGEYSER
SPACEPLATFORMGEYSER = UnitTypeId.SPACEPLATFORMGEYSER

LINGSPEED = UpgradeId.ZERGLINGMOVEMENTSPEED
ROACHSPEED = UpgradeId.GLIALRECONSTITUTION

MISSILE1 = UpgradeId.ZERGMISSILEWEAPONSLEVEL1
MISSILE2 = UpgradeId.ZERGMISSILEWEAPONSLEVEL2
MISSILE3 = UpgradeId.ZERGMISSILEWEAPONSLEVEL3
CARAPACE1 = UpgradeId.ZERGGROUNDARMORSLEVEL1
CARAPACE2 = UpgradeId.ZERGGROUNDARMORSLEVEL2
CARAPACE3 = UpgradeId.ZERGGROUNDARMORSLEVEL3

# Larva per minute from an injected hatch
LARVA_RATE_PER_INJECT = 11.658
DRONE_MINERALS_PER_SECOND = 0.933

class ConstructionType(enum.Enum):
    BUILDING = 0
    FROM_BUILDING = 1
    FROM_LARVA = 2

def get_construction_type(unitId: UnitTypeId) -> ConstructionType:
    if unitId == HATCHERY or unitId == SPAWNINGPOOL or unitId == EXTRACTOR or unitId == SPIRE or unitId == ROACHWARREN or unitId == EVO or unitId == HYDRADEN:
        return ConstructionType.BUILDING
    if unitId == QUEEN or unitId == LINGSPEED or unitId == LAIR or unitId == ROACHSPEED or (
        unitId==MISSILE1) or (
        unitId==MISSILE2) or (
        unitId==MISSILE3) or (
        unitId==CARAPACE1) or (
        unitId==CARAPACE2) or (
        unitId==CARAPACE3):
        return ConstructionType.FROM_BUILDING
    return ConstructionType.FROM_LARVA

def get_construction_building(id) -> UnitTypeId:
    if id == QUEEN or id == LAIR:
        return HATCHERY
    if id == LINGSPEED:
        return SPAWNINGPOOL
    if id == ROACHSPEED:
        return ROACHWARREN
    if id == MISSILE1 or (
       id == MISSILE2) or (
       id == MISSILE3) or (
       id == CARAPACE1) or (
       id == CARAPACE2) or (
       id == CARAPACE3):
       return EVO
    return None

def is_townhall(id: UnitTypeId) -> bool:
    return id == HATCHERY or id == UnitTypeId.NEXUS or id == UnitTypeId.COMMANDCENTER or id == UnitTypeId.ORBITALCOMMAND