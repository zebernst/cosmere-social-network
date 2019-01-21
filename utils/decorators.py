import functools
import pickle
import json
from pathlib import Path
from utils.logging import create_logger


logger = create_logger('csn.utils.decorators')


def cache(filename, protocol='pkl'):
    """cache the return value of the decorated function at the given filename."""
    if protocol == 'pkl':
        read = 'rb'
        write = 'wb'
    else:
        read = 'r'
        write = 'w'

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            cache_path = Path(filename)
            if cache_path.is_file():
                logger.debug(f'Loading cached data for {func.__name__}() found at {filename}.')
                with cache_path.open(mode=read) as f:
                    if protocol == 'json':
                        data = json.load(f)
                    else:
                        data = pickle.load(f)

            else:
                logger.debug(f'No cached data found for {func.__name__}(), so function will be called.')
                data = func(*args, **kwargs)
                with cache_path.open(mode=write) as f:
                    logger.debug(f'Caching data from {func.__name__}() at {filename}.')
                    if protocol == 'json':
                        json.dump(data, f)
                    else:
                        pickle.dump(data, f)

            return data

        return wrapper
    return decorator
