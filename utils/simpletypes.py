from collections import namedtuple


RunContext = namedtuple('RunContext', ['prev', 'run', 'next'])
CharacterOccurrence = namedtuple('CharacterOccurrence', ['pos', 'char'])
