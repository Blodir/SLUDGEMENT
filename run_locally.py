import json

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer

from bot import MyBot
from examples.zerg.zerg_rush import ZergRushBot
from examples.worker_rush import WorkerRushBot

def main():
    with open("botinfo.json") as f:
        info = json.load(f)

    race = Race[info["race"]]

    run_game(maps.get("Catalyst LE"), [
        Bot(race, MyBot()),
        Bot(race.Zerg, ZergRushBot())
    ], realtime=False, step_time_limit=2.0, game_time_limit=(60*20), save_replay_as="test.SC2Replay")

if __name__ == '__main__':
    main()
