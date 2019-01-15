from typing import List

from sc2.units import Units

from .control_group import ControlGroup

class ControlGroupManager():
    def __init__(self):
        self.groups: List[ControlGroup] = []

    def get_groups(self):
        return self.groups
    
    def new_group(self, units: Units):
        self.groups.append(ControlGroup(units))