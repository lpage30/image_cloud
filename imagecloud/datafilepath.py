import pathlib
import uuid
import re

class DataFilepath(object):
    
    def __init__(self, filepath: str | None = None, filetype: str | None = None):
        
        self._filepath = filepath if filepath != None else '{0}.{1}'.format(str(uuid.uuid4()), filetype if filetype != None else 'txt')

        extensions: list[str] = pathlib.Path(self._filepath).suffixes
        save_ext: list[str] = [ext for ext in extensions if ext.startswith('.save')]

        self._filepath_prefix: str = self._filepath.split(''.join(extensions))[0]
        self._filetype = extensions[-1].split('.')[1] if filetype == None else filetype
        self._save_count = 0

        if 0 < len(save_ext):
            found_number = re.search(r".save[^\d]*(\d*).*", save_ext[-1], re.IGNORECASE)
            if found_number:
                self._save_count = int(found_number.group(1))
    
    @property
    def original_filepath(self):
        return self._filepath
    
    @property
    def saveable_filepath(self):
        return '{0}.save{1}.{2}'.format(self._filepath_prefix, self._save_count + 1, self._filetype)
    
    @property
    def filetype(self):
        return self._filetype
    
    @property
    def savecount(self):
        return self._save_count
        
        
        