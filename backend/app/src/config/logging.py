import logging
import logging.config
import os
import sys
from pathlib import Path

from backend.app.src.config.settings import settings

# --- Logging Configuration ---

# Determine the base directory for logs if logging to file is enabled
LOG_DIR = Path(settings.LOG_DIR) if settings.LOG_TO_FILE else None
if LOG_DIR:
    LOG_DIR.mkdir(parents=True, exist_ok=True) # Ensure log directory exists

# Define the logging configuration dictionary
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False, # Keep existing loggers (e.g., from libraries)
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "%(asctime)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": { # Example JSON formatter (requires python-json-logger if not customizing manually)
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)d %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default" if settings.DEBUG else "simple",
            "level": settings.LOGGING_LEVEL.upper(),
            "stream": sys.stdout, # Use sys.stdout for console output
        },
    },
    "loggers": {
        "uvicorn.error": { # Uvicorn's own error logger
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": { # Uvicorn's access logger
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "fastapi": { # FastAPI's logger
            "handlers": ["console"],
            "level": settings.LOGGING_LEVEL.upper(),
            "propagate": False,
        },
        "sqlalchemy.engine": { # SQLAlchemy engine logging (can be verbose)
            "handlers": ["console"],
            "level": "WARNING" if not settings.DEBUG else "INFO", # INFO in DEBUG to see SQL queries
            "propagate": False,
        },
        settings.PROJECT_NAME.lower(): { # Application-specific logger
            "handlers": ["console"],
            "level": settings.LOGGING_LEVEL.upper(),
            "propagate": False, # Do not propagate to the root logger if handlers are defined here
        },
    },
    "root": { # Root logger configuration
        "handlers": ["console"],
        "level": settings.LOGGING_LEVEL.upper(),
    },
}

# Add file handlers if LOG_TO_FILE is enabled in settings
if settings.LOG_TO_FILE and LOG_DIR:
    LOGGING_CONFIG["handlers"]["app_file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "formatter": "default",
        "level": settings.LOGGING_LEVEL.upper(),
        "filename": LOG_DIR / settings.LOG_APP_FILE,
        "maxBytes": settings.LOG_MAX_BYTES,
        "backupCount": settings.LOG_BACKUP_COUNT,
        "encoding": "utf-8",
    }
    LOGGING_CONFIG["handlers"]["error_file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "formatter": "default",
        "level": "ERROR", # Only log ERROR level and above to this file
        "filename": LOG_DIR / settings.LOG_ERROR_FILE,
        "maxBytes": settings.LOG_MAX_BYTES,
        "backupCount": settings.LOG_BACKUP_COUNT,
        "encoding": "utf-8",
    }
    # Add file handlers to relevant loggers
    LOGGING_CONFIG["loggers"][settings.PROJECT_NAME.lower()]["handlers"].extend(["app_file", "error_file"])
    LOGGING_CONFIG["root"]["handlers"].extend(["app_file", "error_file"])
    # If you want specific loggers (like FastAPI) to also log to files, add handlers here too
    # LOGGING_CONFIG["loggers"]["fastapi"]["handlers"].extend(["app_file", "error_file"])


def setup_logging():
    """
    Applies the logging configuration defined in LOGGING_CONFIG.
    This function should be called once when the application starts.
    """
    try:
        logging.config.dictConfig(LOGGING_CONFIG)
        logger = logging.getLogger(settings.PROJECT_NAME.lower())
        logger.info(f"Logging configured. Level: {settings.LOGGING_LEVEL.upper()}, File logging: {settings.LOG_TO_FILE}")
        if settings.LOG_TO_FILE and LOG_DIR:
            logger.info(f"Application logs will be stored in: {LOG_DIR / settings.LOG_APP_FILE}")
            logger.info(f"Error logs will be stored in: {LOG_DIR / settings.LOG_ERROR_FILE}")
    except Exception as e:
        # Fallback to basic logging if configuration fails
        logging.basicConfig(level=logging.INFO)
        logging.error(f"Error setting up logging configuration: {e}. Falling back to basicConfig.")

# --- Utility function to get a logger instance ---
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves a logger instance, defaulting to the project's main logger.

    Args:
        name (Optional[str]): The name of the logger. If None, defaults to
                              the PROJECT_NAME from settings.

    Returns:
        logging.Logger: An instance of the logger.
    """
    if name is None:
        name = settings.PROJECT_NAME.lower()
    return logging.getLogger(name)

if __name__ == "__main__":
    # Example of how to use the logging setup
    setup_logging() # Apply the configuration

    # Get loggers
    root_logger = get_logger("root")
    app_logger = get_logger() # Gets the project-specific logger
    fastapi_logger = get_logger("fastapi")
    sqlalchemy_logger = get_logger("sqlalchemy.engine")

    # Log some messages
    root_logger.debug("This is a debug message from root logger.")
    root_logger.info("This is an info message from root logger.")
    root_logger.warning("This is a warning message from root logger.")
    root_logger.error("This is an error message from root logger.")
    root_logger.critical("This is a critical message from root logger.")

    app_logger.info("This is an info message from the application logger.")
    app_logger.error("This is an error from the application, it should go to error.log if file logging is on.")

    fastapi_logger.info("This is an info message from FastAPI logger.")
    if settings.DEBUG:
        sqlalchemy_logger.info("This is an info message from SQLAlchemy logger (simulating SQL query log).")
    else:
        sqlalchemy_logger.warning("This is a warning from SQLAlchemy (e.g. slow query), not an SQL log.")

    try:
        1 / 0
    except ZeroDivisionError:
        app_logger.exception("A caught exception occurred! Traceback will be logged.")

    print(f"\nLogging settings applied. Check console output.")
    if settings.LOG_TO_FILE and LOG_DIR:
        print(f"If file logging is enabled, check files in: {LOG_DIR}")
        print(f"App log: {LOG_DIR / settings.LOG_APP_FILE}")
        print(f"Error log: {LOG_DIR / settings.LOG_ERROR_FILE}")
