import functools
import pickle
import json
from pathlib import Path


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
                with cache_path.open(mode=read) as f:
                    if protocol == 'json':
                        data = json.load(f)
                    else:
                        data = pickle.load(f)

            else:
                data = func(*args, **kwargs)
                with cache_path.open(mode=write) as f:
                    if protocol == 'json':
                        json.dump(data, f)
                    else:
                        pickle.dump(data, f)

            return data

        return wrapper
    return decorator
