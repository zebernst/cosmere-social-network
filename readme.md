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

**[WIP]**

## Project Structure

**code**:
- [`characters.py`](characters.py) gets character data from the [wiki](https://coppermind.net).
- [`networks/family.py`](networks/family.py) generates a network graph with links representing 
  direct nuclear family relationships.
- [`constants.py`](constants.py) contains certain constants relating to the Cosmere and to metadata about 
  the analysis (e.g. the list of planets in the Cosmere).
- [`utils/`](utils) contains utility functions used in other files.
- [`parse_book.py`](parse_book.py) **(WIP)** is the file that will eventually be used to scan the books
  for characters and create associations between them. Currently does nothing.

<br />

**analysis**:
- interactive graphs can be found on the [project site][gh-pages]. this is where most of the analysis efforts 
  will be concentrated.
- [`graphs/family/`](graphs/family) contains network graphs showing family relationships in the Cosmere.
  Includes sub-graphs showing certain key families and relationships on a per-shardworld basis.
  
<br />

**misc**:
- [`docs/`](docs) contains the code for the [project site][gh-pages].
- [`data/`](data) is the directory in which all data relevant to the analysis is stored. Due to copyright,
  only data generated with this analysis (e.g. [`GML network data`](data/networks/family/all.gml) will be stored 
  publicly on GitHub.
- [`Pipfile`](Pipfile) and [`Pipfile.lock`](Pipfile.lock) contain the Python dependencies used in the analysis.
  These can be easily installed using `pipenv`.
- [`readme.md`](readme.md) is this file.


[gh-pages]: https://zebernst.github.io/cosmere-social-network