from typing import List

from sc2 import BotAI
from sc2.units import Units

from .control_group import ControlGroup

class ControlGroupManager():
    def __init__(self, bot: BotAI):
        self.bot = bot
        self.groups: List[ControlGroup] = []
        self.new_group(Units([], self.bot._game_data))
        self.new_group(Units([], self.bot._game_data))
        self.new_group(Units([], self.bot._game_data))

    def get_groups(self):
        return self.groups
    
    def get_group(self, id: int) -> ControlGroup:
        return self.groups[id]
    
    def new_group(self, units: Units):
        self.groups.append(ControlGroup(units))