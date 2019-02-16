from sc2 import BotAI
from sc2.data import UnitTypeId
from sc2.client import Race
from .data import *
from .scouting_manager import ScoutingManager

class ArmyCompositionManager():
    def __init__(self, bot: BotAI, scouting_manager: ScoutingManager):
        self.bot = bot
        self.scouting_manager = scouting_manager
        self.ids_to_build = []
    
    def iterate(self):
        self.ids_to_build = []
        if UnitTypeId.STARGATE in self.scouting_manager.enemy_tech and self.bot.units(HYDRADEN).exists:
            self.ids_to_build.append(HYDRA)
            if self.bot.units(SPAWNINGPOOL).exists:
                self.ids_to_build.append(LING)
        else:
            if self.bot.units(SPAWNINGPOOL).exists:
                self.ids_to_build.append(LING)
            if self.bot.units(ROACHWARREN).exists:
                self.ids_to_build.append(ROACH)
            # ZvT: Adjust hydra count depending on enemy air unit count
            if self.bot.enemy_race == Race.Terran and self.bot.units(HYDRA).amount < self.scouting_manager.observed_enemy_units.filter(lambda u: u.is_flying).amount:
                self.ids_to_build.append(HYDRA)
            # ZvP: Make hydras if theres a stargate
            elif self.bot.enemy_race == Race.Protoss and self.bot.units(HYDRADEN).exists and UnitTypeId.STARGATE in self.scouting_manager.enemy_tech:
                self.ids_to_build.append(HYDRA)
            elif self.bot.enemy_race == Race.Zerg and self.bot.units(HYDRADEN).exists and self.bot.units(HYDRA).amount + self.bot.already_pending(HYDRA) >= 10 and self.bot.units(ROACH).amount + self.bot.already_pending(ROACH) > 20:
                # ZvZ: make 10 hydras if already have 20+ roaches
                self.ids_to_build.append(HYDRA)