from logging import (
    ERROR,
    INFO,
    DEBUG,
    NOTSET
)
from enum import Enum

class LoggerLevel(Enum):
    ERROR = ERROR
    INFO = INFO
    DEBUG = DEBUG
    NOT_SET= NOTSET
    
class ConsoleLogger:
    def __init__(self, level: LoggerLevel) -> None:
        self._level = level
    
    def error(self, msg: str) -> None:
        if self._level != LoggerLevel.NOT_SET:
            print(msg)

    def warning(self, msg: str) -> None:
        if self._level != LoggerLevel.NOT_SET:
            print(msg)

    def info(self, msg: str) -> None:
        if self._level in [LoggerLevel.INFO, LoggerLevel.DEBUG]:
            print(msg)

    def debug(self, msg: str) -> None:
        if self._level == LoggerLevel.DEBUG:
            print(msg)
            
    @staticmethod
    def create(verbose: bool):
        return ConsoleLogger(LoggerLevel.DEBUG if verbose else LoggerLevel.INFO)

        