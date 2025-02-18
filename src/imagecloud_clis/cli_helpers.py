import argparse
import os.path
from imagecloud.size import (Size, ResizeType, parse_to_resize_type)
from imagecloud.parsers import (
    parse_to_existing_path,
    parse_to_int,
    parse_to_float,
    to_unused_filepath,
)


def existing_filepath(parser: argparse.ArgumentParser, value: str) -> str:
    try:
        return parse_to_existing_path('file', value)
    except Exception as e:
        parser.error(str(e))

def existing_dirpath(parser: argparse.ArgumentParser, value: str) -> str:
    try:
        return parse_to_existing_path('directory', value)
    except Exception as e:
        parser.error(str(e))

def existing_dirpath_of_filepath(parser: argparse.ArgumentParser, value: str) -> str:
    existing_dirpath(parser, os.path.dirname(value))
    return value
    
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
        return Size.parse(value)
    except Exception as e:
        parser.error(str(e))

def to_name(input_filepath: str, output_file_suffix: str, existing_name: str | None, output_directory: str | None):
    name = existing_name if existing_name is not None else os.path.splitext(os.path.basename(input_filepath))[0]
    if output_directory is not None:
        name = os.path.splitext(os.path.basename(
            to_unused_filepath(output_directory, name, output_file_suffix)
        ))[0]
    return name

def is_resize_type(parser: argparse.ArgumentParser, value: str) -> ResizeType:
    try:
        return parse_to_resize_type(value)
    except Exception as e:
        parser.error(str(e))


