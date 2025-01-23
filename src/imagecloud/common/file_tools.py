import os.path

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

def rename_filenames(filepaths: list[str], new_suffix: str) -> list[str]:
    result: list[str] = list()
    for fname in filepaths:
        result.append(to_unused_filepath(fname, new_suffix))
    return result 

