import logging
from enum import Enum


class LoggerLevel(Enum):
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOT_SET = logging.NOTSET
    
