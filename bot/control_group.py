from typing import Union
from typing import List

from sc2.units import Units
from sc2.unit import Unit
from sc2.unit_command import UnitCommand
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2

class ControlGroup():
    def __init__(self, units: Units):
        self.units: Units = units

    def get_center_position(self):
        x = 0
        y = 0
        for unit in self.units:
            x += unit.position.x
            y += unit.position.y
        amount = self.units.amount
        if amount != 0:
            x = x / amount
            y = y / amount
        return Point2((x, y))
    
    def command(self, ability: AbilityId, target: Unit, queue = False) -> List[UnitCommand]:
        res: List[UnitCommand] = []
        for unit in self.units:
            res.append(UnitCommand(ability, unit, target, queue))
        return res
    
    def add(self, units: Union[Units, Unit]):
        if isinstance(units, Unit):
            self.units.append(units)
        else:
            self.units.extend(units)

    def merge_to(self, target):
        # TODO
        pass
    
    def remove(self, units: Union[Units, Unit]):
        # TODO
        pass
    
    def get(self):
        return self.units