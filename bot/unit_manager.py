from sc2 import BotAI
from sc2.units import Units
from sc2.unit import Unit

from .data import *

class UnitManager():

    def __init__(self, bot: BotAI):
        self.bot = bot

    def iterate(self):
        actions = []
        for ling in self.bot.units(LING):
            enemies = self.bot.known_enemy_units
            friendlies = self.bot.units.closer_than(15, ling)
            enemy_combat_value = self.calculate_combat_value(enemies)
            friendly_combat_value = self.calculate_combat_value(friendlies)
            if friendly_combat_value > 1.2 * enemy_combat_value:
                actions.append(ling.attack(self.bot.enemy_start_locations[0]))
            elif friendly_combat_value < 0.5 * enemy_combat_value:
                if not self.one_of_targets_in_range(ling, enemies):
                    actions.append(ling.move(self.bot.start_location))
        return actions
    
    def calculate_combat_value(self, units: Units):
        value = 0
        for unit in units.filter(lambda u: u.can_attack_ground):
            resources = self.bot.get_resource_value(unit.type_id)
            minerals = resources[0]
            vespene = resources[1]
            value += (minerals + vespene)
        return value

    def one_of_targets_in_range(self, unit: Unit, targets: Units):
        for target in targets:
            if unit.target_in_range(target):
                return True
        return False
