import logging
import logging.handlers
import os


class Logger(object):
    """
    A simple logging class that configures a logger with a console handler
    and a timed rotating file handler, ensuring handlers are not duplicated.
    """

    _loggers = {}  # Class-level dictionary to keep track of configured loggers

    level_relations = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "crit": logging.CRITICAL,
    }

    def __new__(
        cls,
        filename,
        level="info",
        when="midnight",
        backCount=3,
        fmt="%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s",
    ):
        logger_name = filename

        if logger_name in cls._loggers:
            return cls._loggers[logger_name].logger
        else:
            instance = super(Logger, cls).__new__(cls)
            instance._configure_logger(logger_name, level, when, backCount, fmt)
            cls._loggers[logger_name] = instance
            return instance.logger

    def _configure_logger(self, logger_name, level, when, backCount, fmt):
        """Configures the logger with handlers and formatters."""
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False
        self.logger.setLevel(self.level_relations.get(level, logging.INFO))

        format_str = logging.Formatter(fmt)

        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(format_str)
            self.logger.addHandler(console_handler)

            log_dir = os.path.dirname(logger_name)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            file_handler = logging.handlers.TimedRotatingFileHandler(
                filename=logger_name, when=when, backupCount=backCount, encoding="utf-8"
            )
            file_handler.setFormatter(format_str)
            self.logger.addHandler(file_handler)
