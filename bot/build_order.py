from sc2 import BotAI
from .data import *

class BuildOrder():
    def __init__(self, bot: BotAI):
        self.bot = bot
        self.iteration = 0
    
    def standard(self):
        priorities = []
        priorities.append((DRONE, 5))
        if self.bot.supply_used >= 13 and self.iteration == 0:
            priorities.append((OVERLORD, 50))
            self.iteration += 1
        elif self.bot.supply_used >= 17 and self.iteration == 1:
            priorities.append((HATCHERY, 50))
            self.iteration += 1
        elif self.bot.supply_used >= 18 and self.iteration == 2:
            priorities.append((EXTRACTOR, 50))
            self.iteration += 1
        elif self.bot.supply_used >= 17 and self.iteration == 3:
            priorities.append((SPAWNINGPOOL, 50))
            self.iteration += 1
        elif self.bot.supply_used >= 19 and self.iteration == 4:
            priorities.append((OVERLORD, 50))
            self.iteration += 1
        return priorities