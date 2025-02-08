import logging
from enum import Enum
import datetime
import os
from sys import (__stdout__, stdout)
from io import (FileIO, TextIOWrapper)
from typing import TextIO
import imagecloud.native.logging as native
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
    

class ConditionalStreamHandler(logging.StreamHandler):
    
    def __init__(self, stream, write_prefix_token):
        super().__init__(stream)
        self.write_prefix_token = write_prefix_token

    def emit(self, record):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        try:
            msg = self.format(record)
            stream = self.stream
            # issue 35046: merged two stream.writes into one.
            # prefix messages with prefix token so StdOutErrRedirector ignores them
            stream.write(self.write_prefix_token + msg + self.terminator)
            self.flush()
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)

class StdoutInterceptor:
    def __init__(self, logger, level: LoggerLevel, ignore_prefix_token):
        
        self.original_stdout_fd: int = -1
        self.pipe_read_fd: int = -1
        self.pipe_write_fd: int = -1
        self.opened = False
        
        self.logger = logger
        self.log_level = level
        self.ignore_prefix_token = ignore_prefix_token
        self.interceptor_input: TextIO | None = None
        self.open()
        
    def __del__(self):
        self.close()
    
    @property
    def input(self) -> TextIO:
        if self.interceptor_input is None:
            raise ValueError('StdoutInterceptor is closed')
        return self.interceptor_input

    def open(self):
        if self.opened:
            return
        self.opened = True
        self.pipe_read_fd, self.pipe_write_fd = os.pipe()
        self.original_stdout_fd = native.py_set_new_sys_stdout(self.pipe_write_fd)
        self.interceptor_input = TextIOWrapper(FileIO(self.pipe_read_fd, mode='r+'))
        
    def close(self):
        if not(self.opened):
            return
        self.opened = False
        native.py_set_original_sys_stdout(self.original_stdout_fd)
        self.interceptor_input.close()
        os.close(self.pipe_read_fd)

        self.interceptor_input = None
        self.original_stdout_fd = -1
        self.pipe_read_fd= -1
        self.pipe_write_fd = -1


    def write(self, message):
        # Filter out empty messages
        if message.strip():
            # messages starting with prefix_token were written by logger; ignore them to prevent circular write
            if message.startswith(self.ignore_prefix_token):
                # message is 'captured' from stream handler, let it though
                print(message[len(self.ignore_prefix_token):], file=__stdout__)
            else: 
                # message is not 'captured' from stream handler, write it to logger
                self.logger.log(extract_logger_level(message, self.log_level).value, message)
                
    def flush(self):
        if self.opened:
            os.fsync(self.pip_write_fd)
 
class  BaseLogger:
    def __init__(self, name: str, level: LoggerLevel) -> None:
        self._name = name
        self._level = level
        self._indent_stack: list[str] = list()
        self._logging_buffer: list[tuple[LoggerLevel,str]] = list()
        self._buffer_logging: bool = False
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level.value)
        native.py_set_logger_level(level.value)
        self._logger_stdout_prefix_token = '$$'
        self._pipe = os.pipe()
        self._logger.addHandler(ConditionalStreamHandler(stdout, self._logger_stdout_prefix_token))
        self._stdout_intercept = StdoutInterceptor(self._logger, level, self._logger_stdout_prefix_token)
        self._logger.addHander(logging.StreamHandler(self._stdout_intercept.input))

    def get_prefix_message(self, level: LoggerLevel) -> str:
        now = datetime.datetime.now()
        return '{0}-{1} {2}'.format(
            now.strftime('%Y-%m-%dT%H:%M:%S'),
            '%02d' % (now.microsecond / 10000),
            level.name
        )
    
    def copy(self):
        return BaseLogger(self._name, self._level)
        
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

    def _log(self, level: LoggerLevel, msg: str) -> bool:
        if self._level != LoggerLevel.NOT_SET and self._level.value <= level.value:
            if self.buffering and level in [LoggerLevel.INFO, LoggerLevel.DEBUG]:
                self._logging_buffer.append((level, msg))
            else:
                match level:
                    case LoggerLevel.INFO:
                        print('{0} - {1}{2}> {3}'.format(
                                LoggerLevel.INFO.name,
                                self.indent,
                                self.get_prefix_message(LoggerLevel.INFO),
                                msg
                            )
                        )        
                    case LoggerLevel.WARNING:
                        print('{0} - {1}{2}> {3}'.format(
                                LoggerLevel.WARNING.name,
                                self.indent,
                                self.get_prefix_message(LoggerLevel.WARNING),
                                msg
                            )
                        )
                    case LoggerLevel.ERROR:
                        print('{0} - {1}{2}> {3}'.format(
                                LoggerLevel.ERROR.name,
                                self.indent,
                                self.get_prefix_message(LoggerLevel.ERROR),
                                msg
                            )
                        )
                    case _:
                        print('{0} - {1}{2}> {3}'.format(
                                LoggerLevel.DEBUG.name,
                                self.indent,
                                self.get_prefix_message(LoggerLevel.DEBUG),
                                msg
                            )
                        )
                return True
        return False
    
    @staticmethod
    def create(name: str, verbose: bool):
        return BaseLogger(name, LoggerLevel.DEBUG if verbose else LoggerLevel.INFO)

        