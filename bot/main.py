import json
import operator
import math
import time
import datetime

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

from .priority_queue import PriorityQueue
from .spending_queue import SpendingQueue
from .coroutine_switch import CoroutineSwitch
from .data import *
from .util import *

# Bots are created as classes and they need to have on_step method defined.
# Do not change the name of the class!
class MyBot(sc2.BotAI):
    with open(Path(__file__).parent / "../botinfo.json") as f:
        NAME = json.load(f)["name"]

    def on_start(self):
        self.spending_queue = SpendingQueue(self)

    async def on_step(self, iteration):
        step_start_time = time.time()

        # WARM UP for 10 iterations to avoid timeout
        if iteration == 0:
            await self.chat_send(f"Name: {self.NAME}")
            await self.do(self.units(LARVA).random.train(DRONE))
            return;
        elif iteration == 1:
            # warm up expansion location cache
            self.expansion_locations
            return;
        elif iteration in range(2, 10):
            return;

        actions = []

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
        resources_left = (self.minerals, self.vespene)
        for p in priorities:
            cost = get_resource_value(p)
            if resources_left[0] >= cost[0] and resources_left[1] >= cost[1]:
                action = await self.create_construction_action(p)
                if action != None:
                    to_remove.append(p)
                    actions.append(action)
            else:
                #TODO: presend worker
                pass
            # reduce resources_left whether we built the unit or not (ensure that we have more resources in the future)
            resources_left = tuple_sub(resources_left, cost)
        for p in to_remove:
            # TODO: change logic to change priorities instead of removing stuff from queue in some cases?
            priorities.dequeue()
        return actions;

    # returns None if action could not be done
    async def create_construction_action(self, unitId: UnitTypeId):
        construction_type = built_by(unitId)
        if construction_type == ConstructionType.BUILDING:
            main_pos = self.start_location
            worker = self.select_build_worker(main_pos)
            if worker is None:
                return None
            else:
                structure_position: Union(Point2, Unit)
                if unitId == EXTRACTOR:
                    for geyser in await self.get_own_geysers():
                        if await self.can_place(EXTRACTOR, geyser.position):
                            structure_position = geyser
                else:
                    structure_position = await self.find_building_placement(unitId, main_pos)
                if structure_position:
                    return worker.build(unitId, structure_position)
        elif construction_type == ConstructionType.FROM_BUILDING:
            hatches = self.units(HATCHERY).ready.noqueue
            if hatches.exists:
                return hatches.first.train(unitId)
        else:
            larvae = self.units(LARVA)
            if larvae.exists:
                return self.units(LARVA).random.train(unitId)
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