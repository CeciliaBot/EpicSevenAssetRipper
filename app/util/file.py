import os
import mmap as memory_map
import platform
from pathlib import Path
import math

def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def path_exists(path):
   return Path(path).exists()

def get_pack_parts(path):
    if path_exists(path + '~1'):
        pack_index = 1
        _parts = [ path, path + '~1' ]
        while True:
            pack_index+=1
            if path_exists(path + f'~{pack_index}'):
                _parts.append( path + f'~{pack_index}')
            else:
                break
        return _parts
    return None

def fopen(path, write = False): # Cross platform os.open ( Used with fmap() )
    access = None

    if platform.system() == 'Windows':
        if write:
            access = os.O_CREAT | os.O_RDWR | os.O_BINARY
        else:
            access = os.O_RDONLY | os.O_BINARY
    else:
        if write:
            access = os.O_CREAT | os.O_RDWR
        else:
            access = os.O_RDONLY
   
    return os.open(path, access)

def mmap(file, length = 0, offset = 0, write = False): # Cross platform File Map
    access = None

    if platform.system() == 'Windows':
        if write:
            access = memory_map.ACCESS_WRITE
        else:
            access = memory_map.ACCESS_READ
    else:
        if write:
            access = memory_map.PROT_WRITE
        else:
            access = memory_map.PROT_READ

    return memory_map.mmap(fileno = file, length = length, offset = offset, access = access)