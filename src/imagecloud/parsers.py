import os.path

def parse_to_int(s:str) -> int:
    if s == None or not(s.isdigit()):
        raise ValueError('Invalid value {0} must be a number'.fomat(s))
    return int(s)

def parse_to_float(s:str) -> float:
    if s == None or not(s.replace('.','',1).isdigit()):
        raise ValueError('Invalid value {0} must be a number'.fomat(s))
    return float(s)
    
def parse_to_existing_path(pathtype: str, value: str) -> str:
    if not os.path.exists(value):
        raise ValueError('The {0} {1} does not exist!'.format(pathtype, value))
    else:
        return value
    
def to_unused_filepath(directory: str, name: str, suffix: str) -> str:
    filepath_prefix = os.path.join(directory, name)
    result = '{0}.{1}'.format(filepath_prefix, suffix)
    version: int = 0
    while os.path.isfile(result):
        version += 1
        result = '{0}.{1}.{2}'.format(filepath_prefix, version, suffix)
    return result

