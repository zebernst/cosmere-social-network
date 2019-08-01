
class Error(Exception):
    pass


class AmbiguousReferenceError(Error):
    pass


class EmptyDisambiguationError(Error):
    pass


class InvalidDisambiguationError(Error):
    pass


class IncompleteDisambiguationError(Error):
    pass
