from sc2 import BotAI
from sc2.data import UnitTypeId
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
            if self.bot.units(HYDRADEN).exists:
                self.ids_to_build.append(HYDRA)