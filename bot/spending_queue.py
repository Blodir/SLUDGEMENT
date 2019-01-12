from .priority_queue import PriorityQueue
from sc2 import BotAI

from .data import *

# TODO: Turn into singleton
class SpendingQueue():
    def __init__(self, bot: BotAI):
        self.spending_queue = PriorityQueue()
        self.bot = bot
    
    def get_spending_queue(self):
        return self.spending_queue
    
    def iterate(self):
        larvae = self.bot.units(LARVA)
        if self.need_spawningpool():
            self.spending_queue.enqueue(SPAWNINGPOOL, 30)

        if self.need_hatchery():
            self.spending_queue.enqueue(HATCHERY, 20)
        
        if self.need_supply(larvae):
            self.spending_queue.enqueue(OVERLORD, 10)

        if self.need_drone(larvae):
            self.spending_queue.enqueue(DRONE, 5)

        if self.need_queen():
            self.spending_queue.enqueue(QUEEN, 21)

    def need_supply(self, larvae) -> bool:
        return self.bot.supply_left < 2 and not self.bot.already_pending(OVERLORD) and self.bot.can_afford(OVERLORD) and larvae.exists

    def need_drone(self, larvae) -> bool:
        return self.bot.can_afford(DRONE) and larvae.exists

    def need_hatchery(self) -> bool:
        return self.bot.units(DRONE).amount > (self.bot.units(HATCHERY).amount * LARVA_RATE_PER_INJECT) and not self.bot.already_pending(HATCHERY)

    def need_spawningpool(self) -> bool:
        return not self.bot.units(SPAWNINGPOOL).exists

    def need_queen(self) -> bool:
        return self.bot.units(SPAWNINGPOOL).exists and (self.bot.units(HATCHERY).amount > self.bot.units(QUEEN).amount)