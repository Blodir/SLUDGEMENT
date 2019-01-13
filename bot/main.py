import json
import operator
import math
import time
import datetime
import copy

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
from sc2.position import Point2
from sc2.unit_command import UnitCommand
from sc2.game_data import *

from .priority_queue import PriorityQueue
from .spending_queue import SpendingQueue
from .unit_manager import UnitManager
from .scouting_manager import ScoutingManager
from .coroutine_switch import CoroutineSwitch
from .data import *
from .util import *

# Bots are created as classes and they need to have on_step method defined.
# Do not change the name of the class!
class MyBot(sc2.BotAI):
    with open(Path(__file__).parent / "../botinfo.json") as f:
        NAME = json.load(f)["name"]

    def on_start(self):
        self.scouting_manager = ScoutingManager(self)
        self.spending_queue = SpendingQueue(self, self.scouting_manager)
        self.unit_manager = UnitManager(self)

    def _prepare_first_step(self):
        self.expansion_locations
        return super()._prepare_first_step()

    async def on_building_construction_complete(self, unit: Unit):
        if unit.type_id == EXTRACTOR:
            await self.saturate_gas(unit)

    async def on_step(self, iteration):
        step_start_time = time.time()

        # WARM UP for 10 iterations to avoid timeout
        if iteration == 0:
            await self.chat_send(f"Name: {self.NAME}")

        actions = []

        # SCOUT
        self.scouting_manager.iterate()

        # UPDATE SPENDING QUEUE
        self.spending_queue.iterate()

        # SPEND RESOURCES
        actions.extend(await self.create_spending_actions(self.spending_queue.get_spending_queue()))

        # INJECT
        actions.extend(await self.inject())

        # SET RALLY POINTS
        if math.floor(self.getTimeInSeconds()) % 10 == 0 and self.units(HATCHERY).not_ready.exists:
            for hatch in self.units(HATCHERY).not_ready:
                mineral_field = self.state.mineral_field.closest_to(hatch.position)
                actions.append(hatch(AbilityId.RALLY_HATCHERY_WORKERS, mineral_field))

        # REDISTRIBUTE WORKERS
        for hatch in self.units(HATCHERY):
            if hatch.surplus_harvesters > 4:
                await self.distribute_workers()
                break
        
        # MANAGE ARMY
        actions.extend(self.unit_manager.iterate())

        # EXECUTE ACTIONS
        await self.do_actions(actions)

        # PRINT TIME
        print(f'Game time: {datetime.timedelta(seconds=math.floor(self.getTimeInSeconds()))}')
        execution_time = (time.time() - step_start_time) * 1000
        print(f'{iteration} : {round(execution_time, 3)}ms')

    async def inject(self):
        ready_queens = []
        actions = []
        for queen in self.units(QUEEN).idle:
            abilities = await self.get_available_abilities(queen)
            if AbilityId.EFFECT_INJECTLARVA in abilities:
                ready_queens.append(queen)
        for queen in ready_queens:
            actions.append(queen(AbilityId.EFFECT_INJECTLARVA, self.units(HATCHERY).first))
        return actions

    async def find_building_placement(self, unitId: UnitTypeId, main_pos) -> Point2 or bool:
        if unitId == HATCHERY:
            return await self.get_next_expansion()
        else:
            return await self.find_placement(unitId, near=main_pos)

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
        for p in priorities:
            cost = self.get_resource_value(p)
            if minerals_left < 0:
                minerals_left = 0
            if vespene_left < 0:
                vespene_left = 0
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
            main_pos = self.start_location
            worker = self.select_build_worker(main_pos)
            if worker is None:
                return None
            else:
                structure_position: Union(Point2, Unit)
                if id == EXTRACTOR:
                    for geyser in await self.get_own_geysers():
                        if await self.can_place(EXTRACTOR, geyser.position):
                            structure_position = geyser
                else:
                    structure_position = await self.find_building_placement(id, main_pos)
                if structure_position:
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

    async def get_own_geysers(self):
        geysers = []
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
    