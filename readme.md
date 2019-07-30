# Cosmere Social Network

> inspired by [this](https://www.macalester.edu/~abeverid/thrones.html) social network analysis of 
  George R. R. Martin's *A Song of Ice and Fire*.

** THIS ANALYSIS IS CURRENTLY IN PROGRESS **

view project site (with interactive graphs) [here][gh-pages]

## Installation
_work in progress_
As the project currently stands, all of the analysis can be done on your local machine. To begin, clone this
repository onto your local machine. 
```bash
git clone https://github.com/zebernst/cosmere-social-network
```

This project manages its Python dependencies with [Pipenv](https://github.com/pypa/pipenv). To install dependencies 
needed to run scripts in this repository, follow the instructions on the Pipenv page to install Pipenv on your local 
machine, navigate to the directory that this repository has been cloned into, and run
```bash
pipenv install
```

Once the dependencies have been installed, there's only one more step. Because Pipenv incorporates a virtual 
environment, you need to prepend any commands that run scripts in this repository with `pipenv run`, or alternatively
run the following command once:
```bash
pipenv shell
```

This will enter the virtual environment created by Pipenv. You'll have to run `pipenv shell` once each time you open
a new terminal window, but the virtual environment will persist in the same work session.

## Project Structure

**code**:
- [`csn.py`](csn.py) is the main script to manage data acquisition and network analysis, meant to be run
  via the command line.
- [`core/characters.py`](core/characters.py) gets character data from the [wiki](https://coppermind.net).
- [`core/constants.py`](core/constants.py) contains certain constants relating to the Cosmere and to metadata about 
  the analysis (e.g. the list of planets in the Cosmere).
- [`core/disambiguation.py`](core/disambiguation.py) is home to functions used to specify exactly which character an
  ambiguous name or title is referring to in the text.
- [`networks/family.py`](networks/family.py) generates a network graph with links representing 
  direct nuclear family relationships.
- [`networks/interactions.py`](networks/interactions.py) generates a network graph with weighted links representing
  interactions between characters in books.
- [`utils/`](utils) contains utility functions used in other files.

**analysis**:
- interactive graphs can be found on the [project site][gh-pages]. this is where most of the analysis efforts 
  will be concentrated.
- [`graphs/family/`](graphs/family) contains network graphs showing family relationships in the Cosmere.
  Includes sub-graphs showing certain key families and relationships on a per-shardworld basis.
  
**misc**:
- [`docs/`](docs) contains the code for the [project site][gh-pages].
- [`data/`](data) is the directory in which all data relevant to the analysis is stored. To avoid potential copyright 
  issues, only data generated with this analysis (e.g. GML network files) will be stored publicly on GitHub.
- [`Gemfile`](Gemfile) and [`Gemfile.lock`](Gemfile.lock) contain the Jekyll dependencies that support
  the project site. These aren't important unless locally hosting your own version of the project site.
- [`Pipfile`](Pipfile) and [`Pipfile.lock`](Pipfile.lock) contain the Python dependencies used in the analysis.
  These can be easily installed using `pipenv`.
- [`readme.md`](readme.md) you are here :)


[gh-pages]: https://zebernst.github.io/cosmere-social-network/