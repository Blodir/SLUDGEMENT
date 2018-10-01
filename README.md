# A bot template for Reaktor Overmind Challenge

Welcome to take part in the Overmind-Challenge. In order to register for the competition, head over to [Overmind-challenge]-link. Then let's get you started.

## Creating a repo for the competition

We have chosen to use Gitlab for the competition because it offers users free private repositories (which you probably wanna use)

1. Create a duplicate of this repository. (Forking is not ideal, as you cannot make the fork private.)
    * Create private empty repo on Gitlab
    * Clone this repository
    * Change the url for the origin of this repository with command ``git remote set-url origin [YOU-REPO-URL.git]``
        * Note, if using HTTPS. you need to change the url from ``https://gitlab.com/my_gitlab_user/myrepo.git`` to ``https://my_gitlab_user@gitlab.com/my_gitlab_user/myrepo.git``
    * Push the code to origin ``git push -u origin --all``
2. Give the "overmind-challenge"-user **reporter** access to the repository. This is used for automated ranking.
    * Under project **settings**, go to **members** subsection.
    * As member to invite, query for overmind-challenge, and choose **Overmind Challenge @overmind-challenge**
    * Set "Choose a role" as Reporter
    * Apply change, by clicking "Add to project"
3. (Optional) Repeat step 2 and invite your teammates, to share the glory.
4. If you were signing up for the competition - you are now able to finish the registration.

## Identify your team

1. Change the name and race of your bot from `botinfo.json`

## Gearing up for the battle

For development you will need Python version 3.6 or higher. Additionally the use of ``python-sc2`` is required.

1. Follow the installation instruction from [python-sc2](https://github.com/Dentosal/python-sc2/blob/master/README.md)
2. Try running the dummy-bot that we provided: ``python3 run_locally.py``
3. Start coding!


## Starting points

- [Python SC2 Wiki](https://github.com/Dentosal/python-sc2/wiki)
- Your bot code goes to `bot/main.py`
- You can modify the `run_locally.py` starter script to your liking
- Do not modify `start_bot.py` as we use it to rank your bot.