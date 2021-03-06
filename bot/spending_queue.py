import math

from .priority_queue import PriorityQueue
from sc2 import BotAI
from sc2.data import Race

from .data import *
from .build_order import BOStep, BORepository, BORunner
from .scouting_manager import ScoutingManager

class SpendingQueue():
    def __init__(self, bot, scouting_manager: ScoutingManager):
        self.scouting_manager = scouting_manager
        self.spending_queue = PriorityQueue()
        self.bot = bot

        self.build_repository = BORepository(bot)

        build = self.build_repository.hatch_first()
        if self.bot.enemy_race == Race.Zerg:
            build = self.build_repository.pool_first_zvz()
        self.build_order_runner = BORunner(build)

        self.goal_drone_count_per_enemy_base = 24 if self.bot.enemy_race == Race.Zerg else 27

        self.overseer_ttl = 0
    
    def get_spending_queue(self):
        return self.spending_queue
    
    def iterate(self):
        if not self.build_order_runner.finished:
            unit_id: UnitTypeId = self.build_order_runner.iterate()
            if unit_id:
                self.spending_queue.reprioritize(unit_id, 50)
        else:
            self.update_hatchery_priority()

            max_workers = 28
            if self.bot.enemy_race == Race.Protoss:
                max_workers = 36
            if self.scouting_manager.enemy_townhall_count == 2:
                max_workers = 52
            if self.scouting_manager.enemy_townhall_count > 2:
                max_workers = 80

            distance_multiplier = 1
            # TODO: consider enemy unit speed
            try:
                if self.scouting_manager.observed_enemy_units.exclude_type({OVERLORD}).exists:
                    closest_distance = self.scouting_manager.observed_enemy_units.exclude_type({OVERLORD, UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.SCV}).closest_distance_to(self.bot.own_natural)
                    if closest_distance > 90:
                        distance_multiplier = 0.8
                    elif closest_distance > 70:
                        distance_multiplier = 1
                    elif closest_distance > 20:
                        distance_multiplier = 1.5
                    elif closest_distance < 20:
                        distance_multiplier = 1.5
                    if self.bot.enemy_race == Race.Protoss and distance_multiplier > 1:
                        distance_multiplier = 1.1
                if self.scouting_manager.observed_enemy_units(LING).amount > 4 and distance_multiplier < 1:
                    # if they are making lings, have to match ling count exactly
                    distance_multiplier = 1
            except:
                print('spending distance multiplier failure')

            self.bot._client.debug_text_screen(f'Distance multiplier: {distance_multiplier}', (0, 0), None, 8)

            # Make army or drones ?
            # (self.bot.units(DRONE).amount + self.bot.already_pending(DRONE)) > self.goal_drone_count_per_enemy_base * self.scouting_manager.enemy_townhall_count
            if (
                distance_multiplier * self.scouting_manager.estimated_enemy_army_value > self.scouting_manager.own_army_value) or (
                self.scouting_manager.enemy_proxies_exist and self.bot.units(DRONE).amount + self.bot.already_pending(DRONE) > 20) or (
                self.bot.units(DRONE).amount + self.bot.already_pending(DRONE) >= max_workers
                ) and not self.scouting_manager.terran_floating_buildings:
                self.spending_queue.reprioritize(ARMY, 38)
            else:
                self.spending_queue.reprioritize(ARMY, 3)
            
            # HACK: ZvZ: all in at 50 drones
            if self.bot.enemy_race == Race.Zerg and self.bot.units(DRONE).amount + self.bot.already_pending(DRONE) > 48 and self.bot.supply_used < 180:
                self.spending_queue.reprioritize(ARMY, 38)
            
            queen_count = self.bot.units(QUEEN).amount + self.bot.queen_already_pending()
            if self.bot.calculate_combat_value(self.scouting_manager.observed_enemy_units.closer_than(60, self.bot.own_natural)) > 1.2 * self.scouting_manager.own_army_value:
                # panic queens
                self.spending_queue.reprioritize(QUEEN, 37)
            elif self.need_queen():
                self.spending_queue.reprioritize(QUEEN, 21)
            elif self.bot.units(SPAWNINGPOOL).exists and self.bot.units(HATCHERY).amount + 1 > queen_count and queen_count < 6:
                self.spending_queue.reprioritize(QUEEN, 5)
            else:
                self.spending_queue.reprioritize(QUEEN, 2)

            # Always have some lings out
            if self.bot.units(LING).amount + (self.bot.already_pending(LING) * 2) < 4 and self.bot.units(SPAWNINGPOOL).exists:
                self.spending_queue.reprioritize(LING, 32)

            if self.bot.units(SPAWNINGPOOL).exists and not LINGSPEED in self.bot.state.upgrades and not self.bot.already_pending(LINGSPEED):
                self.spending_queue.reprioritize(LINGSPEED, 31)

            if self.need_spawningpool():
                self.spending_queue.reprioritize(SPAWNINGPOOL, 30)

            # ROACH WARREN            
            roach_eco = 34
            if self.bot.enemy_race == Race.Terran:
                roach_eco = 26
            if UnitTypeId.STARGATE in self.scouting_manager.enemy_tech:
                roach_eco = 50
            if (self.bot.units(DRONE).amount + self.bot.already_pending(DRONE) >= roach_eco
                or (self.scouting_manager.enemy_proxies_exist and self.bot.units(DRONE).amount + self.bot.already_pending(DRONE) > 19)
                ) and self.bot.units(SPAWNINGPOOL).exists and not self.bot.units(ROACHWARREN).exists and not self.bot.already_pending(ROACHWARREN):
                self.spending_queue.reprioritize(ROACHWARREN, 30)
            
            # EXTRACTORs for hydras
            workers_per_extractor = 12
            if self.bot.vespene > 200:
                workers_per_extractor = 16
            
            if (self.bot.units(HYDRADEN).exists or self.bot.already_pending(HYDRADEN)) and (
                (self.bot.units(EXTRACTOR).amount + self.bot.already_pending(EXTRACTOR)) < math.floor(self.bot.units(DRONE).amount / workers_per_extractor)):
                self.spending_queue.reprioritize(EXTRACTOR, 29)

            # 2nd and 3rd EXTRACTOR if going for roaches !
            if  (self.bot.units(ROACHWARREN).exists or self.bot.already_pending(ROACHWARREN)) and (
                (self.bot.units(EXTRACTOR).amount + self.bot.already_pending(EXTRACTOR)) < 3) and (
                self.bot.units(DRONE).amount + self.bot.already_pending(DRONE) >= 36
                ):
                self.spending_queue.reprioritize(EXTRACTOR, 29)
            
            # MAKE ROACH SPEED
            if (self.bot.units(LAIR).exists or self.bot.units(HIVE).exists) and not ROACHSPEED in self.bot.state.upgrades and not self.bot.already_pending_upgrade(ROACHSPEED):
                if UnitTypeId.STARGATE in self.scouting_manager.enemy_tech:
                    if self.bot.units(DRONE).amount + self.bot.already_pending(DRONE) > 50:
                        self.spending_queue.reprioritize(ROACHSPEED, 20)
                else:
                    self.spending_queue.reprioritize(ROACHSPEED, 26)

            # MAKE HYDRAS
            if (self.bot.units(LAIR).exists or self.bot.units(HIVE).exists) and not self.bot.units(HYDRADEN).exists and not self.bot.already_pending(HYDRADEN) and (
                UnitTypeId.STARGATE in self.scouting_manager.enemy_tech or (
                self.bot.units(DRONE).amount + self.bot.already_pending(DRONE) > 50)
            ):
                self.spending_queue.reprioritize(HYDRADEN, 40)
            
            # MAKE LAIR
            if not self.bot.units(LAIR).exists and not self.bot.lair_already_pending() and not self.bot.units(HIVE).exists and (
               self.bot.units(DRONE).amount + self.bot.already_pending(DRONE) > 32 or (
                   UnitTypeId.STARGATE in self.scouting_manager.enemy_tech
               )
            ):
                if UnitTypeId.STARGATE in self.scouting_manager.enemy_tech:
                    self.spending_queue.reprioritize(LAIR, 40)
                else:
                    self.spending_queue.reprioritize(LAIR, 25)

            # MAKE INFESTATION PIT
            if not self.bot.units(UnitTypeId.INFESTATIONPIT).exists and self.bot.units(LAIR).exists and not self.bot.units(HIVE).exists and not self.bot.already_pending(UnitTypeId.INFESTATIONPIT) and (
               self.bot.units(DRONE).amount + self.bot.already_pending(DRONE) >= 80):
               self.spending_queue.reprioritize(UnitTypeId.INFESTATIONPIT, 20)

            # MAKE HIVE
            if self.bot.units(UnitTypeId.INFESTATIONPIT).exists and self.bot.units(LAIR).exists and not self.bot.units(HIVE).exists and not self.bot.hive_already_pending() and (
               self.bot.units(DRONE).amount + self.bot.already_pending(DRONE) >= 80):
               self.spending_queue.reprioritize(HIVE, 20)

            self.overseer_ttl -= 1
            # OVERSEER - always have one
            if (self.bot.units(LAIR).exists or self.bot.units(HIVE).exists) and not self.bot.units(OVERSEER).exists and not self.bot.already_pending(OVERSEER) and self.overseer_ttl <= 0:
                self.spending_queue.reprioritize(OVERSEER, 20)
                self.overseer_ttl = 100

            # EVOLUTION CHAMBERS            
            if  (self.bot.units(EVO).amount + self.bot.already_pending(EVO) < 2) and (
                self.bot.units(DRONE).amount + self.bot.already_pending(DRONE) > 52
                ):
                self.spending_queue.reprioritize(EVO, 20)

            if self.bot.units(EVO).ready.exists:
                # MISSILE UPGRADE
                if not self.bot.already_pending_upgrade(MISSILE1) and not MISSILE1 in self.bot.state.upgrades:
                    self.spending_queue.reprioritize(MISSILE1, 24)
                elif not self.bot.already_pending_upgrade(MISSILE2) and not MISSILE2 in self.bot.state.upgrades and MISSILE1 in self.bot.state.upgrades:
                    self.spending_queue.reprioritize(MISSILE2, 24)
                elif self.bot.units(HIVE).exists and not self.bot.already_pending_upgrade(MISSILE3) and not MISSILE3 in self.bot.state.upgrades and MISSILE2 in self.bot.state.upgrades:
                    self.spending_queue.reprioritize(MISSILE3, 24)
                
                # CARAPACE UPGRADE
                if not self.bot.already_pending_upgrade(CARAPACE1) and not CARAPACE1 in self.bot.state.upgrades:
                    self.spending_queue.reprioritize(CARAPACE1, 24)
                elif not self.bot.already_pending_upgrade(CARAPACE2) and not CARAPACE2 in self.bot.state.upgrades and CARAPACE1 in self.bot.state.upgrades:
                    self.spending_queue.reprioritize(CARAPACE2, 24)
                elif self.bot.units(HIVE).exists and not self.bot.already_pending_upgrade(CARAPACE3) and not CARAPACE3 in self.bot.state.upgrades and CARAPACE2 in self.bot.state.upgrades:
                    self.spending_queue.reprioritize(CARAPACE3, 24)

            if self.need_supply():
                self.spending_queue.reprioritize(OVERLORD, 40)

            if self.need_drone():
                self.spending_queue.reprioritize(ECO, 6)
            else:
                self.spending_queue.reprioritize(ECO, 0)
            
            # TODO: Make mutas to deal with floating buildings
            if self.scouting_manager.terran_floating_buildings:
                self.spending_queue.reprioritize(ARMY, 1)
                if not self.bot.units(LAIR).exists and not self.bot.lair_already_pending() and not self.bot.units(HIVE).exists:
                    self.spending_queue.reprioritize(LAIR, 41)
                if (self.bot.units(LAIR).exists or self.bot.units(HIVE).exists) and not self.bot.units(SPIRE).exists and not self.bot.already_pending(SPIRE):
                    self.spending_queue.reprioritize(SPIRE, 41)
                if self.bot.units(SPIRE).exists:
                    self.spending_queue.reprioritize(MUTALISK, 39)



    def need_supply(self) -> bool:
        if self.bot.supply_cap >= 200:
            return False
        mineral_saturation = self.bot.get_mineral_saturation()
        mineral_income = mineral_saturation * DRONE_MINERALS_PER_SECOND
        overlords_in_progress = self.bot.already_pending(OVERLORD)
        mineral_cost = 50
        supply_cost = 1
        overlord_buildtime = 18
        if mineral_income == 0:
            mineral_income = 1
        time_until_supplyblock = (self.bot.supply_left + (overlords_in_progress * 8)) / (supply_cost / mineral_cost * mineral_income)
        return time_until_supplyblock < overlord_buildtime

    def need_drone(self) -> bool:
        return self.bot.already_pending(DRONE) + self.bot.units(DRONE).amount < 80

    def need_hatchery(self) -> bool:
        return self.bot.units(DRONE).amount > (self.bot.units(HATCHERY).amount * LARVA_RATE_PER_INJECT) and not self.bot.already_pending(HATCHERY)

    def need_spawningpool(self) -> bool:
        return not self.bot.units(SPAWNINGPOOL).exists and not self.bot.already_pending(SPAWNINGPOOL)

    def need_queen(self) -> bool:
        queen_count = self.bot.units(QUEEN).amount + self.bot.queen_already_pending()
        return self.bot.units(SPAWNINGPOOL).exists and self.bot.units(HATCHERY).amount > queen_count and queen_count < 6
    
    def update_hatchery_priority(self):
        if self.need_hatchery():
            self.spending_queue.reprioritize(HATCHERY, 20)
        else:
            self.spending_queue.reprioritize(HATCHERY, 4)