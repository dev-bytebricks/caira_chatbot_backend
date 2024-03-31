import logging.config

def setup_logging():
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": logging.INFO,
            }
        },
        "root": {
            "handlers": ["console"],
            "level": logging.INFO,
        },
        "loggers": {
            "httpx": {
            "level": logging.WARNING,
            "handlers": ["console"],
            "propagate": False,
            }
        },
    }

    logging.config.dictConfig(logging_config)
