# Contributing to LeoSetter

First off, thank you for considering contributing to LeoSetter! It's people like you that make LeoSetter such a great tool.

## Where do I go from here?

If you've noticed a bug or have a feature request, please make one! It's generally best if you get confirmation of your bug or approval for your feature request this way before starting to code.

## Fork & create a branch

If this is something you think you can fix, then fork LeoSetter and create a branch with a descriptive name.

A good branch name would be (where issue #325 is the ticket you're working on):

```sh
git checkout -b 325-add-dms-gps-support
```

## Get the test suite running

Make sure you have a working Python development environment.
Install the dependencies using `pip install -r requirements.txt`. 
You will also need `exiftool` installed on your system.

Currently, you can test the application simply by running it:
```sh
python run_mvp.py
```

*Note: Automated tests will be added in a future update.*

## Implement your fix or feature

At this point, you're ready to make your changes. Feel free to ask for help; everyone is a beginner at first.

## Make a Pull Request

At this point, you should switch back to your master branch and make sure it's up to date with LeoSetter's master branch:

```sh
git remote add upstream git@github.com:yourusername/leosetter.git
git checkout master
git pull upstream master
```

Then update your feature branch from your local copy of master, and push it!

```sh
git checkout 325-add-dms-gps-support
git rebase master
git push --set-upstream origin 325-add-dms-gps-support
```

Finally, go to GitHub and make a Pull Request! Please use the provided Pull Request template to describe your changes.
