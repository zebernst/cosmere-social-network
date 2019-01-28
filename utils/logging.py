import logging
from utils.paths import log_dir


# create shared handler
_composite_file_hdlr = logging.FileHandler(log_dir / "csn.all.log", mode='w')
_composite_file_hdlr.setLevel(logging.DEBUG)
_composite_file_hdlr.setFormatter(logging.Formatter('%(asctime)s - %(name)s [%(levelname)s] :: %(message)s'))


def create_logger(name):
    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # create handlers
    stdout_hdlr = logging.StreamHandler()
    stdout_hdlr.setLevel(logging.INFO)
    named_file_hdlr = logging.FileHandler(log_dir / f"{name}.log", mode='w')
    named_file_hdlr.setLevel(logging.DEBUG)

    # create set handler formats
    stdout_hdlr.setFormatter(logging.Formatter('%(name)s [%(levelname)s] :: %(message)s'))
    named_file_hdlr.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] :: %(message)s'))

    # add handlers to logger
    logger.addHandler(stdout_hdlr)
    logger.addHandler(named_file_hdlr)
    logger.addHandler(_composite_file_hdlr)

    # return configured logger
    return logger
