import logging
from enum import Enum


class LoggerLevel(Enum):
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOT_SET = logging.NOTSET
    
def extract_logger_level(message: str, default: LoggerLevel) -> LoggerLevel:
    for level in LoggerLevel:
        if level.name in message:
            return level
    return default
