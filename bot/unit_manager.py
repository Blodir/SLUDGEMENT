from typing import List

from sc2 import BotAI
from sc2.units import Units
from sc2.unit import Unit
from sc2.ids.ability_id import AbilityId
from sc2.unit_command import UnitCommand
from sc2.position import Point2, Point3

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

        observed_enemy_units = self.scouting_manager.observed_enemy_units

        # ARMY MANAGEMENT

        all_army: Units = self.bot.units.exclude_type({OVERLORD, DRONE, QUEEN, LARVA, EGG}).not_structure.ready
        remaining_units = all_army
        groups = []

        to_remove = []
        for unit in remaining_units:
            if unit.tag in to_remove:
                continue
            nearby_units = remaining_units.closer_than(5, unit.position)
            if nearby_units.exists:
                groups.append(nearby_units)
                to_remove.extend(nearby_units.tags)
        remaining_units = remaining_units.tags_not_in(set(to_remove))
        for unit_group in groups:
            enemies = observed_enemy_units.filter(lambda u: u.can_attack_ground).closer_than(20, unit_group.center)
            own_value = self.bot.calculate_combat_value(unit_group)
            center: Point2 = unit_group.center
            if enemies.exists:
                enemy_value = self.bot.calculate_combat_value(enemies)
                difference = own_value - enemy_value
                if own_value > 1.2 * enemy_value:
                    self.bot._client.debug_text_world(f'fighting: {difference}', Point3((center.x, center.y, 10)), None, 12)
                    for unit in unit_group:
                        actions.append(unit.attack(enemies.center))
                else:
                    # retreat
                    distance_to_main = unit_group.center.distance_to(self.bot.start_location)
                    if distance_to_main < 5:
                        self.bot._client.debug_text_world(f'fighting: {difference}', Point3((center.x, center.y, 10)), None, 12)
                        for unit in unit_group:
                            actions.append(unit.attack(self.bot.start_location))
                    else:
                        self.bot._client.debug_text_world(f'retreating: {difference}', Point3((center.x, center.y, 10)), None, 12)
                        for unit in unit_group:
                            actions.append(unit.move(self.bot.start_location))
            elif own_value > 1.2 * self.scouting_manager.estimated_enemy_army_value:
                difference = own_value - self.scouting_manager.estimated_enemy_army_value
                self.bot._client.debug_text_world(f'attacking base: {difference}', Point3((center.x, center.y, 10)), None, 12)
                for unit in unit_group:
                    actions.append(unit.attack(self.bot.enemy_start_locations[0]))
            else:
                self.bot._client.debug_text_world('merging', Point3((center.x, center.y, 10)), None, 12)
                # merge groups
                temp = all_army.tags_not_in(unit_group.tags)
                if temp.exists:
                    target_pos = temp.closest_to(unit_group.center).position
                    for unit in unit_group:
                        actions.append(unit.move(target_pos))
        
        # DRONES AND QUEENS

        for expansion in self.bot.owned_expansions:
            enemy_raid = observed_enemy_units.closer_than(20, expansion)
            if enemy_raid.exists:
                raid_value = self.bot.calculate_combat_value(enemy_raid)
                defending_army: Units = all_army.closer_than(15, expansion)
                if raid_value > self.bot.calculate_combat_value(defending_army.exclude_type({DRONE})):
                    for defender in self.bot.units.closer_than(15, expansion):
                        pos = defender.position
                        if expansion != self.bot.start_location:
                            if defender.type_id == DRONE:
                                self.bot._client.debug_text_world(f'mineral walking', Point3((pos.x, pos.y, 10)), None, 12)
                                actions.append(defender.gather(self.bot.main_minerals.random))
                            elif defender.type_id == QUEEN:
                                self.bot._client.debug_text_world(f'attacking', Point3((pos.x, pos.y, 10)), None, 12)
                                actions.append(defender.attack(expansion.position))
                        else:
                            # counter worker rush
                            self.bot._client.debug_text_world(f'pull the bois', Point3((pos.x, pos.y, 10)), None, 12)
                            actions.append(defender.attack(expansion.position))


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
        '''
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
        '''

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