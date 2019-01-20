from typing import List, Tuple

from sc2 import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from .data import *

class BOStep():
    def __init__(self, condition, unit: UnitTypeId):
        self.condition = condition
        self.unit_id: UnitTypeId = unit
    def try_condition(self) -> bool:
        return self.condition()

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
    
    def pool_first(self) -> List[BOStep]:
        return [
            (BOStep(lambda: self.bot.supply_used >= 13, OVERLORD)),
            (BOStep(lambda: self.bot.supply_used >= 16, SPAWNINGPOOL)),
            (BOStep(lambda: self.bot.supply_used >= 17, HATCHERY)),
            (BOStep(lambda: self.bot.supply_used >= 18, EXTRACTOR)),
            (BOStep(lambda: self.bot.supply_used >= 19, LING)),
        ]
    
    def hatch_first(self) -> List[BOStep]:
        return [
            (BOStep(lambda: self.bot.supply_used >= 13, OVERLORD)),
            (BOStep(lambda: self.bot.supply_used >= 17, HATCHERY)),
            (BOStep(lambda: self.bot.supply_used >= 18, EXTRACTOR)),
            (BOStep(lambda: self.bot.supply_used >= 17, SPAWNINGPOOL)),
            (BOStep(lambda: self.bot.supply_used >= 19, OVERLORD))
        ]

class BuildOrderRunner():
    def __init__(self, bot, build_order: List[BOStep]):
        self.bot = bot
        self.state: int = 0
        self.build_ended = False
        self.steps: List[BOStep] = build_order
    def iterate(self) -> List[Tuple[UnitTypeId, int]]:
        build_priorities = []
        if self.state == 0:
            build_priorities.append((DRONE, 5))
            build_priorities.append((self.steps[self.state].unit_id, 1000 - self.state))
            self.state += 1
            return build_priorities
        previous_step: BOStep = self.steps[self.state-1]
        if self.state >= len(self.steps) - 1:
            self.build_ended = True
            return None
        if self.steps[self.state].try_condition() and (self.bot.units(previous_step.unit_id).exists or self.bot.already_pending(previous_step.unit_id)):
            build_priorities.append((self.steps[self.state].unit_id, 1000 - self.state))
            self.state += 1
        return build_priorities
