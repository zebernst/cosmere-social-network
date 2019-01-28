import functools
import pickle
import json
from pathlib import Path
from os import PathLike
from typing import Union
from enum import Enum, auto

from utils.logging import create_logger


logger = create_logger('csn.utils.caching')


class CacheProtocol(Enum):
    """define explicit formats that the @cache decorator can deal with"""
    AUTO = auto()
    JSON = auto()
    PICKLE = auto()
    PLAINTEXT = auto()


_protocols = {
    'pkl': CacheProtocol.PICKLE,
    'pickle': CacheProtocol.PICKLE,
    'p': CacheProtocol.PICKLE,
    'json': CacheProtocol.JSON,
    'txt': CacheProtocol.PLAINTEXT,
    'text': CacheProtocol.PLAINTEXT,
}


def detect_protocol(filename: PathLike):
    """detect protocol type from file extension"""
    cache_path = Path(filename)
    logger.debug('Extracting protocol key from filename.')
    return resolve_protocol(cache_path.suffix[1:])


def resolve_protocol(protocol: Union[CacheProtocol, str]):
    """resolve protocol type from string"""
    if isinstance(protocol, CacheProtocol):
        logger.debug('Direct protocol given, no resolution needed.')
        return protocol
    elif isinstance(protocol, str):
        logger.debug('Protocol resolved from key.')
        return _protocols.get(protocol, CacheProtocol.PLAINTEXT)
    else:
        logger.debug('No protocol found, assuming plain text.')
        return CacheProtocol.PLAINTEXT


def load_cache(path: Path, protocol: CacheProtocol):
    # specify file pointer mode
    if protocol in (CacheProtocol.PICKLE,):
        read = 'rb'
    else:
        read = 'r'

    with path.open(mode=read) as f:
        if protocol == CacheProtocol.PICKLE:
            data = pickle.load(f)
        elif protocol == CacheProtocol.JSON:
            data = json.load(f)
        else:
            data = f.read()

        logger.debug(f'Loaded cached data from {path}.')
        return data


def save_cache(path: Path, protocol: CacheProtocol, data):
    # specify file pointer mode
    if protocol in (CacheProtocol.PICKLE,):
        write = 'wb'
    else:
        write = 'w'

    with path.open(mode=write) as f:
        if protocol == CacheProtocol.PICKLE:
            pickle.dump(data, f)
        elif protocol == CacheProtocol.JSON:
            json.dump(data, f)
        else:
            f.write(data)

        logger.debug(f'Cached data at {path}.')


def cache(filename: PathLike, protocol='auto'):
    """cache the return value of the decorated function at the given filename."""

    # ensure that enclosing folder of desired cache file exists
    cache_path = Path(filename)
    cache_path.resolve().parent.mkdir(parents=True, exist_ok=True)

    if protocol == 'auto' or protocol == CacheProtocol.AUTO:
        protocol = detect_protocol(cache_path)
    elif isinstance(protocol, str):
        protocol = _protocols.get(protocol, CacheProtocol.PLAINTEXT)

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            if cache_path.is_file():
                logger.debug(f'Loading cached data for {func.__name__}().')
                data = load_cache(cache_path, protocol)

            else:
                logger.debug(f'No cached data found for {func.__name__}(), so {func.__name__}() must be called.')
                data = func(*args, **kwargs)
                logger.debug(f'Caching data returned from {func.__name__}().')
                save_cache(cache_path, protocol, data)

            return data

        return wrapper
    return decorator
