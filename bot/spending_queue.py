from .priority_queue import PriorityQueue
from sc2 import BotAI

from .data import *

# TODO: Implement a buildorder
class SpendingQueue():
    def __init__(self, bot: BotAI):
        self.spending_queue = PriorityQueue()
        self.bot = bot
    
    def get_spending_queue(self):
        return self.spending_queue
    
    def iterate(self):
        larvae = self.bot.units(LARVA)

        self.update_hatchery_priority()

        if self.need_spawningpool():
            self.spending_queue.reprioritize(SPAWNINGPOOL, 30)

        if self.need_supply(larvae):
            self.spending_queue.reprioritize(OVERLORD, 10)

        if self.need_drone(larvae):
            self.spending_queue.reprioritize(DRONE, 5)

        if self.need_queen():
            self.spending_queue.reprioritize(QUEEN, 21)

    def need_supply(self, larvae) -> bool:
        return self.bot.supply_left < 2 and not self.bot.already_pending(OVERLORD) and self.bot.can_afford(OVERLORD) and larvae.exists

    def need_drone(self, larvae) -> bool:
        return self.bot.can_afford(DRONE) and larvae.exists

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