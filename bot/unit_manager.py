from typing import List

from sc2 import BotAI
from sc2.units import Units
from sc2.unit import Unit
from sc2.ids.ability_id import AbilityId
from sc2.unit_command import UnitCommand

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
        actions: List[UnitCommand] = []

        enemy_units = self.bot.known_enemy_units

        # decide if control group should engage or disengage
        """         for group in self.control_group_manager.get_groups():
            enemies = enemy_units.closer_than(15, group.get_center_position())
            if not enemies.exists:
                continue
            friendlies = group.get().ready
            enemy_combat_value = self.bot.calculate_combat_value(enemies)
            friendly_combat_value = self.bot.calculate_combat_value(friendlies)
            if friendly_combat_value > 1.2 * enemy_combat_value:
                self.addActionsNoDuplicates(group.command(AbilityId.ATTACK, enemies.random), actions)
            elif friendly_combat_value < 0.8 * enemy_combat_value:
                self.addActionsNoDuplicates(group.command(AbilityId.MOVE, self.bot.start_location), actions) """
        #
        
        # decide if individual unit should engage or disengage
        for ling in self.bot.units(LING):
            enemies = self.scouting_manager.observed_enemy_units.closer_than(15, ling)
            enemy_combat_value = self.bot.calculate_combat_value(enemies)
            friendlies = self.bot.units.closer_than(15, ling)
            friendly_combat_value = self.bot.calculate_combat_value(friendlies)
            if friendly_combat_value > 1.2 * enemy_combat_value:
                actions.append(ling.attack(self.bot.enemy_start_locations[0]))
            elif friendly_combat_value < 0.5 * enemy_combat_value:
                #if not self.one_of_targets_in_range(ling, enemies):
                actions.append(ling.move(self.bot.start_location))

        for expansion in self.bot.owned_expansions:
            enemy_raid = enemy_units.closer_than(20, expansion)
            if enemy_raid.exists:
                # self.addActionsNoDuplicates(self.control_group_manager.get_group(2).command(AbilityId.ATTACK, expansion), actions)
                raid_value = self.bot.calculate_combat_value(enemy_raid)
                defenders = self.bot.units.closer_than(15, expansion).ready
                if raid_value > self.bot.calculate_combat_value(defenders.filter(lambda u: u.type_id != DRONE)):
                    for defender in defenders:
                        if expansion != self.bot.start_location:
                            if defender.type_id == DRONE:
                                self.addActionsNoDuplicates(defender.gather(self.bot.main_minerals.random), actions)
                            else:
                                self.addActionsNoDuplicates(defender.move(self.bot.start_location), actions)
                        else:
                            # counter worker rush
                            self.addActionsNoDuplicates(defender.attack(expansion.position), actions)
                else:
                    for defender in defenders:
                        if defender.type_id != DRONE:
                            self.addActionsNoDuplicates(defender.attack(expansion.position), actions)

        if self.scouting_manager.own_army_value > 1.2 * self.scouting_manager.estimated_enemy_army_value:
            # TODO merge group 2 into 1 and attack with 1
            # self.addActionsNoDuplicates(self.control_group_manager.get_group(2).command(AbilityId.ATTACK, self.bot.enemy_start_locations[0]), actions)
            pass

        return actions

    def one_of_targets_in_range(self, unit: Unit, targets: Units):
        for target in targets:
            if unit.target_in_range(target):
                return True
        return False


    # FIXME: Super slow algorithm for making sure an unit is only given one action
    def addActionsNoDuplicates(self, commands: Union[UnitCommand, List[UnitCommand]], actions: List[UnitCommand]):
        actions_to_add = []
        if isinstance(commands, List):
            for cmd in commands:
                for action in actions:
                    if cmd.unit.tag == action.unit.tag:
                        break
                    else:
                        actions_to_add.append(action)
        else:
            actions_to_add.append(commands)
        actions.extend(actions_to_add)