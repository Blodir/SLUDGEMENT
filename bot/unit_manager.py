from typing import List, Union

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
        self.unselectable = Units([], self.bot._game_data)

    def iterate(self, iteration):
        actions: List[UnitCommand] = []

        all_army: Units = self.bot.units.exclude_type({OVERLORD, DRONE, QUEEN, LARVA, EGG}).not_structure.ready
        observed_enemy_army = self.scouting_manager.observed_enemy_units.not_structure.exclude_type({OVERLORD})
        estimated_enemy_value = self.scouting_manager.estimated_enemy_army_value

        enemy_raiders = self.get_enemy_raiders()

        army_units = all_army

        for observed_enemy in observed_enemy_army:
            pos = observed_enemy.position
            self.bot._client.debug_text_world(f'observed', Point3((pos.x, pos.y, 10)), None, 12)

        # ARMY MANAGEMENT

        if iteration % 300 == 0 and self.unselectable.amount == 0:
            if army_units(LING).exists:
                unit: Unit = army_units(LING).random
                scouting_order: List[Point2] = []
                keys: List[Point2] = list(self.bot.expansion_locations.keys())
                for idx in range(len(self.bot.expansion_locations)):
                    closest = self.bot.start_location.closest(keys)
                    scouting_order.append(closest)
                    keys.remove(closest)
                for position in scouting_order:
                    actions.append(unit.move(position, True))
                    self.unselectable.append(unit)
                
        for unit in self.unselectable:
            self.bot._client.debug_text_world(f'scouting', Point3((unit.position.x, unit.position.y, 10)), None, 12)

        groups: List[Units] = self.group_army(army_units.tags_not_in(self.unselectable.tags))

        for group in groups:
            nearby_enemies = None
            if observed_enemy_army.exists:
                closest_enemy = observed_enemy_army.closest_to(group.center)
                if closest_enemy.distance_to(group.center) < 15:
                    nearby_enemies: Units = observed_enemy_army.closer_than(15, closest_enemy)
                    enemy_value = self.bot.calculate_combat_value(nearby_enemies)
            group_value = self.bot.calculate_combat_value(group)

            if nearby_enemies and nearby_enemies.exists:
                if group_value > enemy_value:
                    # attack enemy group
                    actions.extend(self.command_group(group, AbilityId.ATTACK, nearby_enemies.center))
                    self.bot._client.debug_text_world(f'attacking group', Point3((group.center.x, group.center.y, 10)), None, 12)
                else:
                    # retreat somewhwere
                    move_position = self.bot.start_location
                    if group.center.distance_to(move_position) < 5:
                        actions.extend(self.command_group(group, AbilityId.ATTACK, move_position))
                        self.bot._client.debug_text_world(f'attacking', Point3((group.center.x, group.center.y, 10)), None, 12)
                    else:
                        actions.extend(self.command_group(group, AbilityId.MOVE, move_position))
                        self.bot._client.debug_text_world(f'retreating', Point3((group.center.x, group.center.y, 10)), None, 12)
            else:
                # do other stuff
                if group_value > 1.2 * estimated_enemy_value:
                    if self.bot.known_enemy_units.exists:
                        attack_position = self.bot.known_enemy_units.closest_to(group.center).position
                    else:
                        attack_position = self.bot.enemy_start_locations[0]
                    actions.extend(self.command_group(group, AbilityId.ATTACK, attack_position))
                    self.bot._client.debug_text_world(f'attacking base', Point3((group.center.x, group.center.y, 10)), None, 12)
                else:
                    # merge
                    other_units: Units = all_army.tags_not_in(group.tags)
                    if other_units.exists:
                        closest_other_unit: Unit = other_units.closest_to(group.center)
                        actions.extend(self.command_group(group, AbilityId.MOVE, closest_other_unit.position))
                        self.bot._client.debug_text_world(f'merging', Point3((group.center.x, group.center.y, 10)), None, 12)
                    else:
                        self.bot._client.debug_text_world(f'idle', Point3((group.center.x, group.center.y, 10)), None, 12)

        # QUEENS AND DRONES
        for expansion in self.bot.owned_expansions:
            enemy_raid = observed_enemy_army.closer_than(20, expansion)
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
                            if enemy_raid.closer_than(5, defender.position).exists:
                                self.bot._client.debug_text_world(f'pull the bois', Point3((pos.x, pos.y, 10)), None, 12)
                                actions.append(defender.attack(expansion.position))
























        '''
        to_remove = []
        for unit in army_units_wo_orders:
            if unit.tag in to_remove:
                continue
            nearby_units = army_units_wo_orders.closer_than(5, unit.position)
            if nearby_units.exists:
                groups.append(nearby_units)
                to_remove.extend(nearby_units.tags)
        army_units_wo_orders = army_units_wo_orders.tags_not_in(set(to_remove))
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
        '''
        return actions

    def one_of_targets_in_range(self, unit: Unit, targets: Units):
        for target in targets:
            if unit.target_in_range(target):
                return True
        return False
    
    def get_enemy_raiders(self):
        output = {}
        for exp_position in self.bot.owned_expansions:
            enemies = self.bot.known_enemy_units.closer_than(15, exp_position)
            output[exp_position] = enemies
        return output
    
    def group_army(self, army: Units) -> List[Units]:
        groups: List[Units] = []
        already_grouped_tags = []

        for unit in army:
            if unit.tag in already_grouped_tags:
                continue
            # TODO: fix recursive grouping
            # neighbors: Units = self.find_neighbors(unit, army.tags_not_in(set(already_grouped_tags)))
            neighbors: Units = army.closer_than(5, unit.position)
            groups.append(neighbors)
            already_grouped_tags.extend(neighbors.tags)
        
        return groups
                
    def find_neighbors(self, THE_SOURCE: Unit, units: Units) -> Units:
        neighbors: Units = units.closer_than(3, THE_SOURCE.position)

        temp: Units = Units([], self.bot._game_data)
        for individual in neighbors:
            temp.__or__(self.find_neighbors(individual, units.tags_not_in(neighbors.tags)))
        output = neighbors.__or__(temp)
        if output is None:
            return Units([], self.bot._game_data)
        return neighbors.__or__(temp)

    def command_group(self, units: Units, command: UnitCommand, target: Union[Unit, Point2]):
        commands = []
        for unit in units:
            commands.append(unit(command, target))
        return commands