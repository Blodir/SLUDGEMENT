# Artificial Overmind Challenge by Reaktor – starter kit

[The official Discord server for the competition!](https://discord.gg/D9XEhWY)

## Creating a repo for the competition

1. Fork this repo in Gitlab
    * Make sure that "Project visibility" of the fork is set to "Private"
2. Give the `overmind-challenge` user **reporter** access to you forked repository
    * Settings -> Members -> Invite as reporter
3. Register your team on the [Articial Overmind Challenge site](https://artificial-overmind.reaktor.com/)
    * Copy your repository URL from Gitlab (Project -> Clone -> HTTPS)

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
- If you need to use any Python dependencies, just paste the libraries into your team repo.


## Rules

- The competition will use [the official SEUL rules](http://seul.fi/esports/pelisaannot/turnaussaannot-starcraft-ii/#english-version) for applicable parts
- However, since there are no human players or real time gameplay involved, and because bots may be quite deterministic in their nature:
  * The "3. Other rules" section is not used
    + Bots should properly resign instead of just disconnecting
  * The "7. Fair play" forbids insulting others. However, we not only allow, but encourage you to mock the opposing bot using the in-game chat
    + However, please try be fun and good-intentioning, you are not trying to make anybody feel bad, we are here to have fun
  * Games will be played with a time limit. This is initially 30 minutes of in-game time, and will be updated later if it causes any issues
  * Bot code crashing or exceeding the time limit will automatically lose the match
  * Draw situations will not be replayed, and the games will be marked as draws instead
  * If score-based evaluation is implemented during the competition, it will be used to resolve draws
    + In the finals, draw situations will be resolved by bigger army value in the end of the game, if scores are not available
  * Pausing the game is neither allowed or possile
  * Map pool is static and decided by the organizers
    + All maps will be selected from the official ladder map pool, starting at the first season of 2017, available [here](https://github.com/Blizzard/s2client-proto#map-packs)
- The organizers reserve the right to change the rules and technical limitations during the competition
- Your git repo for the bot must not exceed one gigabyte in size
- Please connect us (e.g. in Discord) if you have any questions

