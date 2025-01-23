import argparse
import os.path

def parse_to_int(s:str) -> int:
    if s == None or not(s.isdigit()):
        raise ValueError('Invalid value {0} must be a number'.fomat(s))

def parse_to_float(s:str) -> float:
    if s == None or not(s.replace('.','',1).isdigit()):
            raise ValueError('Invalid value {0} must be a number'.fomat(s))
    return float(s)
    
def parse_to_tuple(s: str) -> tuple[int, int]:
    width, height = s.split(',')
    return (parse_to_int(width), parse_to_int(height))

def existing_filepath(parser: argparse.ArgumentParser, value: str) -> str:
    if not os.path.exists(value):
        parser.error('The file {0} does not exist!'.format(value))
    else:
        return value
    
def is_one_of_array(parser: argparse.ArgumentParser, value: str, valid_values: list[str]) -> str:
    if value in valid_values:
        return value
    else:
        parser.error('Invalid value {0} must be one of [{1}]'.format(value, ','.join(valid_values)))

def is_integer(parser: argparse.ArgumentParser, value: str):
    try:
        return parse_to_int(str)
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