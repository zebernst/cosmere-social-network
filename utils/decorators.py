import functools
import pickle
import json
from pathlib import Path
from utils.logging import create_logger
from enum import Enum, auto


logger = create_logger('csn.utils.decorators')


class CacheProtocol(Enum):
    """define explicit formats that the @cache decorator can deal with"""
    AUTO = auto()
    JSON = auto()
    PICKLE = auto()
    PLAINTEXT = auto()


def cache(filename, protocol='auto'):
    """cache the return value of the decorated function at the given filename."""

    # ensure that enclosing folder of desired cache file exists
    cache_path = Path(filename)
    cache_path.resolve().parent.mkdir(parents=True, exist_ok=True)

    protocols = {
        'pkl': CacheProtocol.PICKLE,
        'pickle': CacheProtocol.PICKLE,
        'p': CacheProtocol.PICKLE,
        'json': CacheProtocol.JSON,
        'txt': CacheProtocol.PLAINTEXT,
        'text': CacheProtocol.PLAINTEXT,
    }
    if protocol == 'auto' or protocol == CacheProtocol.AUTO:
        protocol = protocols.get(cache_path.suffix[1:], CacheProtocol.PLAINTEXT)
    else:
        protocol = protocols.get(protocol, CacheProtocol.PLAINTEXT)

    # specify file pointer mode
    if protocol in ('pkl', ):
        read = 'rb'
        write = 'wb'
    else:
        read = 'r'
        write = 'w'

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            if cache_path.is_file():
                logger.debug(f'Loading cached data for {func.__name__}() found at {filename}.')
                with cache_path.open(mode=read) as f:
                    if protocol == CacheProtocol.PICKLE:
                        data = pickle.load(f)
                    elif protocol == CacheProtocol.JSON:
                        data = json.load(f)
                    else:
                        data = f.read()
            else:
                logger.debug(f'No cached data found for {func.__name__}(), so function will be called.')
                data = func(*args, **kwargs)
                with cache_path.open(mode=write) as f:
                    logger.debug(f'Caching data from {func.__name__}() at {filename}.')
                    if protocol == CacheProtocol.PICKLE:
                        pickle.dump(data, f)
                    elif protocol == CacheProtocol.JSON:
                        json.dump(data, f)
                    else:
                        f.write(data)

            return data

        return wrapper
    return decorator
