import logging
import datetime
from sys import stdout
import traceback
from imagecloud.logger_level import LoggerLevel
from imagecloud.native.base_logger import (
    native_set_base_logger
)

class  BaseLogger:
    def __init__(self, name: str, level: LoggerLevel) -> None:
        self._name = name
        self._level = level
        self._indent_stack: list[str] = list()
        self._logging_buffer: list[tuple[LoggerLevel,str]] = list()
        self._buffer_logging: bool = False
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level.value)
        native_set_base_logger(level.value, self._native_logger_callback)
        self._logger.addHandler(logging.StreamHandler(stdout))
                                    
    def get_prefix_message(self, level: LoggerLevel) -> str:
        now = datetime.datetime.now()
        return '{0}-{1} {2}'.format(
            now.strftime('%Y-%m-%dT%H:%M:%S'),
            '%02d' % (now.microsecond / 10000),
            level.name
        )
    def reset_context(self) -> None:
        self._indent_stack: list[str] = list()
        self._logging_buffer: list[tuple[LoggerLevel,str]] = list()
        self._buffer_logging: bool = False

        
    @property
    def buffering(self) -> bool:
        return self._buffer_logging
        
    @property
    def indent(self) -> str:
        result = ''.join(self._indent_stack)
        if 0 < len(self._indent_stack) and 1 < len(self._indent_stack[-1]):
            result = '{0} '.format(result)
        return result
    
    def push_indent(self, v: str = '') -> None:
        self._indent_stack.append('\t{0}'.format(v))

    def pop_indent(self) -> None:
        if 0 < len(self._indent_stack):
            self._indent_stack.pop()
    
    def error(self, msg: str) -> None:
        self._log(LoggerLevel.ERROR, msg)
        
    def warning(self, msg: str) -> None:
        self._log(LoggerLevel.WARNING, msg)

    def info(self, msg: str) -> None:
        self._log(LoggerLevel.INFO, msg)

    def debug(self, msg: str) -> None:
        self._log(LoggerLevel.DEBUG, msg)

    def start_buffering(self) -> None:
        self._buffer_logging = True
        
    def stop_buffering(self, log_buffer: bool) -> None:
        self._buffer_logging = False
        if log_buffer:
            for level, message in self._logging_buffer:
                self._log(level, message)
        self._logging_buffer = list()

    def _log(self, level: LoggerLevel, msg: str, native: bool = False) -> bool:
        if self._level != LoggerLevel.NOT_SET and self._level.value <= level.value:
            if self.buffering and level in [LoggerLevel.INFO, LoggerLevel.DEBUG]:
                self._logging_buffer.append((level, msg))
            else:
                self._logger.log(level.value, '{0}{1}{2}> {3}'.format(
                        self.indent,
                        self.get_prefix_message(level),
                        '(native)' if native else '',
                        msg
                    )
                )        
                return True
        return False
    
    def _native_logger_callback(self, native_level: int, native_message: str):
        level = LoggerLevel(native_level)
        
        self._log(level, native_message, True)
        
    @staticmethod
    def create(name: str, verbose: bool):
        return BaseLogger(name, LoggerLevel.DEBUG if verbose else LoggerLevel.INFO)

        