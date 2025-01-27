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
        self._indent_stack: list[str] = list()
    
    def copy(self):
        return ConsoleLogger(self._level)
    
    @property
    def indent(self) -> str:
        return ''.join(self._indent_stack)
    
    def push_indent(self, v: str = '') -> None:
        self._indent_stack.append('{0}\t'.format(v))

    def pop_indent(self) -> None:
        if 0 < len(self._indent_stack):
            self._indent_stack.pop()

    
    def error(self, msg: str) -> None:
        if self._level != LoggerLevel.NOT_SET:
            print('{0}{1}'.format(self.indent, msg))

    def warning(self, msg: str) -> None:
        if self._level != LoggerLevel.NOT_SET:
            print('{0}{1}'.format(self.indent, msg))

    def info(self, msg: str) -> None:
        if self._level in [LoggerLevel.INFO, LoggerLevel.DEBUG]:
            print('{0}{1}'.format(self.indent, msg))

    def debug(self, msg: str) -> None:
        if self._level == LoggerLevel.DEBUG:
            print('{0}{1}'.format(self.indent, msg))
            
    @staticmethod
    def create(verbose: bool):
        return ConsoleLogger(LoggerLevel.DEBUG if verbose else LoggerLevel.INFO)

        