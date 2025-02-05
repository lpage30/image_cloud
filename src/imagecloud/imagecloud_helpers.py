import datetime
import os.path
from imagecloud.position_box_size import (ResizeType, RESIZE_TYPES, Size)

def parse_to_int(s:str) -> int:
    if s == None or not(s.isdigit()):
        raise ValueError('Invalid value {0} must be a number'.fomat(s))
    return int(s)

def parse_to_float(s:str) -> float:
    if s == None or not(s.replace('.','',1).isdigit()):
        raise ValueError('Invalid value {0} must be a number'.fomat(s))
    return float(s)
    
def parse_to_size(s: str) -> Size:
    width, height = s.split(',')
    return Size((parse_to_int(width), parse_to_int(height)))

def parse_to_existing_path(pathtype: str, value: str) -> str:
    if not os.path.exists(value):
        raise ValueError('The {0} {1} does not exist!'.format(pathtype, value))
    else:
        return value

def parse_to_resize_type(s: str) -> ResizeType:
    for member in ResizeType:
        if s.upper() == member.name:
            return member
    raise ValueError('{0} unsupported. Must be one of [{1}]'.format(s, '{0}'.format('|'.join(RESIZE_TYPES))))

    
def to_unused_filepath(directory: str, name: str, suffix: str) -> str:
    filepath_prefix = os.path.join(directory, name)
    result = '{0}.{1}'.format(filepath_prefix, suffix)
    version: int = 0
    while os.path.isfile(result):
        version += 1
        result = '{0}.{1}.{2}'.format(filepath_prefix, version, suffix)
    return result

class TimeMeasure:
    def __init__(self):
        self.start()

    def start(self) -> datetime.datetime:
        self._start = datetime.datetime.now()
        self._stop = None
        return self._start
    
    def stop(self) -> datetime.datetime:
        self._stop = datetime.datetime.now()
        return self._stop

    def latency(self) -> datetime.timedelta:
        stop = self._stop if self._stop is not None else datetime.datetime.now()
        return stop - self._start
    
    def latency_str(self) -> str:
        delta = self.latency()
        minutes, seconds = divmod(delta.total_seconds(), 60)
        hours, minutes = divmod(minutes, 60)
        milliseconds = (seconds - int(seconds)) * 1000
        return '{0:03}H_{1:02}M_{2:02}S_{3:03}MS'.format(
            int(hours), 
            int(minutes), 
            int(seconds),
            int(milliseconds)
        )
    