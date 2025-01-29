import argparse
from imagecloud.position_box_size import Size
from imagecloud.imagecloud_helpers import (
    parse_to_existing_filepath,
    parse_to_int,
    parse_to_float,
    parse_to_size,
)


def existing_filepath(parser: argparse.ArgumentParser, value: str) -> str:
    try:
        return parse_to_existing_filepath(value)
    except Exception as e:
        parser.error(str(e))
    
def is_one_of_array(parser: argparse.ArgumentParser, value: str, valid_values: list[str]) -> str:
    if value in valid_values:
        return value
    else:
        parser.error('Invalid value {0} must be one of [{1}]'.format(value, ','.join(valid_values)))

def is_integer(parser: argparse.ArgumentParser, value: str) -> int:
    try:
        return parse_to_int(value)
    except Exception as e:
        parser.error(str(e))

def is_float(parser: argparse.ArgumentParser, value: str) -> float:
    try:
        return parse_to_float(value)
    except Exception as e:
        parser.error(str(e))

def is_size(parser: argparse.ArgumentParser, value: str) -> Size:
    try:
        return parse_to_size(value)
    except Exception as e:
        parser.error(str(e))
        
def to_unused_filepath(filepath: str, new_suffix: str | None = None) -> str:
    filepath_parts = filepath.split('.')
    filepath_prefix = '.'.join(filepath_parts[:-1])
    suffix = new_suffix if new_suffix is not None else filepath_parts[-1]
    result = '{0}.{1}'.format(filepath_prefix, suffix)
    version: int = 0
    while os.path.isfile(result):
        version += 1
        result = '{0}.{1}.{2}'.format(filepath_prefix, version, suffix)
    return result
