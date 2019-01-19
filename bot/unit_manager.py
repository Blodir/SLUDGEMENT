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
        self.unselectable_enemy_units = Units([], self.bot._game_data)
        self.scouting_ttl = 300

    def iterate(self, iteration):
        self.scouting_ttl -= 1

        actions: List[UnitCommand] = []

        all_army: Units = self.bot.units.exclude_type({OVERLORD, DRONE, QUEEN, LARVA, EGG}).not_structure.ready
        observed_enemy_army = self.scouting_manager.observed_enemy_units.filter(lambda u: u.can_attack_ground)
        estimated_enemy_value = self.scouting_manager.estimated_enemy_army_value

        enemy_raiders = self.get_enemy_raiders()
        enemy_raiders_value = 0
        for base_position in enemy_raiders:
            enemy_raiders_value += self.bot.calculate_combat_value(enemy_raiders[base_position])

        army_units = all_army

        for observed_enemy in observed_enemy_army:
            pos = observed_enemy.position
            self.bot._client.debug_text_world(f'observed', Point3((pos.x, pos.y, 10)), None, 12)

        # SCOUTING

        if army_units(LING).exists and self.scouting_ttl < 0 and enemy_raiders_value == 0:
            self.scouting_ttl = 300
            unit: Unit = army_units(LING).random
            actions.append(unit.stop())
            scouting_order: List[Point2] = []
            keys: List[Point2] = list(self.bot.expansion_locations.keys())
            for idx in range(len(self.bot.expansion_locations)):
                closest = self.bot.start_location.closest(keys)
                scouting_order.append(closest)
                keys.remove(closest)
            for position in scouting_order:
                actions.append(unit.move(position, True))
            self.unselectable.append(unit)

        # UPDATE UNSELECTABLE UNITS SNAPSHOTS

        self.unselectable = self.bot.units.tags_in(self.unselectable.tags)

        to_remove = []
        for unit in self.unselectable:
            self.bot._client.debug_text_world(f'unselectable', Point3((unit.position.x, unit.position.y, 10)), None, 12)
            if unit.is_idle or unit.is_gathering or not unit.is_visible:
                to_remove.append(unit.tag)
        self.unselectable = self.unselectable.tags_not_in(set(to_remove))

        # ARMY GROUPS

        groups: List[Units] = self.group_army(army_units.tags_not_in(self.unselectable.tags))

        for group in groups:
            nearby_enemies = None
            if observed_enemy_army.exists:
                closest_enemy = observed_enemy_army.closest_to(group.center)
                if closest_enemy.distance_to(group.center) < 15:
                    nearby_enemies: Units = observed_enemy_army.closer_than(15, closest_enemy)
                    enemy_value = self.bot.calculate_combat_value(nearby_enemies.ready)
            group_value = self.bot.calculate_combat_value(group)

            if nearby_enemies and nearby_enemies.exists:
                if group_value + self.bot.calculate_combat_value(self.bot.units.exclude_type({DRONE, OVERLORD}).closer_than(15, group.center)) > enemy_value:
                    # attack enemy group
                    actions.extend(self.command_group(group, AbilityId.ATTACK, nearby_enemies.center))
                    self.bot._client.debug_text_world(f'attacking group', Point3((group.center.x, group.center.y, 10)), None, 12)
                else:
                    # retreat somewhwere
                    mins = self.bot.get_mineral_fields_for_expansion(self.bot.closest_mining_expansion_location(group.center).position)
                    if mins.exists:
                        move_position = mins.center
                    else:
                        move_position = self.bot.start_location
                    if group.center.distance_to(move_position) < 5:
                        # Last resort attack with everything
                        everything:Units = group
                        if enemy_value > 200:
                            everything = self.bot.units.closer_than(15, group.center)
                            self.unselectable.extend(everything)
                        everything = everything.__and__(self.bot.units(QUEEN))
                        actions.extend(self.command_group(everything, AbilityId.ATTACK, nearby_enemies.center))
                        self.bot._client.debug_text_world(f'attacking', Point3((group.center.x, group.center.y, 10)), None, 12)
                    else:
                        actions.extend(self.command_group(group, AbilityId.MOVE, move_position))
                        self.bot._client.debug_text_world(f'retreating', Point3((group.center.x, group.center.y, 10)), None, 12)
            else:
                if group_value > 1.2 * estimated_enemy_value:
                    # attack toward closest enemy buildings
                    attack_position = self.bot.enemy_start_locations[0]
                    if self.scouting_manager.observed_enemy_units.exists:
                        target_enemy_units: Units = self.scouting_manager.observed_enemy_units.exclude_type(OVERLORD)
                        if target_enemy_units.exists:
                            attack_position = target_enemy_units.closest_to(group.center).position
                    actions.extend(self.command_group(group, AbilityId.ATTACK, attack_position))
                    self.bot._client.debug_text_world(f'attacking base', Point3((group.center.x, group.center.y, 10)), None, 12)
                else:
                    # merge
                    other_units: Units = all_army.tags_not_in(group.tags.union(self.unselectable.tags))
                    if other_units.exists:
                        closest_other_unit: Unit = other_units.closest_to(group.center)
                        actions.extend(self.command_group(group, AbilityId.MOVE, closest_other_unit.position))
                        self.bot._client.debug_text_world(f'merging', Point3((group.center.x, group.center.y, 10)), None, 12)
                    else:
                        self.bot._client.debug_text_world(f'idle', Point3((group.center.x, group.center.y, 10)), None, 12)

        # QUEENS AND DRONES
        for expansion in self.bot.owned_expansions:
            enemy_raid: Units = observed_enemy_army.closer_than(20, expansion)
            if enemy_raid.exists:
                raid_value = self.bot.calculate_combat_value(enemy_raid)
                defending_army: Units = all_army.closer_than(15, expansion)
                if raid_value > self.bot.calculate_combat_value(defending_army.exclude_type({DRONE})):
                    for defender in self.bot.units.closer_than(15, expansion).tags_not_in(self.unselectable.tags):
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
                                actions.append(defender.attack(enemy_raid.center))
                            elif enemy_raid.of_type({DRONE, UnitTypeId.SCV, UnitTypeId.PROBE}).exists:
                                if raid_value > 90:
                                    self.bot._client.debug_text_world(f'defend worker rush', Point3((pos.x, pos.y, 10)), None, 12)
                                    actions.append(defender.attack(enemy_raid.center))

        # DEFEND CANNON RUSH WITH DRONES

        for expansion in self.bot.owned_expansions:
            enemy_scouting_workers = self.bot.known_enemy_units({DRONE, UnitTypeId.PROBE, UnitTypeId.SCV}).closer_than(20, expansion).tags_not_in(self.unselectable_enemy_units.tags)
            enemy_proxies = self.bot.known_enemy_structures.closer_than(20, expansion).tags_not_in(self.unselectable_enemy_units.tags)
            if enemy_proxies.exists:
                for proxy in enemy_proxies:
                    if proxy.type_id == UnitTypeId.PHOTONCANNON:
                        for drone in self.bot.units(DRONE).tags_not_in(self.unselectable.tags).take(4, False):
                            actions.append(drone.attack(proxy))
                            self.unselectable.append(drone)
                            self.unselectable_enemy_units.append(proxy)
            if enemy_scouting_workers.exists:
                for enemy_worker in enemy_scouting_workers:
                    own_workers: Units = self.bot.units(DRONE).tags_not_in(self.unselectable.tags)
                    if own_workers.exists:
                        own_worker: Unit = own_workers.closest_to(enemy_worker)
                        actions.append(own_worker.attack(enemy_worker))
                        self.unselectable.append(own_worker)
                        self.unselectable_enemy_units.append(enemy_worker)























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
            neighbors: Units = army.closer_than(15, unit.position)
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
    
    def get_engagement_prediction(self, army1: Units, army2: Units):
        pass