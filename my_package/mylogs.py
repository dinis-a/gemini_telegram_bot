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
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'crit': logging.CRITICAL
    }

    def __new__(cls, filename, level='info', when='midnight', backCount=3,
                fmt='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'):
        """
        Uses __new__ to return an existing logger instance if one with the
        same filename (name) has already been configured. This prevents
        reconfiguring the same logger and adding duplicate handlers.
        """
        # Use the filename as the logger name
        logger_name = filename

        if logger_name in cls._loggers:
            # Return the existing logger instance if already configured
            return cls._loggers[logger_name].logger
        else:
            # Create a new instance if the logger hasn't been configured yet
            instance = super(Logger, cls).__new__(cls)
            instance._configure_logger(logger_name, level, when, backCount, fmt)
            cls._loggers[logger_name] = instance
            return instance.logger

    def _configure_logger(self, logger_name, level, when, backCount, fmt):
        """Configures the logger with handlers and formatters."""
        self.logger = logging.getLogger(logger_name)

        # Prevent log messages from being propagated to the root logger
        # if handlers are already configured here. This helps avoid duplicates
        # if the root logger also has handlers.
        # Note: Propagation is True by default. Setting to False here
        # means this logger's messages won't go up the hierarchy *unless*
        # explicitly handled by this logger or its ancestors with propagate=True.
        # In this setup, we add handlers directly to this logger, so setting
        # propagate to False is often desired to prevent double logging
        # if the root logger is also configured elsewhere.
        self.logger.propagate = False

        # Set the logging level
        self.logger.setLevel(self.level_relations.get(level, logging.INFO)) # Default to INFO if level is invalid

        # Define the log format
        format_str = logging.Formatter(fmt)

        # Add handlers only if the logger doesn't have any handlers yet
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(format_str)
            self.logger.addHandler(console_handler)

            # Ensure the directory for the log file exists
            log_dir = os.path.dirname(logger_name)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # File handler with timed rotation
            # Use the logger_name as the filename for the log file
            file_handler = logging.handlers.TimedRotatingFileHandler(
                filename=logger_name, when=when, backupCount=backCount, encoding='utf-8'
            )
            file_handler.setFormatter(format_str)
            self.logger.addHandler(file_handler)
        else:
             # If handlers already exist, inform (optional)
             # print(f"Logger '{logger_name}' already configured, skipping handler setup.")
             pass

