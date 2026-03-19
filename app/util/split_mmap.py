# Wrapper for multiple files as a single mmap class
# Only provides size, tell, seek, read, read_byte, find, close methods

import math
import os
from .file        import mmap as mmap_open, fopen
from typing       import TYPE_CHECKING
if TYPE_CHECKING: from ..pack   import DataPack
else: DataPack = None

class DataPackPart:
    def __init__(self, path, offset:int=0):
        self._path = path
        self._fileno = fopen(path)
        self.mmap = mmap_open(file=self._fileno)
        self._offset = offset
        self._end_offset = offset + self.mmap.size()

    def size(self):
        return self.mmap.size()

    def contains_offset(self, offset):
        return self._offset <= offset and self._end_offset > offset

    def to_local_offset(self, offset:int=0):
        return offset - self._offset

    def bytes_to_end(self, offset: int=0):
        return self._end_offset - offset

class FragmentedPackMemoryMap:
    '''
    Use this to seek and read from a data.pack split into multiple files
    '''

    parts: list[DataPackPart] = []
    _size = 0
    internal_cursor = 0
    
    def __init__(self, pack: DataPack):
        if pack._parts:
            current_offset = 0
            self.parts = []
            for part in pack._parts:
                p = DataPackPart(part, current_offset)
                current_offset += p.size()
                self.parts.append(p)
            self._size = current_offset

        else:
            self.parts = [ DataPackPart(pack._path, 0) ]
            self._size = self.parts[0].size()
        
        self.active_pack_part = self.parts[0]

    def _get_file_at_offset(self, offset: int=None):
        # YunaEngine data.pack parts seem to have max fixed size of 1.073.741.824 bytes (1GB)
        # to find the file of a specific file we could do floor( offset / 1.073.741.824 )
        # (assuming all parts except the last one are full and that they are sorted)
        return self.parts[math.floor( offset / 1073741824 )]
        # looping is slower but future proof

        # for part in self.parts:
        #     if part.contains_offset(j):
        #         return part
        # raise Exception(f'Offset {offset} not found in split {self.parts[0]._path}!')
    
    def _update_local_cursor_and_return_file(self):
        '''
        Return the file at the current offset of tell() and updates the file's real cursor to match that offset
        Use this after calling self.seek()
        '''
        file = self._get_file_at_offset(self.internal_cursor)
        file.mmap.seek( file.to_local_offset(self.internal_cursor) )
        return file

    def current_file(self):
        '''
        Return the file at the current offset of tell(), but it doesn't update the file's memory map position
        '''
        return self._get_file_at_offset(self.internal_cursor)
    
    def seek(self, pos: int=0, *args):
        s = self.size()
        self.internal_cursor = pos if pos < s else s
    
    def tell(self):
        return self.internal_cursor
    
    def size(self):
        '''
        Total size of all parts combined
        '''
        return self._size

    def read(self, size: int=1):
        to_read = size
        result = bytes()
        while to_read > 0:
            part = self._update_local_cursor_and_return_file()
            read_cunk_size = min(to_read, part.bytes_to_end(self.internal_cursor))
            result += part.mmap.read(read_cunk_size)
            to_read-=read_cunk_size
            self.seek(self.internal_cursor+read_cunk_size)
        return result
    
    def read_byte(self):
        return int.from_bytes(self.read(1))

    def find(self, value:bytes, offset: int=None, stop: int=None):
        stop = stop if stop else self.size()
        read_len = len(value)
        if offset: self.seek(offset)
        while self.internal_cursor < stop:
            _value = self.read(self, read_len)
            if _value == value:
                self.seek(self.internal_cursor - read_len)
                return self.internal_cursor
        return  -1
    
    def close(self):
        for i in range(len(self.parts)):
            part = self.parts[i]
            try:
                # main file will be close when main DataPack is destroyed, but the other parts can/should be closed now
                part.mmap.close()
                if i>0 and part._fileno is not None:
                    os.close( part._fileno )
            except OSError as e:
                print('Error while closing file', part._path)
                print(e)