import os
import time
from itertools                           import cycle
from app.utils                           import hasEnoughStorage, convert_size, freeDiskSpace
from app.utils_file                      import fopen, fmap
from app.constants                       import KEY
from app.utils_generate_file_tree_pack   import generate_decrypted_tree
from app.utils_extract_pack              import ExtractFiles

class NotEnoughSpaceOnDisk(Exception):
    pass

def xorChunk(bytesChunk, key):
    return bytes(a ^ b for a, b in zip(bytesChunk, cycle(key)))

def decrypt(path_input, path_output, progress_callback = lambda val: print(val)):
    pack_file = fopen( path=path_input )

    map = fmap( file = pack_file )

    progress = 0
    keyLength = len(KEY)
    fileSize = map.size()

    disk = os.path.split(path_output)

    if hasEnoughStorage(disk[0], fileSize) == False:
        raise NotEnoughSpaceOnDisk("Not enough space on the disk to write the decrypted file!\n\nDisk space: " + convert_size(freeDiskSpace(disk[0])) + "\nFile size: "  + convert_size(fileSize))

    with open(path_output, 'wb') as output:
        while True:
            current_progress = int(map.tell() / fileSize * 100)
            if current_progress > progress:
                progress = current_progress
                progress_callback.emit(progress)

            decryptedChunk = xorChunk(map.read(keyLength), KEY)

            if decryptedChunk == b'': # End of file
                break

            output.write(decryptedChunk)

    map.close()
    os.close(pack_file)

    return 'Done'

def extract(file, folder, progress_callback = lambda val: print(val)):
    tree = generate_decrypted_tree(file, progress_callback.emit)
    ExtractFiles(folder, file, tree, True, progress_callback = progress_callback)
    return 'Done'