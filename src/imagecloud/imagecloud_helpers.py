import os.path

def parse_to_int(s:str) -> int:
    if s == None or not(s.isdigit()):
        raise ValueError('Invalid value {0} must be a number'.fomat(s))
    return int(s)

def parse_to_float(s:str) -> float:
    if s == None or not(s.replace('.','',1).isdigit()):
        raise ValueError('Invalid value {0} must be a number'.fomat(s))
    return float(s)
    
def parse_to_tuple(s: str) -> tuple[int, int]:
    width, height = s.split(',')
    return (parse_to_int(width), parse_to_int(height))

def parse_to_existing_filepath(value: str) -> str:
    if not os.path.exists(value):
        raise ValueError('The file {0} does not exist!'.format(value))
    else:
        return value
    
def to_unused_filepath(filepath: str, new_suffix: str | None = None) -> str:
    filepath_parts = filepath.split('.')
    filepath_prefix = '.'.join(filepath_parts[:-1])
    suffix = new_suffix if new_suffix != None else filepath_parts[-1]
    result = '{0}.{1}'.format(filepath_prefix, suffix)
    version: int = 0
    while os.path.isfile(result):
        version += 1
        result = '{0}.{1}.{2}'.format(filepath_prefix, version, suffix)
    return result

