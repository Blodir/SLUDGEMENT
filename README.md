# A bot template for Reaktor Overmind Challenge

Welcome to take part in the Overmind-Challenge. Let's get you started!

## Creating a repo for the competition

We have chosen to use Gitlab for the competition because it offers users free private repositories (which you probably wanna use)

1. Create a duplicate of this repository. (Forking is not ideal, as you cannot make the fork private.)
    * Create private empty repo on Gitlab
    * Clone this repository
    * Change the url for the origin of this repository with command ``git remote set-url origin [YOU-REPO-URL.git]``
    * Push the code to origin ``git push -u origin --all``
2. Give the "overmind-challenge"-user **reporter** access to the repository. This is used for automated ranking.
3. (Optional) Invite your teammates, to share the glory.

## Setup

You'll need Python 3.6 or newer.

1. Change the name and race of your bot from `botinfo.json`
2. Install the SC2 Python API: `pip3 install --user --upgrade sc2`.
3. Try it: `python3 run_locally.py`
4. Start coding!

Starting points:

- [Python SC2 API docs](https://github.com/Dentosal/python-sc2), check out the Wiki!
- Your bot code goes to `bot/main.py`
- You can modify the `run_locally.py` starter script to your liking
- Do not modify `start_bot.py` which is used by the competition runner scripts
