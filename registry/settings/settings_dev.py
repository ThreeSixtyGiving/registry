# flake8: noqa
import os
from settings.settings import *  # noqa F401, F403

DEBUG = True

ALLOWED_HOSTS = [".localhost", "127.0.0.1", "[::1]"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{levelname} [{module}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "formatter": "simple",
            "propagate": True,
        },
    },
}
