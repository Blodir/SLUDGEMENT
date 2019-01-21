from typing import List

from sc2.ids.unit_typeid import UnitTypeId

from .data import *

class BOStep():
    def __init__(self, start_condition, end_condition, unit_id: UnitTypeId):
        self.start_condition = start_condition
        self.end_condition = end_condition
        self.unit_id = unit_id

class BORunner():
    def __init__(self, build_order: List[BOStep]):
        self.build_order = build_order
        self.step = 0
        self.finished = False
    
    def iterate(self) -> UnitTypeId:
        if self.step >= len(self.build_order):
            self.finished = True
            return None

        if (self.step == 0 or self.build_order[self.step-1].end_condition()) and self.build_order[self.step].start_condition():
            self.step += 1
            return self.build_order[self.step - 1].unit_id
        elif self.step > 0 and not self.build_order[self.step-1].end_condition(): return self.build_order[self.step-1].unit_id
        else: return None

class BORepository():
    def __init__(self, bot):
        self.bot = bot
    
    def hatch_first(self):
        return [
            (BOStep(
                lambda: self.bot.supply_used >= 13,
                lambda: self.bot.already_pending(OVERLORD) or self.bot.units(OVERLORD).amount == 2,
                OVERLORD
            )),
            BOStep(
                lambda: self.bot.supply_used >= 13,
                lambda: self.bot.already_pending(DRONE) + self.bot.units(DRONE).amount >= 17,
                DRONE
            ),
            (BOStep(
                lambda: self.bot.supply_used >= 17,
                lambda: self.bot.already_pending(HATCHERY) or self.bot.units(HATCHERY).amount == 2,
                HATCHERY
            )),
            BOStep(
                lambda: self.bot.supply_used >= 16,
                lambda: self.bot.already_pending(DRONE) + self.bot.units(DRONE).amount >= 18,
                DRONE
            ),
            (BOStep(
                lambda: self.bot.supply_used >= 18,
                lambda: self.bot.already_pending(EXTRACTOR) or self.bot.units(EXTRACTOR).exists,
                EXTRACTOR
            )),
            (BOStep(
                lambda: self.bot.supply_used >= 17,
                lambda: self.bot.already_pending(SPAWNINGPOOL) or self.bot.units(SPAWNINGPOOL).exists,
                SPAWNINGPOOL
            )),
            BOStep(
                lambda: self.bot.supply_used >= 16,
                lambda: self.bot.already_pending(DRONE) + self.bot.units(DRONE).amount >= 19,
                DRONE
            ),
            (BOStep(
                lambda: self.bot.supply_used >= 19,
                lambda: self.bot.already_pending(OVERLORD) or self.bot.units(OVERLORD).amount == 3,
                OVERLORD
            ))
        ]
    
    def pool_first_zvz(self):
        return [
            BOStep(
                lambda: self.bot.supply_used >= 13,
                lambda: self.bot.already_pending(OVERLORD) or self.bot.units(OVERLORD).amount == 2,
                OVERLORD
            ),
            BOStep(
                lambda: self.bot.supply_used >= 13,
                lambda: self.bot.already_pending(DRONE) + self.bot.units(DRONE).amount >= 16,
                DRONE
            ),
            BOStep(
                lambda: self.bot.supply_used >= 16,
                lambda: self.bot.already_pending(SPAWNINGPOOL) or self.bot.units(SPAWNINGPOOL).exists,
                SPAWNINGPOOL
            ),
            BOStep(
                lambda: self.bot.supply_used >= 15,
                lambda: self.bot.already_pending(DRONE) + self.bot.units(DRONE).amount >= 17,
                DRONE
            ),
            BOStep(
                lambda: self.bot.supply_used >= 17,
                lambda: self.bot.already_pending(HATCHERY) or self.bot.units(HATCHERY).amount == 2,
                HATCHERY
            ),
            BOStep(
                lambda: self.bot.supply_used >= 16,
                lambda: self.bot.already_pending(DRONE) + self.bot.units(DRONE).amount >= 17,
                DRONE
            ),
            (BOStep(
                lambda: self.bot.supply_used >= 17,
                lambda: self.bot.already_pending(EXTRACTOR) or self.bot.units(EXTRACTOR).exists,
                EXTRACTOR
            )),
            (BOStep(
                lambda: self.bot.supply_used >= 16,
                lambda: self.bot.units(LING).amount + self.bot.already_pending(LING) >= 6,
                LING
            )),
            (BOStep(
                lambda: self.bot.supply_used >= 19,
                lambda: self.bot.already_pending(OVERLORD) or self.bot.units(OVERLORD).amount == 3,
                OVERLORD
            ))
        ]