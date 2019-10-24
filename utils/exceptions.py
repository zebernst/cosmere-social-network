
class Error(Exception):
    pass


class AmbiguousReferenceError(Error):
    pass


class NoDisambiguationFoundError(Error):
    pass


class InvalidDisambiguationError(Error):
    pass


class IncompleteDisambiguationError(Error):
    pass
