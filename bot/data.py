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
QUEEN = UnitTypeId.QUEEN
EXTRACTOR = UnitTypeId.EXTRACTOR
LAIR = UnitTypeId.LAIR
HIVE = UnitTypeId.HIVE

LING = UnitTypeId.ZERGLING

MINERAL_FIELD = UnitTypeId.MINERALFIELD
VESPENE_GEYSER = UnitTypeId.VESPENEGEYSER
SPACEPLATFORMGEYSER = UnitTypeId.SPACEPLATFORMGEYSER

LINGSPEED = UpgradeId.ZERGLINGMOVEMENTSPEED

# Larva per minute from an injected hatch
LARVA_RATE_PER_INJECT = 11.658
DRONE_MINERALS_PER_SECOND = 0.933

class ConstructionType(enum.Enum):
    BUILDING = 0
    FROM_BUILDING = 1
    FROM_LARVA = 2

def get_construction_type(unitId: UnitTypeId) -> ConstructionType:
    if unitId == HATCHERY or unitId == SPAWNINGPOOL or unitId == EXTRACTOR:
        return ConstructionType.BUILDING
    if unitId == QUEEN or unitId == LINGSPEED:
        return ConstructionType.FROM_BUILDING
    return ConstructionType.FROM_LARVA

def get_construction_building(id) -> UnitTypeId:
    if id == QUEEN:
        return HATCHERY
    if id == LINGSPEED:
        return SPAWNINGPOOL
    return None

def is_townhall(id: UnitTypeId) -> bool:
    return id == HATCHERY or id == UnitTypeId.NEXUS or id == UnitTypeId.COMMANDCENTER or id == UnitTypeId.ORBITALCOMMAND