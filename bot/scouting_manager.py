from typing import List

from sc2 import BotAI
from sc2.units import Units
from sc2.unit import Unit
from sc2.position import Point3
from sc2.client import Race

from .unit_observation import UnitObservation
from .data import *

class ScoutingManager():
    def __init__(self, bot: BotAI):
        self.enemy_townhall_count = 1
        self.estimated_enemy_army_value = 0
        self.own_army_value = 0
        self.bot = bot
        self.unit_observations: List[UnitObservation] = []
    
    def iterate(self):
        # Update unit observations based on known enemy units
        ttl = 90
        for unit in self.bot.known_enemy_units:
            updated = False
            for observation in self.unit_observations:
                if observation.unit.tag == unit.tag:
                    observation.update_unit(unit)
                    observation.update_ttl(ttl)
                    updated = True
            if not updated:
                self.unit_observations.append(UnitObservation(unit, ttl))

        # Update observed_enemy_units then remove old observations
        # TODO: remove observations that are in vision, but dont exist
        temp: List[Unit] = []
        to_remove = []
        for observation in self.unit_observations:
            temp.append(observation.unit)
            if not observation.iterate() or (not self.bot.known_enemy_units.find_by_tag(observation.unit.tag) and self.bot.units.closer_than(7, observation.unit.position).exists):
                # forget unit if observation has expired or there's a friendly unit in vision range but the enemy unit can't be seen
                to_remove.append(observation)
        for observation in to_remove:
            self.unit_observations.remove(observation)
        
        self.observed_enemy_units: Units = Units(temp, self.bot._game_data)

        # Count enemy townhalls
        # TODO: scout main base
        temp_basecount = 1
        for struct in self.bot.known_enemy_structures:
            if is_townhall(struct.type_id) and not struct.position in self.bot.enemy_start_locations and struct.position in self.bot.expansion_locations:
                temp_basecount += 1
        self.enemy_townhall_count = temp_basecount

        # Estimate army values
        self.estimated_enemy_army_value = self.bot.calculate_combat_value(self.observed_enemy_units.not_structure.exclude_type({DRONE, OVERLORD, UnitTypeId.SCV, UnitTypeId.PROBE}))
        self.own_army_value = self.bot.calculate_combat_value(self.bot.units.not_structure.ready.filter(lambda u: u.type_id != DRONE and u.type_id != QUEEN))
        # TODO: consider any army type in the army value calculation
        # HACK vvvvvv
        self.own_army_value += self.bot.already_pending(LING) * 50 + self.bot.already_pending(ROACH) * 100

        # Check for proxies
        self.enemy_proxies_exist = False
        self.observed_enemy_structures = self.observed_enemy_units.structure
        if self.observed_enemy_structures.exists:
            for expansion in self.bot.owned_expansions:
                if self.observed_enemy_structures.closer_than(60, expansion).exists:
                    self.enemy_proxies_exist = True
        
        self.enemy_raiders = self.get_enemy_raiders()
        self.enemy_raiders_value = 0
        for base_position in self.enemy_raiders:
            self.enemy_raiders_value += self.bot.calculate_combat_value(self.enemy_raiders[base_position])

        # Check for dumbfuck terrans floating buildings
        self.terran_floating_buildings = False
        if self.bot.enemy_race == Race.Terran and (
            self.observed_enemy_units.not_flying.amount == 0
        ) and self.bot.getTimeInSeconds() > 360: # 6 minutes
            self.terran_floating_buildings = True

    def get_enemy_raiders(self):
        output = {}
        for exp_position in self.bot.owned_expansions:
            enemies = self.bot.known_enemy_units.closer_than(15, exp_position)
            output[exp_position] = enemies
        return output

    def remove_observation(self, tag):
        to_remove = None
        for observation in self.unit_observations:
            if observation.unit.tag == tag:
                to_remove = observation
        if to_remove != None:
            self.unit_observations.remove(to_remove)