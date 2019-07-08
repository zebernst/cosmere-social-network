import logging

from utils.paths import log_dir


# create shared handler
_composite_file_hdlr = logging.FileHandler(log_dir / "csn.log", mode='w')
_composite_file_hdlr.setLevel(logging.DEBUG)
_composite_file_hdlr.setFormatter(logging.Formatter('{asctime} - {name:21s} :: {levelname:^8s} :: {message}', style='{'))


def create_logger(name: str) -> logging.Logger:
    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # create handlers
    stdout_hdlr = logging.StreamHandler()
    stdout_hdlr.setLevel(logging.WARNING)
    named_file_hdlr = logging.FileHandler(log_dir / f"{name}.log", mode='w')
    named_file_hdlr.setLevel(logging.DEBUG)

    # create set handler formats
    stdout_hdlr.setFormatter(logging.Formatter('{name:21s} :: {levelname:^8s} :: {message}', style='{'))
    named_file_hdlr.setFormatter(logging.Formatter('{asctime} :: {levelname:^8s} :: {message}', style='{'))

    # add handlers to logger
    logger.addHandler(stdout_hdlr)
    logger.addHandler(named_file_hdlr)
    logger.addHandler(_composite_file_hdlr)

    # return configured logger
    return logger


def get_active_project_loggers():
    loggers = logging.root.manager.loggerDict
    return [logger for name, logger in loggers.items() if isinstance(logger, logging.Logger) and name.startswith('csn')]


def close_file_handlers(logger: logging.Logger):
    for hdlr in logger.handlers[:]:
        if isinstance(hdlr, logging.FileHandler):
            hdlr.flush()
            hdlr.close()
            logger.removeHandler(hdlr)
