from collections import namedtuple


__all__ = ['RunContext', 'CharacterOccurrence']


RunContext = namedtuple('RunContext', ['chapter', 'prev', 'run', 'next'])
CharacterOccurrence = namedtuple('CharacterOccurrence', ['pos', 'char'])
