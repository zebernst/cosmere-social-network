# Cosmere Social Network

> inspired by [this](https://www.macalester.edu/~abeverid/thrones.html) social network analysis of 
  George R. R. Martin's *A Song of Ice and Fire*.

_work in progress_

<br />

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
- [`graphs/family/`](graphs/family) contains network graphs showing family relationships in the Cosmere.
  Includes sub-graphs showing certain key families and relationships on a per-shardworld basis.
  
<br />

**misc**:
- [`docs/`](docs) contains the code for the [project site](https://zebernst.github.io/cosmere-social-network).
- [`data/`](data) is the directory in which all data relevant to the analysis is stored. Due to copyright,
  only publicly available data (i.e. the character data from the wiki) will be stored publicly on GitHub.
- [`Pipfile`](Pipfile) and [`Pipfile.lock`](Pipfile.lock) contain the Python dependencies used in the analysis.
  These can be easily installed using `pipenv`.
- [`readme.md`](readme.md) is this file.
