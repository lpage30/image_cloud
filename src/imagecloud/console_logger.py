from logging import (
    ERROR,
    WARNING,
    INFO,
    DEBUG,
    NOTSET
)
from enum import Enum

class LoggerLevel(Enum):
    ERROR = ERROR
    WARNING = WARNING
    INFO = INFO
    DEBUG = DEBUG
    NOT_SET= NOTSET
    

class ConsoleLogger:
    def __init__(self, level: LoggerLevel) -> None:
        self._level = level
        self._indent_stack: list[str] = list()
        self._logging_buffer: list[tuple[LoggerLevel,str]] = list()
        self._buffer_logging: bool = False
    
    def copy(self):
        return ConsoleLogger(self._level)                
    
    @property
    def buffering(self) -> bool:
        return self._buffer_logging
        
    @property
    def indent(self) -> str:
        result = ''.join(self._indent_stack)
        if 0 < len(self._indent_stack) and 1 < len(self._indent_stack[-1]):
            result = '{0}> '.format(result)
        return result
    
    def push_indent(self, v: str = '') -> None:
        self._indent_stack.append('\t{0}'.format(v))

    def pop_indent(self) -> None:
        if 0 < len(self._indent_stack):
            self._indent_stack.pop()
    
    def error(self, msg: str) -> None:
        self._log(LoggerLevel.ERROR, '{0}{1}'.format(self.indent, msg))

    def warning(self, msg: str) -> None:
        self._log(LoggerLevel.WARNING, '{0}{1}'.format(self.indent, msg))

    def info(self, msg: str) -> None:
        self._log(LoggerLevel.INFO, '{0}{1}'.format(self.indent, msg))

    def debug(self, msg: str) -> None:
        self._log(LoggerLevel.DEBUG, '{0}{1}'.format(self.indent, msg))

    def start_buffering(self) -> None:
        self._buffer_logging = True
        
    def stop_buffering(self, log_buffer: bool) -> None:
        self._buffer_logging = False
        if log_buffer:
            for level, message in self._logging_buffer:
                self._log(level, message)
        self._logging_buffer = list()

    def _log(self, level: LoggerLevel, msg: str) -> None:
        if self._level != LoggerLevel.NOT_SET and self._level.value <= level.value:
            if self.buffering and level in [LoggerLevel.INFO, LoggerLevel.DEBUG]:
                self._logging_buffer.append((level, msg))
            else:
                print(msg)
            
        
    @staticmethod
    def create(verbose: bool):
        return ConsoleLogger(LoggerLevel.DEBUG if verbose else LoggerLevel.INFO)

        