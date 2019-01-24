from typing import List, Union, Dict
import math
import random

from sc2 import BotAI
from sc2.client import Race
from sc2.units import Units
from sc2.unit import Unit
from sc2.ids.ability_id import AbilityId
from sc2.unit_command import UnitCommand
from sc2.position import Point2, Point3, Rect
from sc2.pixel_map import PixelMap

from .scouting_manager import ScoutingManager

from .data import *

class UnitManager():

    def __init__(self, bot: BotAI, scouting_manager: ScoutingManager):
        self.bot = bot
        self.scouting_manager = scouting_manager
        self.unselectable = Units([], self.bot._game_data)
        self.unselectable_enemy_units = Units([], self.bot._game_data)
        self.scouting_ttl = 300
        self.inject_targets: Dict[Unit, Unit] = {}
        self.inject_queens: Units = Units([], self.bot._game_data)

    async def iterate(self, iteration):
        self.scouting_ttl -= 1

        actions: List[UnitCommand] = []

        all_army: Units = self.bot.units.exclude_type({OVERLORD, DRONE, QUEEN, LARVA, EGG}).not_structure.ready
        observed_enemy_army = self.scouting_manager.observed_enemy_units.filter(lambda u: u.can_attack_ground)
        estimated_enemy_value = self.scouting_manager.estimated_enemy_army_value

        army_units = all_army

        for observed_enemy in observed_enemy_army:
            pos = observed_enemy.position
            self.bot._client.debug_text_world(f'observed', Point3((pos.x, pos.y, 10)), None, 12)

        # ASSIGN INJECT QUEENS
        # TODO: DONT DO THIS IF ENEMIES CLOSEBY
        hatches = self.bot.find_closest_n_from_units(self.bot.start_location, 4, self.bot.units(HATCHERY)).ready.tags_not_in(set(map(lambda h: h.tag, self.inject_targets.keys())))
        for hatch in hatches:
            free_queens: Units = self.bot.units(QUEEN).tags_not_in(self.unselectable.tags).tags_not_in(self.inject_queens.tags)
            if free_queens.exists:
                queen = free_queens.random
                self.inject_targets[hatch] = queen
                self.inject_queens.append(queen)
        
        # INJECT
        for hatch in self.inject_targets:
            if self.bot.known_enemy_units.closer_than(15, hatch).exists:
                continue
            inject_queen = self.inject_targets[hatch]
            if inject_queen:
                try:
                    abilities = await self.bot.get_available_abilities(inject_queen)
                    if abilities and len(abilities) > 0 and AbilityId.EFFECT_INJECTLARVA in abilities:
                        actions.append(inject_queen(AbilityId.EFFECT_INJECTLARVA, hatch))
                    else:
                        # move to hatch
                        pass
                except:
                    print('inject error')
            else:
                del self.inject_targets[hatch]

        # SCOUTING

        if army_units(LING).exists and self.scouting_ttl < 0 and self.scouting_manager.enemy_raiders_value == 0:
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


        # KILL TERRAN BUILDINGS WITH MUTAS
        if self.scouting_manager.terran_floating_buildings:
            mutas: Units = self.bot.units(MUTALISK).tags_not_in(self.unselectable.tags)
            pos: Point2 = self.bot.enemy_start_locations[0] + 15 * self.bot._game_info.map_center.direction_vector(self.bot.enemy_start_locations[0])
            corners = [
                Point2((0, 0)),
                Point2((self.bot._game_info.pathing_grid.width - 1, 0)),
                Point2((self.bot._game_info.pathing_grid.width - 1, self.bot._game_info.pathing_grid.height - 1)),
                Point2((0,self.bot._game_info.pathing_grid.height- 1)),
                Point2((0, 0))
            ]
            for muta in mutas:
                for corner in corners:
                    actions.append(muta.attack(corner, True))
                self.unselectable.append(muta)

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

                    # ling micro
                    microing_back_tags: List[int] = []
                    if nearby_enemies(LING).exists:
                        for unit in group(LING):
                            local_enemies: Units = nearby_enemies.closer_than(3, unit.position)
                            local_allies: Units = group.closer_than(3, unit.position)
                            # TODO: use attack range instead of proximity... (if enemies cant attack they arent a threat)
                            if (self.bot.calculate_combat_value(local_enemies) 
                                > self.bot.calculate_combat_value(local_allies)
                            ):
                                target = unit.position + 5 * local_enemies.center.direction_vector(group.center)
                                actions.append(unit.move(target))
                                microing_back_tags.append(unit.tag)
                                self.bot._client.debug_text_world(f'micro point', Point3((target.x, target.y, 10)), None, 12)
                                self.bot._client.debug_text_world(f'microing back', Point3((unit.position.x, unit.position.y, 10)), None, 12)
                    actions.extend(self.command_group(group.tags_not_in(set(microing_back_tags)), AbilityId.ATTACK, nearby_enemies.center))
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
                        if enemy_value > 150:
                            everything = self.bot.units.closer_than(15, group.center)
                            self.unselectable.extend(everything)
                        everything = everything + self.bot.units(QUEEN)
                        actions.extend(self.command_group(everything, AbilityId.ATTACK, nearby_enemies.center))
                        self.bot._client.debug_text_world(f'last resort', Point3((group.center.x, group.center.y, 10)), None, 12)
                    else:
                        # TODO: dont retreat if too close to enemy
                        actions.extend(self.command_group(group, AbilityId.MOVE, move_position))
                        self.bot._client.debug_text_world(f'retreating', Point3((group.center.x, group.center.y, 10)), None, 12)
            else:
                if group_value > 1.2 * estimated_enemy_value or self.bot.supply_used >= 180:
                    # attack toward closest enemy buildings
                    attack_position = self.bot.enemy_start_locations[0]
                    observed_structures = self.scouting_manager.observed_enemy_units.structure
                    if observed_structures.exists:
                        attack_position = observed_structures.closest_to(group.center).position
                    if self.scouting_manager.observed_enemy_units.exists:
                        target_enemy_units: Units = self.scouting_manager.observed_enemy_units.filter(lambda u: u.can_attack_ground)
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

        # DRONE DEFENSE
        for expansion in self.bot.owned_expansions:
            enemy_raid: Units = observed_enemy_army.closer_than(10, expansion)
            if enemy_raid.exists:
                raid_value = self.bot.calculate_combat_value(enemy_raid)
                defending_army: Units = all_army.closer_than(15, expansion)
                if raid_value > self.bot.calculate_combat_value(defending_army.exclude_type({DRONE})):
                    for defender in self.bot.units(DRONE).closer_than(10, expansion).tags_not_in(self.unselectable.tags):
                        pos = defender.position
                        if expansion != self.bot.start_location:
                            self.bot._client.debug_text_world(f'mineral walking', Point3((pos.x, pos.y, 10)), None, 12)
                            actions.append(defender.gather(self.bot.main_minerals.random))
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

        if self.bot.enemy_race == Race.Protoss:
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

        # EXTRA QUEEN CONTROL
        extra_queens = self.bot.units(QUEEN).tags_not_in(self.unselectable.tags)
        # if there's a fight contribute otherwise make creep tumors
        if extra_queens.exists:
            if self.bot.known_enemy_units.exists and self.bot.units.closer_than(20, extra_queens.center).tags_not_in(extra_queens.tags).filter(lambda u: u.is_attacking).exists and self.bot.known_enemy_units.closer_than(20, extra_queens.center).exists:
                actions.extend(self.command_group(extra_queens, AbilityId.ATTACK, self.bot.known_enemy_units.closest_to(extra_queens.center).position))
                self.bot._client.debug_text_world(f'queen attack', Point3((extra_queens.center.x, extra_queens.center.y, 10)), None, 12)
            else:
                for queen in extra_queens.tags_not_in(self.inject_queens.tags):
                    if queen.is_idle:
                        abilities = await self.bot.get_available_abilities(queen)
                        position = await self.bot.find_tumor_placement()
                        if AbilityId.BUILD_CREEPTUMOR_QUEEN in abilities and position and self.bot.has_creep(position):
                            actions.append(queen(AbilityId.BUILD_CREEPTUMOR, position))
                            self.unselectable.append(queen)
                        else:
                            if queen.position.distance_to(extra_queens.center) > 2:
                                # regroup extra queens
                                actions.append(queen.move(extra_queens.center))

        # CREEP TUMORS
        for tumor in self.bot.units(UnitTypeId.CREEPTUMORBURROWED):
            # TODO: direct creep spread to some direction...
            # Dont overmake creep xd
            # TODO: Dont block hatch positions
            abilities = await self.bot.get_available_abilities(tumor)
            angle = random.randint(0, 360)
            x = math.cos(angle)
            y = math.sin(angle)
            position: Point2 = tumor.position + (9 * Point2((x, y)))
            if not self.bot.units(UnitTypeId.CREEPTUMORBURROWED).closer_than(9, position).exists and not self.bot.position_blocks_expansion(position):
                if AbilityId.BUILD_CREEPTUMOR_TUMOR in abilities:
                    actions.append(tumor(AbilityId.BUILD_CREEPTUMOR, position))


















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
    
    async def inject(self):
        ready_queens = []
        actions = []
        for queen in self.bot.units(QUEEN).idle:
            abilities = await self.bot.get_available_abilities(queen)
            if AbilityId.EFFECT_INJECTLARVA in abilities:
                ready_queens.append(queen)
        for queen in ready_queens:
            actions.append(queen(AbilityId.EFFECT_INJECTLARVA, self.bot.units(HATCHERY).first))
        return actions
