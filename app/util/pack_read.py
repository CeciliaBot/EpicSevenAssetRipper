import zipfile
import tarfile
import mmap
from collections  import namedtuple
from pathvalidate import sanitize_filepath
from ..constants  import KEY, KEY_LEN
from .bytearray   import ByteArray
from .types       import FileType
from .split_mmap  import FragmentedPackMemoryMap
from typing       import TYPE_CHECKING
if TYPE_CHECKING: from ..pack   import DataPack
else: DataPack = None

# Mimik tarfile info
MemberInfo = namedtuple('MemberInfo', ['name', 'size', 'offset_data', 'mtime', 'isfile'])

# data pack
E7_PACK_FILE_HEADER_LENGTH = 15 # 11 known and 4 extra 
def e7_get_params(header: bytes | bytearray):

    container_length = int.from_bytes( header[ :4 ],   byteorder='little', signed=False )

    path_length      = int.from_bytes( header[ 5:6 ],  byteorder='little', signed=False )

    data_length      = int.from_bytes( header[ 6:10 ], byteorder='little', signed=False )

    extra_bytes      = list( header[10: ] )

    return container_length, path_length, data_length, extra_bytes




class BasePackIO:
    def __init__(self, pack: DataPack):
        self.pack = pack
        self.mmap = pack.mmap()
        self.read_bytes = pack.read_bytes

    def next(self) -> MemberInfo | None:
        '''
            Get the next member
        '''
        return MemberInfo()

    def get_file_content(self, file: FileType):
        '''
            Given a file returns that file's content in bytes
        '''
        self.mmap.seek(file['offset'])

        return self.mmap.read(file['size'])

    def size(self):
        return self.mmap.size()

    def close(self):
        self.mmap.close()


class TarPack(BasePackIO):
    def __init__(self, pack: DataPack):
        super().__init__(pack)
        self.tar = tarfile.TarFile(pack.get_path(), 'r')
        self.next = self.tar.next # get the next member
    
    def get_file_content(self, file: FileType):
        self.mmap.seek(file['offset'])

        return self.read_bytes(self.mmap, file['offset'], file['size'])
    
    def close(self):
        super().close()
        self.tar.close()


class ZipPack(BasePackIO):
    _next_cursor = 0

    def __init__(self, pack: DataPack):
        super().__init__(pack)
        self.zip = zipfile.ZipFile(file=pack.get_path(), mode='r')
        self.info_table = self.zip.infolist()

    def next(self):
        l = len(self.info_table)

        while self._next_cursor < l:
            f = self.info_table[self._next_cursor]

            size = getattr( f, 'file_size' )

            self._next_cursor+=1

            if size:
                # file
                return MemberInfo(name=f.filename, size=f.file_size, offset_data=0, mtime=0, isfile=lambda:True)
            else:
                # folder
                continue
        
        return None
    
    def get_file_content(self, file: FileType):
        info = self.zip.getinfo(file['full_path'])
        if info:
            # Wrap in bytearray to keep the type consistent with the other byte readers
            return ByteArray( self.zip.read(info) )
        else:
            return ByteArray()
        
    def close(self):
        super().close()
        self.zip.close()


class EpicSevenDataPack(BasePackIO):
    find = None

    def __init__(self, pack):
        super().__init__(pack)
        self.read_bytes = pack.read_bytes
        if pack._is_encrypted:
            self.find = self._mmap_encrypted_find
            # FragmentedPackMemoryMap works with single files but adds useless overhead, only use it if necessary
            self.mmap = FragmentedPackMemoryMap(pack) if pack._parts else pack.mmap()
        else:
            self.find = self.mmap.find
    
    def _mmap_encrypted_find(self, value, offset = None, stop = None):
        f: mmap.mmap = self.mmap
        
        if offset is not None:
            f.seek(offset)
        else:
            offset = f.tell()

        if not stop:
            stop = f.size() - 1

        while offset < stop:
            
            if f.read_byte() ^ KEY[ offset % KEY_LEN ] == 2:
                return offset

            offset += 1

        return -1

    def next(self):
        f = self.mmap
        pack_read = self.pack.read_bytes
        stop = f.size() - 19

        while True:
            cursor = self.find(b'\x02', f.tell(), stop)

            if cursor == -1:
                break

            f.seek(cursor - 4)

            container_length, path_length, data_length, extra_bytes = e7_get_params(pack_read(f, cursor - 4, E7_PACK_FILE_HEADER_LENGTH))

            if container_length != path_length + data_length + 19: # Not a valid file, continue looking
                f.seek(cursor + 1)
            else:
                try:
                    # if the path is not a clean "utf-8" it will raise an exception without the "ignore"
                    # if the it's actually a file it won't trigger the exception
                    name = sanitize_filepath( pack_read(f, f.tell(), path_length).decode("utf-8") )
                    offset_data = f.tell()
                    f.seek(offset_data + data_length)
                    return MemberInfo(name=name, size=data_length, offset_data=offset_data, mtime=extra_bytes, isfile=lambda: True)
                except UnicodeDecodeError:
                    f.seek(cursor+1)
            
        return None

    def get_file_content(self, file: FileType):
        self.mmap.seek(file['offset'])
        return self.read_bytes(self.mmap, file['offset'], file['size'])


def PackFileScanner(pack: DataPack):
    if pack._type == 'zip':
        return ZipPack(pack)
    elif pack._type == 'tar':
        return TarPack(pack)
    elif pack._type == 'pack':
        return EpicSevenDataPack(pack)
