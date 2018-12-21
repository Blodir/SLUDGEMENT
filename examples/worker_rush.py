import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer

class WorkerRushBot(sc2.BotAI):
    async def on_step(self, iteration):
        actions = []
        if iteration == 0:
            for worker in self.workers:
                actions.append(worker.attack(self.enemy_start_locations[0]))
            await self.do_actions(actions)

def main():
    run_game(maps.get("Abyssal Reef LE"), [
        Bot(Race.Zerg, WorkerRushBot()),
        Computer(Race.Protoss, Difficulty.Medium)
    ], realtime=True)

if __name__ == '__main__':
    main()
