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
            priorities.append((OVERLORD, 51))
            self.iteration += 1
        elif self.bot.supply_used >= 17 and self.iteration >= 1 and not self.bot.already_pending(HATCHERY) and not self.bot.units(HATCHERY).amount > 1:
            priorities.append((HATCHERY, 50))
            self.iteration += 1
        elif self.bot.supply_used >= 18 and self.iteration >= 2 and not self.bot.already_pending(EXTRACTOR) and not self.bot.units(EXTRACTOR).exists:
            priorities.append((EXTRACTOR, 49))
            self.iteration += 1
        elif self.bot.supply_used >= 17 and self.iteration >= 3 and not self.bot.already_pending(SPAWNINGPOOL) and not self.bot.units(SPAWNINGPOOL).exists and self.bot.units(EXTRACTOR).exists:
            priorities.append((SPAWNINGPOOL, 48))
            self.iteration += 1
        elif self.bot.supply_used >= 19 and self.iteration >= 4 and not self.bot.already_pending(OVERLORD) and not self.bot.units(OVERLORD).amount > 1:
            priorities.append((OVERLORD, 47))
            self.iteration += 1
        return priorities