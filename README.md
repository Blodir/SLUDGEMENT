# The Artificial Overmind Challenge by Reaktor starter kit

[Join the official Discord server for the competition!](https://discord.gg/D9XEhWY)

## Creating a repo for the competition

1. Fork this repo in Gitlab
    * Make sure that "Project visibility" is set to "Private"
2. Give the `overmind-challenge` user **reporter** access to your forked repository
    * Settings -> Members -> Invite as reporter
3. Register your team on the [Artificial Overmind Challenge site](https://artificial-overmind.reaktor.com/)
    * Copy your repository URL from Gitlab (Project -> Clone -> HTTPS)
4. You'll get an email with more instructions and link to your Team Dashboard!

## Gearing up for the battle

Note: for development you will need Python version 3.6 or higher.

1. Follow the installation instructions for StarCraft II, StartCraft II maps, and `python-sc2` from [python-sc2](https://github.com/Dentosal/python-sc2/blob/master/README.md)
    * The Starcraft II game is free to play! Just follow the instructions above to get started.
2. Change the name and race of your bot to `botinfo.json`
3. Fix all FIXME items in `bot/main.py`
4. Run the bot: `python3 run_locally.py`
5. Push your code to Gitlab to start fighting your opponents. You'll see the results on your Team Dashboard (link in email)
7. Win the competition!

Documentation for the `python-sc2`:
- [The BotAI-class](https://github.com/Dentosal/python-sc2/wiki/The-BotAI-class)
- [Units and actions](https://github.com/Dentosal/python-sc2/wiki/Units-and-actions)

## Example

A worker rush is less than twenty lines of code:

```python
import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer

class WorkerRushBot(sc2.BotAI):
    async def on_step(self, iteration):
        if iteration == 0:
            actions = []
            for worker in self.workers:
                actions.append(worker.attack(self.enemy_start_locations[0]))
            await self.do_actions(actions)

run_game(maps.get("Abyssal Reef LE"), [
    Bot(Race.Zerg, WorkerRushBot()),
    Computer(Race.Protoss, Difficulty.Medium)
], realtime=True)
```

This is probably the simplest bot that has any realistic chances of winning the game. We have run it against the medium AI a few times, and once in a while it wins.

You can find more examples in the [`examples/`](/examples) folder.

## Tips

- The [Python SC2 Wiki](https://github.com/Dentosal/python-sc2/wiki) contains useful material to get you started
- The [Starcraft II AI Discord](https://discord.gg/D9XEhWY) gives you access to the community and support
- The code for your bot goes to [bot/main.py](bot/main.py): simple examples can be found at [python-sc2 examples](https://github.com/Dentosal/python-sc2/tree/master/examples)
  * Further, our server-side runner expects to find a class names `MyBot` in this file.
- On our servers, your code will be run on python 3.6. (currently, python 3.6.3)
- You can modify the `run_locally.py` starter script to your liking as you might want to increase the difficulty of the game-AI at some point
- If you need to use any Python dependencies, just paste the libraries into your team repo
- Push code to Gitlab early and push it often, to see your progress and make sure your bot works correctly on our servers.
- Watch how your bot fares on the Ranking on the [Artificial Overmind Challenge site](https://artificial-overmind.reaktor.com/)  

## Rules

- The competition will use [the official SEUL rules](https://seul.fi/e-urheilu/pelisaannot/turnaussaannot-starcraft-ii/#english-version) where applicable 
- However, since there are no human players or real-time gameplay and because bots may be quite deterministic in their nature, we've made the following adjustments:
  * The "3. Other rules" section is not used
    + Bots should properly resign instead of just disconnecting
  * The "7. Fair play" section forbids insulting others. However, we not only allow, but actively encourage you to mock the opposing bot using the in-game chat
    + Please remember to keep it fun and good-natured - we're not trying to make anybody feel bad but are here to have fun
  * Games will be played with a time limit. This is initially 30 minutes of in-game time, and will be updated later if it causes any issues
  * Bot code crashing or exceeding the per-step time limit will automatically result in a loss
    + Per-step limit is currently 2 seconds, but will be lowered it that becomes an issue later
  * Draw situations will not be replayed and the games will be marked as draws instead
  * If score-based evaluation is implemented during the competition, it will be used to resolve draws
    + In the finals, draw situations will be resolved by who has the higher army value at the end of the game if scores are not available
  * Pausing the game is neither allowed or possible
  * The map pool is static and decided by the organizers
    + All maps will be selected from the official ladder map pool starting with the first season of 2017, available [here](https://github.com/Blizzard/s2client-proto#map-packs)
- The organizers reserve the right to change the rules and technical limitations during the competition
- Your git repo for the bot must not exceed one gigabyte in size
- Technical limitations:
  * IO is not allowed. Don't use filesystem or networking.
  * Starting threads or processes is not allowed. 
- Please contact us (e.g. in Discord) if you have any questions

