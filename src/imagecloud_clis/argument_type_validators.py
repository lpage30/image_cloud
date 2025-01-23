import argparse
from imagecloud.common.string_parsers import (
    parse_to_existing_filepath,
    parse_to_int,
    parse_to_float,
    parse_to_tuple,
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

def is_integer(parser: argparse.ArgumentParser, value: str):
    try:
        return parse_to_int(value)
    except Exception as e:
        parser.error(str(e))

def is_float(parser: argparse.ArgumentParser, value: str):
    try:
        return parse_to_float(value)
    except Exception as e:
        parser.error(str(e))

def is_tuple_integers(parser: argparse.ArgumentParser, value: str):
    try:
        return parse_to_tuple(value)
    except Exception as e:
        parser.error(str(e))