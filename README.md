# A bot template for Reaktor Overmind Challenge

Welcome to take part in the Overmind-Challenge. In order to register for the competition, head over to [Overmind-challenge]-link. Then let's get you started.

## Creating a repo for the competition

We have chosen to use Gitlab for the competition because it offers users free private repositories.

1. Fork this repo
    * You probably want to change the "Project visibility" of the fork to Private - so nobody borrows your ideas.
2. Give the "overmind-challenge"-user **reporter** access to the repository. This is used for automated ranking.
    * Under project **settings**, go to **members** subsection.
    * For the "Member to invite"-section, query for overmind-challenge, and choose "**Overmind Challenge @overmind-challenge**"
    * Set "Choose a role" as Reporter
    * Apply change, by clicking "Add to project"
3. (Optional) Repeat step 2 and invite your teammates, to share the glory.
4. If you were signing up for the competition - you are now able to finish the registration.

## Identify your team

1. Change the name and race of your bot to `botinfo.json`
    * The race can be changed during the competition.

## Gearing up for the battle

For development you will need Python version 3.6 or higher. Additionally the use of ``python-sc2`` is required.

1. Follow the installation instruction for StarCraft II, StartCraft II maps, and python-sc2 from [python-sc2](https://github.com/Dentosal/python-sc2/blob/master/README.md)
2. Try running the bot: ``python3 run_locally.py``
3. Start coding!


## Starting points

- [Python SC2 Wiki](https://github.com/Dentosal/python-sc2/wiki) contains useful material to get you started.
- The code for your bot goes to `bot/main.py`
- You can modify the `run_locally.py` starter script to your liking - you might want to increase the difficulty of the game-AI at some point.
- The `start_bot.py` is used when ranking your bot and should not be modified.