import enum

from sc2.ids.unit_typeid import UnitTypeId

LARVA = UnitTypeId.LARVA
OVERLORD = UnitTypeId.OVERLORD
DRONE = UnitTypeId.DRONE
HATCHERY = UnitTypeId.HATCHERY
SPAWNINGPOOL = UnitTypeId.SPAWNINGPOOL
QUEEN = UnitTypeId.QUEEN
EXTRACTOR = UnitTypeId.EXTRACTOR

MINERAL_FIELD = UnitTypeId.MINERALFIELD
VESPENE_GEYSER = UnitTypeId.VESPENEGEYSER
SPACEPLATFORMGEYSER = UnitTypeId.SPACEPLATFORMGEYSER

# Larva per minute from an injected hatch
LARVA_RATE_PER_INJECT = 11.658
DRONE_MINERALS_PER_SECOND = 0.933

class ConstructionType(enum.Enum):
    BUILDING = 0
    FROM_BUILDING = 1
    FROM_LARVA = 2

def built_by(unitId: UnitTypeId) -> ConstructionType:
    if unitId == HATCHERY or unitId == SPAWNINGPOOL or unitId == EXTRACTOR:
        return ConstructionType.BUILDING
    if unitId == (QUEEN):
        return ConstructionType.FROM_BUILDING
    return ConstructionType.FROM_LARVA

def get_resource_value(unitId: UnitTypeId) -> (int, int):
    if unitId == HATCHERY:
        return (300, 0)
    if unitId == DRONE:
        return (50, 0)
    if unitId == OVERLORD:
        return (100, 0)
    if unitId == QUEEN:
        return (150, 0)
    if unitId == SPAWNINGPOOL:
        return (200, 0)
    if unitId == EXTRACTOR:
        return (75, 0)
    return (0, 0)
