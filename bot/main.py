import json
import operator
import math
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

from .priority_queue import PriorityQueue

LARVA = UnitTypeId.LARVA
OVERLORD = UnitTypeId.OVERLORD
DRONE = UnitTypeId.DRONE
HATCHERY = UnitTypeId.HATCHERY
SPAWNINGPOOL = UnitTypeId.SPAWNINGPOOL
QUEEN = UnitTypeId.QUEEN

# Larva per minute from an injected hatch
LARVA_RATE_PER_INJECT = 11.658

# Bots are created as classes and they need to have on_step method defined.
# Do not change the name of the class!
class MyBot(sc2.BotAI):
    with open(Path(__file__).parent / "../botinfo.json") as f:
        NAME = json.load(f)["name"]

    # On_step method is invoked each game-tick and should not take more than
    # 2 seconds to run, otherwise the bot will timeout and cannot receive new
    # orders.
    # It is important to note that on_step is asynchronous - meaning practices
    # for asynchronous programming should be followed.
    async def on_step(self, iteration):
        spending_queue = PriorityQueue()
        actions = []
        larvae = self.units(LARVA)
        allocated_resources = (0, 0)

        if self.need_spawningpool():
            spending_queue.enqueue(SPAWNINGPOOL, 30)

        if self.need_hatchery():
            spending_queue.enqueue(HATCHERY, 20)
        
        if self.need_supply(larvae):
            spending_queue.enqueue(OVERLORD, 10)

        if self.need_drone(larvae):
            spending_queue.enqueue(DRONE, 5)

        if self.need_queen():
            spending_queue.enqueue(QUEEN, 21)
        
        # loop over the spending queue
        # break the loop if at any point we have allocated more resources than currently available
        while not spending_queue.isEmpty():
            unitId: UnitTypeId = spending_queue.dequeue()[0]
            allocated_resources = tuple(map(operator.add, allocated_resources, self.get_resource_value(unitId)))
            if (allocated_resources[0] > self.minerals or allocated_resources[1] > self.vespene):
                break
            if self.is_structure(unitId):
                main_pos = self.start_location
                worker = self.select_build_worker(main_pos)
                if worker is None:
                    break
                else:
                    structure_position = await self.find_building_placement(unitId, main_pos)
                    actions.append(worker.build(unitId, structure_position))
            elif self.is_built_from_building(unitId):
                hatches = self.units(HATCHERY).ready.noqueue
                if hatches.exists:
                    actions.append(hatches.first.train(unitId))
            else:
                actions.append(larvae.random.train(unitId))

        actions.extend(await self.inject())

        await self.do_actions(actions)

        if iteration == 0:
            await self.chat_send(f"Name: {self.NAME}")

    def need_supply(self, larvae) -> bool:
        return self.supply_left < 2 and not self.already_pending(OVERLORD) and self.can_afford(OVERLORD) and larvae.exists

    def need_drone(self, larvae) -> bool:
        return self.can_afford(DRONE) and larvae.exists

    def need_hatchery(self) -> bool:
        return self.units(DRONE).amount > (self.units(HATCHERY).amount * LARVA_RATE_PER_INJECT) and not self.already_pending(HATCHERY)

    def need_spawningpool(self) -> bool:
        return not self.units(SPAWNINGPOOL).owned.exists

    def need_queen(self) -> bool:
        return self.units(SPAWNINGPOOL).owned.exists and (self.units(HATCHERY).amount > self.units(QUEEN).amount)

    def get_resource_value(self, unitId: UnitTypeId) -> (int, int):
        if unitId == HATCHERY:
            return (300, 0)
        if unitId == DRONE:
            return (50, 0)
        if unitId == OVERLORD:
            return (100, 0)
        if unitId == QUEEN:
            return (150, 0)
        return (0, 0)
    
    def is_structure(self, unitId: UnitTypeId) -> bool:
        if unitId == HATCHERY:
            return True
        if unitId == SPAWNINGPOOL:
            return True
        return False

    def is_built_from_building(self, unitId: UnitTypeId) -> bool:
        if unitId == QUEEN:
            return True
        return False

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

    async def find_building_placement(self, unitId: UnitTypeId, main_pos) -> Point2:
        if unitId == HATCHERY:
            return await self.next_expansion_location()
        else:
            return await self.find_placement(unitId, near=main_pos)
    
    async def next_expansion_location(self) -> Point2:
        res: Point2 = self.start_location
        best = math.inf
        for idx, key in enumerate(self.expansion_locations):
            distance = key.distance_to(self.start_location)
            can_place = await self.can_place(HATCHERY, key)
            if distance < best and can_place:
                best = distance
                res = key
        return res