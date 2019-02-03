from typing import List, Union, Dict
import math
import random
import time

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
        self.army_scouting_ttl = 100
        self.panic_scout_ttl = 0
        self.inject_targets: Dict[Unit, Unit] = {}
        self.inject_queens: Units = Units([], self.bot._game_data)
        self.dead_tumors: Units = Units([], self.bot._game_data)
        self.spread_overlords: Units = Units([], self.bot._game_data)

    async def iterate(self, iteration):
        self.scouting_ttl -= 1

        actions: List[UnitCommand] = []

        all_army: Units = self.bot.units.exclude_type({OVERLORD, DRONE, QUEEN, LARVA, EGG}).not_structure.ready
        observed_enemy_army = self.scouting_manager.observed_enemy_units.filter(lambda u: u.can_attack_ground or u.type_id == UnitTypeId.BUNKER)
        estimated_enemy_value = self.scouting_manager.estimated_enemy_army_value

        army_units = all_army

        for observed_enemy in observed_enemy_army:
            pos = observed_enemy.position
            self.bot._client.debug_text_world(f'observed', Point3((pos.x, pos.y, 10)), None, 12)

        # ASSIGN INJECT QUEENS
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

        # army scout only if opponent army has not been close for a while
        if not observed_enemy_army.closer_than(70, self.bot.own_natural).amount > 2:
            self.army_scouting_ttl -= 1
        else:
            self.army_scouting_ttl = 60

        if self.army_scouting_ttl <= 0 and army_units(LING).exists:
            self.army_scouting_ttl = 60
            unit: Unit = army_units(LING).random
            actions.append(unit.move(self.bot.enemy_start_locations[0]))
            self.unselectable.append(unit)
        
        # panic scout main if drone difference gets high enough
        if self.bot.already_pending(DRONE) + self.bot.units(DRONE).amount > 25 * self.scouting_manager.enemy_townhall_count:
            if self.panic_scout_ttl <= 0:
                if self.bot.units(OVERLORD).exists:
                    print('panic scouting')
                    closest_overlord = self.bot.units(OVERLORD).tags_not_in(self.unselectable.tags).closest_to(self.bot.enemy_start_locations[0])
                    original_position = closest_overlord.position
                    actions.append(closest_overlord.stop())
                    actions.append(closest_overlord.move(self.bot.enemy_start_locations[0], True))
                    actions.append(closest_overlord.move(original_position, True))
                    self.unselectable.append(closest_overlord)
                    self.panic_scout_ttl = 300
            else:
                self.panic_scout_ttl -= 1



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

        self.spread_overlords = self.bot.units.tags_in(self.spread_overlords.tags)
        for overlord in self.spread_overlords:
            self.bot._client.debug_text_world(f'spread', Point3((overlord.position.x,overlord.position.y, 10)), None, 12)

        groups_start_time = time.time()
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
                bias = 1
                if nearby_enemies.closer_than(15, self.bot.own_natural).exists and group_value > 750:
                    bias = 1.2
                if self.bot.supply_used > 180:
                    bias = 1.5
                should_engage: bool = self.evaluate_engagement(self.bot.units.exclude_type({DRONE, OVERLORD}).closer_than(20, nearby_enemies.center), nearby_enemies, bias) > 0
                if should_engage:
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
                    
                    if nearby_enemies.exclude_type({UnitTypeId.CHANGELINGZERGLING, UnitTypeId.CHANGELING, UnitTypeId.CHANGELINGZERGLINGWINGS}).exists:
                        actions.extend(self.command_group(group.tags_not_in(set(microing_back_tags)), AbilityId.ATTACK, nearby_enemies.center))
                    else:
                        actions.extend(self.command_group(group, AbilityId.ATTACK, nearby_enemies.closest_to(group.center)))
                    self.bot._client.debug_text_world(f'attacking group', Point3((group.center.x,group.center.y, 10)), None, 12)
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
        execution_time = (time.time() - groups_start_time) * 1000
        #print(f'//// Groups: {round(execution_time, 3)}ms')

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

        extra_queen_start_time = time.time()
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
        execution_time = (time.time() - extra_queen_start_time) * 1000
        #print(f'//// Extra queens: {round(execution_time, 3)}ms')

        creep_start_time = time.time()
        # CREEP TUMORS
        for tumor in self.bot.units(UnitTypeId.CREEPTUMORBURROWED).tags_not_in(self.dead_tumors.tags):
            # TODO: direct creep spread to some direction...
            # Dont overmake creep xd
            abilities = await self.bot.get_available_abilities(tumor)
            if AbilityId.BUILD_CREEPTUMOR_TUMOR in abilities:
                angle = random.randint(0, 360)
                x = math.cos(angle)
                y = math.sin(angle)
                position: Point2 = tumor.position + (9 * Point2((x, y)))
                if self.bot.has_creep(position) and not self.bot.units(UnitTypeId.CREEPTUMORBURROWED).closer_than(9, position).exists and not self.bot.position_blocks_expansion(position):
                    actions.append(tumor(AbilityId.BUILD_CREEPTUMOR, position))
                    self.dead_tumors.append(tumor)
        execution_time = (time.time() - creep_start_time) * 1000
        #print(f'//// Creep: {round(execution_time, 3)}ms')

        # OVERLORD retreat from enemy structures and anti air stuff
        for overlord in self.bot.units(OVERLORD).tags_not_in(self.unselectable.tags):
            threats: Units = self.bot.known_enemy_units.filter(lambda u: u.is_structure or u.can_attack_air).closer_than(10, overlord) 
            if threats.exists:
                destination: Point2 = overlord.position + 2 * threats.center.direction_vector(overlord.position)
                actions.append(overlord.move(destination))


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

    def evaluate_engagement(self, own_units: Units, enemy_units: Units, bias = 1):
        own_ranged: Units = own_units.filter(lambda u: u.ground_range > 3)
        own_melee: Units = own_units.tags_not_in(own_ranged.tags)
        enemy_ranged: Units = enemy_units.filter(lambda u: u.ground_range > 3)
        
        try:
            own_ranged_value = bias * self.bot.calculate_combat_value(own_ranged)
        except:
            own_ranged_value = 0
        try:
            enemy_ranged_value = self.bot.calculate_combat_value(enemy_ranged)
        except:
            enemy_ranged_value = 0

        corrected_own_value = bias * self.bot.calculate_combat_value(own_units)

        if own_ranged_value < enemy_ranged_value and own_units.exists:
            perimeter = self.get_enemy_perimeter(enemy_units.not_structure, self.bot.known_enemy_structures, own_units.center)
            if own_melee.exists:
                own_melee_value = bias * self.bot.calculate_combat_value(Units(own_melee.take(perimeter * 2, require_all=False), self.bot._game_data))
            else:
                own_melee_value = 0
            corrected_own_value = own_melee_value + own_ranged_value
        evaluation = corrected_own_value - self.bot.calculate_combat_value(enemy_units)
        return evaluation 
    
    def get_enemy_perimeter(self, enemy_units: Units, enemy_structures: Units, reference_position: Point2):
        perimeter = 0
        pathing_grid: PixelMap = self.bot._game_info.pathing_grid
        for enemy_unit in enemy_units:
            enemies_excluding_self: Units = enemy_units.tags_not_in({enemy_unit.tag})
            pos: Point2 = enemy_unit.position
            positions = [
                Point2((pos.x-1, pos.y+1)),
                Point2((pos.x, pos.y+1)),
                Point2((pos.x+1, pos.y+1)),
                Point2((pos.x-1, pos.y)),
                # [pos.x, pos.y], disregard center point
                Point2((pos.x+1, pos.y)),
                Point2((pos.x-1, pos.y-1)),
                Point2((pos.x, pos.y-1)),
                Point2((pos.x+1, pos.y-1)),
            ]
            if reference_position.distance_to(enemy_unit.position) > 5:
                positions = remove_n_furthest_points(positions, reference_position, 3)
            for p in positions:
                if pathing_grid[math.floor(p.x), math.floor(p.y)] <= 0 and not enemies_excluding_self.closer_than(1, p).exists and not enemy_structures.closer_than(1, p).exists:
                    perimeter += 1
        return perimeter
    
def remove_n_furthest_points(points: List[Point2], reference, n):
    def sort(p: Point2):
        return p.distance_to(reference)
    points.sort(reverse = True, key = sort)
    for i in range(n):
        points.pop(0)
    return points