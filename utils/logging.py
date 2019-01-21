import logging
from constants import root_dir


def create_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    fh = logging.FileHandler(root_dir / 'logs' / f"{name}.log", mode='w')
    fh.setLevel(logging.DEBUG)

    ch.setFormatter(logging.Formatter('%(name)s :: %(levelname)s :: %(message)s'))
    fh.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s :: %(message)s'))

    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger
