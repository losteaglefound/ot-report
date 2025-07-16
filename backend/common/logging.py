import logging
import logging.config
import os

from config import config


# logging.basicConfig(
#     level=logging.INFO,
#     format="%(filename)s - %(asctime)s - %(name)s - %(levelname)s - %(message)s"
# )



LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'detailed': {
            'format': "%(filename)s - %(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },

    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': config.LOG_DIR.joinpath("app.log"),
            'formatter': 'detailed',
            'level': 'INFO',
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'filename': config.LOG_DIR.joinpath("error.log"),
            'formatter': 'detailed',
            'level': 'ERROR',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
            'level': 'INFO',
        },
    },

    'root': {
        'handlers': ['file', 'error_file', 'console'],
        'level': 'DEBUG',
    },
}

logging.config.dictConfig(LOGGING_CONFIG)