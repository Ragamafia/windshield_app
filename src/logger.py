import os   # noqa

from loguru import logger as vanilla_logger


os.environ[
    "LOGURU_FORMAT"
] = "{time:DD.MM.YY HH:mm:ss} [<lvl>{level:^10}</lvl>] <lvl>{message}</lvl>"  # noqa
os.environ["LEVEL"] = "DEBUG"  # noqa


class Logger:
    logger: vanilla_logger

    def __init__(self):
        self.logger = vanilla_logger

        self.debug = vanilla_logger.debug
        self.info = vanilla_logger.info
        self.warning = vanilla_logger.warning
        self.error = vanilla_logger.error
        self.success = vanilla_logger.success
        self.exception = vanilla_logger.exception
        self.critical = vanilla_logger.critical
        self.log = vanilla_logger.log
        self.add = vanilla_logger.add


logger = Logger()