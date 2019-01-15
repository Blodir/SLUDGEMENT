from typing import List

from sc2 import BotAI
from sc2.units import Units
from sc2.unit import Unit

from .unit_observation import UnitObservation
from .data import *
from .util import *

class ScoutingManager():
    def __init__(self, bot: BotAI):
        self.enemy_townhall_count = 1
        self.estimated_enemy_army_value = 0
        self.own_army_value = 0
        self.bot = bot
        self.unit_observations: List[UnitObservation] = []
    
    def iterate(self):
        # Update unit observations based on known enemy units
        for unit in self.bot.known_enemy_units:
            updated = False
            for observation in self.unit_observations:
                if observation.unit.tag == unit.tag:
                    observation.update_ttl(50)
                    updated = True
            if not updated:
                self.unit_observations.append(UnitObservation(unit, 50))

        # Update observed_enemy_units then remove old observations
        temp: List[Unit] = []
        to_remove = []
        for observation in self.unit_observations:
            temp.append(observation.unit)
            if not observation.iterate():
                to_remove.append(observation)
        for observation in to_remove:
            self.unit_observations.remove(observation)
        
        self.observed_enemy_units: Units = Units(temp, self.bot._game_data)
        
        # Count enemy townhalls
        temp_basecount = 1
        for struct in self.bot.known_enemy_structures:
            if is_townhall(struct.type_id) and not struct.position in self.bot.enemy_start_locations:
                temp_basecount += 1
        self.enemy_townhall_count = temp_basecount

        # Estimate army values
        self.estimated_enemy_army_value = self.bot.calculate_combat_value(self.observed_enemy_units.not_structure)
        self.own_army_value = self.bot.calculate_combat_value(self.bot.units.not_structure.ready.filter(lambda u: u.type_id != DRONE and u.type_id != QUEEN))


    def remove_observation(self, tag):
        to_remove = None
        for observation in self.unit_observations:
            if observation.unit.tag == tag:
                to_remove = observation
        if to_remove != None:
            self.unit_observations.remove(to_remove)