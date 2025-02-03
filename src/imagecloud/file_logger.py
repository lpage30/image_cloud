from imagecloud.base_logger import BaseLogger, LoggerLevel
import logging

class FileLogger(BaseLogger):
    def __init__(self, name: str, level: LoggerLevel, log_filepath: str) -> None:
        super().__init__(name, level)
        self._file_handler = logging.FileHandler(log_filepath)
        self._logger.addHandler(self._file_handler)
        
    def copy(self):
        return FileLogger(self._name, self._level, self._)
    
    @staticmethod
    def create(name: str, verbose: bool, log_filepath: str) -> BaseLogger:
        return FileLogger(name, LoggerLevel.DEBUG if verbose else LoggerLevel.INFO, log_filepath)


        