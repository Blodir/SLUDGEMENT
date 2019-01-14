from sc2 import BotAI
from sc2.units import Units
from sc2.unit import Unit

from .data import *

class UnitManager():

    def __init__(self, bot: BotAI):
        self.bot = bot

    def iterate(self):
        actions = []
        enemies = self.bot.known_enemy_units
        enemy_combat_value = self.calculate_combat_value(enemies)
        for ling in self.bot.units(LING):
            friendlies = self.bot.units.closer_than(15, ling)
            friendly_combat_value = self.calculate_combat_value(friendlies)
            if friendly_combat_value > 1.2 * enemy_combat_value:
                actions.append(ling.attack(self.bot.enemy_start_locations[0]))
            elif friendly_combat_value < 0.5 * enemy_combat_value:
                if not self.one_of_targets_in_range(ling, enemies):
                    actions.append(ling.move(self.bot.start_location))
        for expansion in self.bot.owned_expansions:
            enemy_raid = enemies.closer_than(10, expansion)
            if enemy_raid.exists:
                raid_value = self.calculate_combat_value(enemy_raid)
                defenders = self.bot.units.closer_than(15, expansion)
                if raid_value > self.calculate_combat_value(defenders):
                    for defender in defenders:
                        actions.append(defender.move(self.bot.start_location))
                else:
                    for defender in defenders:
                        actions.append(defender.attack(expansion.position))

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
