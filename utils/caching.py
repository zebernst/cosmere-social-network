import functools
import json
import pickle
from enum import auto, Enum
from pathlib import Path
from typing import Any, Union

from .logs import get_logger


__all__ = ['cache', 'save_cache', 'load_cache', 'CacheProtocol', 'detect_protocol']


logger = get_logger('csn.utils.caching')


class CacheProtocol(Enum):
    """define explicit formats that the @cache decorator can deal with"""
    AUTO = auto()
    JSON = auto()
    PICKLE = auto()
    PLAINTEXT = auto()

    @property
    def read(self):
        return {
            CacheProtocol.JSON:      'rt',
            CacheProtocol.PICKLE:    'rb',
            CacheProtocol.PLAINTEXT: 'rt'
        }[self]

    @property
    def write(self):
        return {
            CacheProtocol.JSON:      'wt',
            CacheProtocol.PICKLE:    'wb',
            CacheProtocol.PLAINTEXT: 'wt'
        }[self]

    @property
    def append(self):
        return {
            CacheProtocol.JSON:      'at',
            CacheProtocol.PICKLE:    'ab',
            CacheProtocol.PLAINTEXT: 'at'
        }[self]


_protocols = {
    'pkl':    CacheProtocol.PICKLE,
    'pickle': CacheProtocol.PICKLE,
    'p':      CacheProtocol.PICKLE,
    'json':   CacheProtocol.JSON,
    'txt':    CacheProtocol.PLAINTEXT,
    'text':   CacheProtocol.PLAINTEXT,
}


def detect_protocol(filename: Union[Path, str]) -> CacheProtocol:
    """detect protocol type from file extension"""
    cache_path = Path(filename)
    logger.debug('Extracting protocol key from filename.')
    return resolve_protocol(cache_path.suffix[1:])


def resolve_protocol(protocol: Union[CacheProtocol, str]) -> CacheProtocol:
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


def load_cache(path: Path, protocol: CacheProtocol) -> Any:
    with path.open(mode=protocol.read) as f:
        if protocol == CacheProtocol.PICKLE:
            data = pickle.load(f)
        elif protocol == CacheProtocol.JSON:
            data = json.load(f)
        else:
            data = f.read()

        logger.debug(f'Loaded cached data from {path}.')
        return data


def save_cache(path: Path, protocol: CacheProtocol, data):
    with path.open(mode=protocol.write) as f:
        if protocol == CacheProtocol.PICKLE:
            pickle.dump(data, f)
        elif protocol == CacheProtocol.JSON:
            json.dump(data, f)
        else:
            f.write(data)

        logger.debug(f'Stored cached data at {path}.')


def cache(filename: Union[Path, str], protocol='auto'):
    """cache the return value of the decorated function at the given filename."""

    # ensure that enclosing folder of desired cache file exists
    cache_path = Path(filename)
    cache_path.resolve().parent.mkdir(parents=True, exist_ok=True)

    if protocol == 'auto' or protocol == CacheProtocol.AUTO:
        protocol = detect_protocol(cache_path)
    elif isinstance(protocol, str):
        protocol = resolve_protocol(protocol)

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            if cache_path.is_file():
                logger.info(f'Loading cached data for {func.__name__}().')
                data = load_cache(cache_path, protocol)

            else:
                logger.info(f'No cached data found for {func.__name__}(); executing function.')
                data = func(*args, **kwargs)
                logger.info(f'Caching data returned from {func.__name__}().')
                save_cache(cache_path, protocol, data)

            return data

        return wrapper

    return decorator
