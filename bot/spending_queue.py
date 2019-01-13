from .priority_queue import PriorityQueue
from sc2 import BotAI

from .data import *
from .build_order import BuildOrder

# TODO: Implement a buildorder
class SpendingQueue():
    def __init__(self, bot):
        self.spending_queue = PriorityQueue()
        self.bot = bot
        self.build = BuildOrder(bot)
    
    def get_spending_queue(self):
        return self.spending_queue
    
    def iterate(self):
        if self.bot.supply_used < 21:
            bo_priorities = self.build.standard()
            for p in bo_priorities:
                self.spending_queue.reprioritize(p[0], p[1])
            if self.need_queen():
                self.spending_queue.reprioritize(QUEEN, 21)
        else:
            self.update_hatchery_priority()

            if self.need_spawningpool():
                self.spending_queue.reprioritize(SPAWNINGPOOL, 30)

            if self.need_supply():
                self.spending_queue.reprioritize(OVERLORD, 10)

            if self.need_drone():
                self.spending_queue.reprioritize(DRONE, 5)

            if self.need_queen():
                self.spending_queue.reprioritize(QUEEN, 21)

    def need_supply(self) -> bool:
        if self.supply_cap >= 200:
            return false
        mineral_saturation = self.bot.get_mineral_saturation()
        mineral_income = mineral_saturation * DRONE_MINERALS_PER_SECOND
        overlords_in_progress = self.bot.already_pending(OVERLORD)
        mineral_cost = 50
        supply_cost = 1
        overlord_buildtime = 18
        time_until_supplyblock = (self.bot.supply_left + (overlords_in_progress * 8)) / (supply_cost / mineral_cost * mineral_income)
        return time_until_supplyblock < overlord_buildtime

    def need_drone(self) -> bool:
        return self.bot.can_afford(DRONE)

    def need_hatchery(self) -> bool:
        return self.bot.units(DRONE).amount > (self.bot.units(HATCHERY).amount * LARVA_RATE_PER_INJECT) and not self.bot.already_pending(HATCHERY)

    def need_spawningpool(self) -> bool:
        return not self.bot.units(SPAWNINGPOOL).exists and not self.bot.already_pending(SPAWNINGPOOL)

    def need_queen(self) -> bool:
        return self.bot.units(SPAWNINGPOOL).exists and (self.bot.units(HATCHERY).amount > self.bot.units(QUEEN).amount)
    
    def update_hatchery_priority(self):
        if self.need_hatchery():
            self.spending_queue.reprioritize(HATCHERY, 20)
        else:
            self.spending_queue.reprioritize(HATCHERY, 4)