# Artificial Overmind Challenge by Reaktor – starter kit

## Creating a repo for the competition

1. Fork this repo in Gitlab
    * Make sure that "Project visibility" of the fork is set to "Private"
2. Give the `overmind-challenge` user **reporter** access to you forked repository
    * Project settings -> members -> invite as reporter
4. Go to [awesome portal](https://overmind-ranker.herokuapp.com/admin/create-team) and register your team

## Gearing up for the battle

For development you will need Python version 3.6 or higher.

1. Follow the installation instruction for StarCraft II, StartCraft II maps, and `python-sc2` from [python-sc2](https://github.com/Dentosal/python-sc2/blob/master/README.md)
2. Change the name and race of your bot to `botinfo.json`
3. Fix all FIXME items in `bot/main.py`
4. Run the bot: `python3 run_locally.py`
5. ???
6. Win the competition!

Documentation for the `python-sc2`:

- [The BotAI-class](https://github.com/Dentosal/python-sc2/wiki/The-BotAI-class)
- [Units and actions](https://github.com/Dentosal/python-sc2/wiki/Units-and-actions)

## Tips

- [Python SC2 Wiki](https://github.com/Dentosal/python-sc2/wiki) contains useful material to get you started.
- [Starcraft II AI Discord](https://discord.gg/qTZ65sh) has community at your fingertips.
- The code for your bot goes to `bot/main.py`: simple examples can be found at [python-sc2 examples](https://github.com/Dentosal/python-sc2/tree/master/examples)
- You can modify the `run_locally.py` starter script to your liking - you might want to increase the difficulty of the game-AI at some point.
- The `start_bot.py` is used when ranking your bot and should not be modified.
