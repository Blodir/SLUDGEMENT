from sc2 import BotAI
from sc2.units import Units
from sc2.unit import Unit
from sc2.ids.ability_id import AbilityId

from .control_group_manager import ControlGroupManager
from .control_group import ControlGroup
from .scouting_manager import ScoutingManager

from .data import *
from .util import *

class UnitManager():

    def __init__(self, bot: BotAI, control_group_manager: ControlGroupManager, scouting_manager: ScoutingManager):
        self.bot = bot
        self.control_group_manager = control_group_manager
        self.scouting_manager = scouting_manager

    def iterate(self):
        actions = []

        # decide if control group should engage or disengage
        """         for group in self.control_group_manager:
            enemies = self.bot.known_enemy_units.closer_than(20, group.get_center_position())
            friendlies = group.get()
            enemy_combat_value = calculate_combat_value(enemies)
            friendly_combat_value = calculate_combat_value(friendlies)
            if friendly_combat_value > 1.2 * enemy_combat_value:
                actions.append(group.command(AbilityId.ATTACK, enemies.random))
            elif friendly_combat_value < 0.5 * enemy_combat_value:
                actions.append(group.command(AbilityId.MOVE, self.bot.expansion_locations.furthest_to(enemies.random.position))) """
        #
        
        # decide if individual unit should engage or disengage
        enemies = self.bot.known_enemy_units
        enemy_combat_value = self.bot.calculate_combat_value(enemies)
        for ling in self.bot.units(LING):
            friendlies = self.bot.units.closer_than(15, ling)
            friendly_combat_value = self.bot.calculate_combat_value(friendlies)
            if friendly_combat_value > 1.2 * enemy_combat_value:
                actions.append(ling.attack(self.bot.enemy_start_locations[0]))
            elif friendly_combat_value < 0.5 * enemy_combat_value:
                #if not self.one_of_targets_in_range(ling, enemies):
                actions.append(ling.move(self.bot.start_location))

        for expansion in self.bot.owned_expansions:
            enemy_raid = enemies.closer_than(10, expansion)
            if enemy_raid.exists:
                raid_value = self.bot.calculate_combat_value(enemy_raid)
                defenders = self.bot.units.closer_than(15, expansion)
                if raid_value > self.bot.calculate_combat_value(defenders):
                    for defender in defenders:
                        actions.append(defender.move(self.bot.start_location))
                else:
                    for defender in defenders:
                        actions.append(defender.attack(expansion.position))

        return actions

    def one_of_targets_in_range(self, unit: Unit, targets: Units):
        for target in targets:
            if unit.target_in_range(target):
                return True
        return False
