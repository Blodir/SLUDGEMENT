from sc2 import BotAI

from .data import *

class ScoutingManager():
    def __init__(self, bot: BotAI):
        self.enemy_townhall_count = 1
        self.bot = bot
    
    def iterate(self):
        temp_basecount = 1
        for struct in self.bot.known_enemy_structures:
            if is_townhall(struct.type_id) and not struct.position in self.bot.enemy_start_locations:
                temp_basecount += 1
        self.enemy_townhall_count = temp_basecount