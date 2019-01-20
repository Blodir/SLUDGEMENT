import json
import operator
import math
import time
import datetime
import copy
import random

from typing import Union
from pathlib import Path

import sc2
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.effect_id import EffectId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2, Point3
from sc2.unit_command import UnitCommand
from sc2.game_data import *
from sc2.data import Race

from .priority_queue import PriorityQueue
from .spending_queue import SpendingQueue
from .unit_manager import UnitManager
from .scouting_manager import ScoutingManager
from .data import *

# Bots are created as classes and they need to have on_step method defined.
# Do not change the name of the class!
class MyBot(sc2.BotAI):
    with open(Path(__file__).parent / "../botinfo.json") as f:
        NAME = json.load(f)["name"]

    def on_start(self):
        self.scouting_manager = ScoutingManager(self)
        self.spending_queue = SpendingQueue(self, self.scouting_manager)
        self.unit_manager = UnitManager(self, self.scouting_manager)

    def _prepare_first_step(self):
        self.expansion_locations
        return super()._prepare_first_step()

    async def on_unit_created(self, unit:Unit):
        # Scout with second ovie
        if unit.type_id == OVERLORD:
            if self.units(OVERLORD).amount == 2:
                positions = []
                if self.enemy_race == Race.Protoss:
                    # Scout for cannon rush
                    positions.append(self.own_natural)
                if self.enemy_race == Race.Terran:
                    # Scout for proxy rax
                    for expansion in self.expansion_locations:
                        if expansion == self.start_location or expansion == self.own_natural:
                            continue
                        if expansion.distance_to(self.start_location) < 50 or expansion.distance_to(self.own_natural) < 50:
                            positions.append(expansion)
                for position in positions:
                    await self.do(unit.move(position, True))

    async def on_unit_destroyed(self, unit_tag):
        # TODO: remove destroyed unit from all control groups

        # remove destroyed unit from scouted units
        self.scouting_manager.remove_observation(unit_tag)
        if self.unit_manager.unselectable.tags_in({unit_tag}).exists:
            self.unit_manager.unselectable = self.unit_manager.unselectable.tags_not_in({unit_tag})
        if self.unit_manager.unselectable_enemy_units.tags_in({unit_tag}).exists:
            self.unit_manager.unselectable_enemy_units = self.unit_manager.unselectable_enemy_units.tags_not_in({unit_tag})
        
        # remove from inject targets
        if unit_tag in list(map(lambda q: q.tag,self.unit_manager.inject_targets.values())):
            to_remove = None
            for hatch in self.unit_manager.inject_targets:
                if self.unit_manager.inject_targets[hatch].tag == unit_tag:
                    to_remove = hatch
            del self.unit_manager.inject_targets[to_remove]

    async def on_building_construction_complete(self, unit: Unit):
        if unit.type_id == EXTRACTOR:
            await self.saturate_gas(unit)

    async def on_step(self, iteration):
        step_start_time = time.time()

        actions = []

        if iteration == 0:
            actions.append(self.units(LARVA).random.train(DRONE))
            await self.do_actions(actions)
            return
        if iteration == 1:
            self.main_minerals = self.get_mineral_fields_for_expansion(self.start_location)

            await self.chat_send("Bow down to your invertebrate overlords")
            return
        if iteration == 2:
            self.enemy_natural = self.calculate_enemy_natural()
            self.own_natural = self.calculate_own_natural()
            actions.append(self.units(OVERLORD).first.move(self.enemy_natural))
            await self.do_actions(actions)
            return

        # SCOUT
        self.scouting_manager.iterate()

        # UPDATE SPENDING QUEUE
        self.spending_queue.iterate()

        # SPEND RESOURCES
        actions.extend(await self.create_spending_actions(self.spending_queue.get_spending_queue()))

        # SET RALLY POINTS
        if math.floor(self.getTimeInSeconds()) % 10 == 0 and self.units(HATCHERY).not_ready.exists:
            for hatch in self.units(HATCHERY).not_ready:
                mineral_field = self.state.mineral_field.closest_to(hatch.position)
                actions.append(hatch(AbilityId.RALLY_HATCHERY_WORKERS, mineral_field))

        # MANAGE ARMY (order matters, manage army before worker redistribution to fix bug with unselectable units)
        actions.extend(await self.unit_manager.iterate(iteration))

        # REDISTRIBUTE WORKERS
        oversaturated_bases = self.units(HATCHERY).filter(lambda h: h.surplus_harvesters > 2)
        if oversaturated_bases.exists:
            await self.distribute_workers()
        elif self.units(DRONE).idle.exists:
            await self.distribute_workers()
        
        # EXECUTE ACTIONS
        await self.do_actions(actions)

        # SEND DEBUG
        # self._client.debug_text_simple(f"Own army value: {self.scouting_manager.own_army_value}")
        # self._client.debug_text_simple(f"Enemy army value: {self.scouting_manager.estimated_enemy_army_value}")
        await self._client.send_debug()

        # PRINT TIME
        execution_time = (time.time() - step_start_time) * 1000
        print(f'Game time: {datetime.timedelta(seconds=math.floor(self.getTimeInSeconds()))}, Iteration: {iteration}, Execution time: {round(execution_time, 3)}ms')

    async def find_building_placement(self, unitId: UnitTypeId) -> Point2 or bool:
        if unitId == HATCHERY:
            return await self.get_next_expansion()
        else:
            if unitId == SPAWNINGPOOL:
                # find placement behind mineral line
                pos = self.start_location + (-5 * self.main_minerals.center.direction_vector(self.start_location))
            else:
                # find placement opposite side of hatch from mineral line
                pos = self.start_location + (5 * self.main_minerals.center.direction_vector(self.start_location))
            return await self.find_placement(unitId, near=pos)

    def getTimeInSeconds(self):
        # returns real time if game is played on "faster"
        return self.state.game_loop * 0.725 * (1/16)

#########################################################################################
#########################################################################################
    async def create_spending_actions(self, priorities: PriorityQueue):
        # TODO: eventually take different stuff like mineral/vesp ratio to consideration
        # eg. if building mutas and lings, you don't want to get stuck at 1k minerals and 0 vespene because mutas are higher priority
        actions = []
        to_remove = []
        minerals_left = self.minerals
        vespene_left = self.vespene
        larvae = self.units(LARVA)
        for p in priorities:
            if minerals_left < 0:
                minerals_left = 0
            if vespene_left < 0:
                vespene_left = 0
            if p == ARMY:
                # make army until no larva remaining
                cost = self.get_resource_value(LING)
                while minerals_left >= cost[0] and vespene_left >= cost[1] and larvae.exists:
                    action = await self.create_construction_action(LING)
                    if action != None:
                        actions.append(action)
                    minerals_left -= cost[0]
                    vespene_left -= cost[1]
            elif p == DRONE:
                # make drone until no larva remaining
                cost = self.get_resource_value(DRONE)
                while minerals_left >= cost[0] and vespene_left >= cost[1] and larvae.exists:
                    action = await self.create_construction_action(DRONE)
                    if action != None:
                        actions.append(action)
                    minerals_left -= cost[0]
                    vespene_left -= cost[1]
            else:
                cost = self.get_resource_value(p)
                if minerals_left >= cost[0] and vespene_left >= cost[1]:
                    action = await self.create_construction_action(p)
                    if action != None:
                        to_remove.append(p)
                        actions.append(action)
                else:
                    #TODO: presend worker
                    pass
                minerals_left -= cost[0]
                vespene_left -= cost[1]
        for p in to_remove:
            # TODO: change logic to change priorities instead of removing stuff from queue in some cases?
            priorities.delete(p)
        return actions;

    # returns None if action could not be done
    async def create_construction_action(self, id: UnitTypeId):
        construction_type = built_by(id)
        if construction_type == ConstructionType.BUILDING:
            worker = self.select_build_worker(self.start_location)
            if worker is None:
                return None
            else:
                structure_position: Union(Point2, Unit)
                if id == EXTRACTOR:
                    for geyser in await self.get_own_geysers():
                        if await self.can_place(EXTRACTOR, geyser.position):
                            structure_position = geyser
                            break
                else:
                    structure_position = await self.find_building_placement(id)
                if structure_position:
                    self.unit_manager.unselectable.append(worker)
                    return worker.build(id, structure_position)
        elif construction_type == ConstructionType.FROM_BUILDING:
            buildingId = get_construction_building(id)
            buildings = self.units(buildingId).ready.noqueue
            if buildings.exists:
                if isinstance(id, UnitTypeId):
                    return buildings.first.train(id)
                if isinstance(id, UpgradeId):
                    return buildings.first.research(id)
        else:
            larvae = self.units(LARVA)
            if larvae.exists:
                return self.units(LARVA).random.train(id)
        return None

    async def get_own_geysers(self) -> Units:
        geysers: Units = Units([], self._game_data)
        for own_expansion in self.owned_expansions:
            for expansion in self.expansion_locations:
                if expansion == own_expansion:
                    for unit in self.expansion_locations[expansion]:
                        if unit.type_id == VESPENE_GEYSER or unit.type_id == SPACEPLATFORMGEYSER:
                            geysers.append(unit)
        return geysers
    
    # returns the amount of drones currently mining minerals
    def get_mineral_saturation(self):
        res = 0
        for own_expansion in self.owned_expansions:
            res += self.owned_expansions[own_expansion].assigned_harvesters
        return res

    async def saturate_gas(self, unit: Unit):
        actions = []
        for drone in self.units(DRONE).closer_than(15, unit.position).take(3):
            actions.append(drone.gather(unit))
        await self.do_actions(actions)

    def queen_already_pending(self) -> int:
        counter = 0
        for hatch in self.units(HATCHERY):
            for order in hatch.orders:
                if order.ability.id == AbilityId.TRAINQUEEN_QUEEN:
                    counter += 1
        return counter

    def get_resource_value(self, id: UnitTypeId) -> (int, int):
        unitData: UnitTypeData = self._game_data.units[id.value]
        return (unitData.cost.minerals, unitData.cost.vespene)
    
    def calculate_combat_value(self, units: Units):
        value = 0
        for unit in units.filter(lambda u: u.can_attack_ground):
            if unit.type_id == DRONE or unit.type_id == UnitTypeId.PROBE or unit.type_id == UnitTypeId.SCV:
                resources = (10, 0)
            else:
                resources = self.get_resource_value(unit.type_id)
            minerals = resources[0]
            vespene = resources[1]
            value += (minerals + vespene)
        return value

    def calculate_enemy_natural(self) -> Point2:
        enemy_base = self.enemy_start_locations[0]
        best = None
        distance = math.inf
        for expansion in self.expansion_locations:
            temp = expansion.distance2_to(enemy_base)
            if temp < distance and temp > 0:
                distance = temp
                best = expansion
        return best

    def calculate_own_natural(self) -> Point2:
        best = None
        distance = math.inf
        for expansion in self.expansion_locations:
            temp = expansion.distance2_to(self.start_location)
            if temp < distance and temp > 0:
                distance = temp
                best = expansion
        return best
    
    def closest_mining_expansion_location(self, position) -> Point2:
        mining_bases: Units = self.units(HATCHERY).filter(lambda h: h.assigned_harvesters > 4)
        if mining_bases.exists:
            base: Unit = mining_bases.closest_to(position)
            return base.position
        return self.start_location
    
    def get_mineral_fields_for_expansion(self, expansion_position: Point2) -> Units:
        mins: Units = Units([], self._game_data)
        for unit in self.expansion_locations[expansion_position]:
            if unit.mineral_contents > 0:
                mins.append(unit)
        return mins
    
    async def find_tumor_placement(self) -> Point2:
        # TODO: SLOW function fix fix fix. Also doesn't take into consideration whether theres something blocking tumor or not
        creep_emitters: Units = self.units({HATCHERY, UnitTypeId.CREEPTUMORBURROWED})
        while True:
            target_emitter: Unit = creep_emitters.random
            target_position: Point2 = target_emitter.position + (9 * Point2((-1 + 2 * random.random(), -1 + 2 * random.random())))
            check = True
            for emitter in creep_emitters:
                if target_position.distance_to(emitter.position) < 9:
                    check = False
                    break
            if check:
                return target_position