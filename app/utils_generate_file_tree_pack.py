import os
import re
from pathvalidate       import sanitize_filepath
from app.utils_file     import fopen, fmap
from app.constants      import KEY
from app.utils          import xorBytes, listToTree

PACK_FILE_HEADER_LENGTH = 15 # 11 known and 4 extra 

class fake_signal(): # If progress signal is missing
    def emit(val):
        ''''''

def get_params(header):

    container_length = int.from_bytes( header[ :4 ],   byteorder='little', signed=False )

    path_length      = int.from_bytes( header[ 5:6 ],  byteorder='little', signed=False )

    data_length      = int.from_bytes( header[ 6:10 ], byteorder='little', signed=False )

    extra_bytes      = list( header[10: ] )

    return container_length, path_length, data_length, extra_bytes

def generate_pack_tree(path, decrypted, progress_callback = fake_signal):
    func = generate_encrypted_tree

    if decrypted:
        func = generate_decrypted_tree

    return func(path, progress_callback.emit)


def generate_decrypted_tree(pack_path, callback):
    key = KEY

    pack_file = fopen( path=pack_path )

    pack_map = fmap( file = pack_file )

    files = []
    perc = 0
    fileMapLength = pack_map.size()

    while True:
        cursor = pack_map.find(b'\x02', pack_map.tell())

        current_perc = int(cursor / (fileMapLength / 100))
        if current_perc > perc:
            perc = current_perc
            callback(perc)

        if cursor == -1:
            callback(100) # end of file not found -> 100%
            break

        pack_map.seek(cursor - 4)

        container_length, path_length, data_length, extra_bytes = get_params(pack_map.read(PACK_FILE_HEADER_LENGTH))

        if container_length == path_length + data_length + 19: # make sure it's a valid file

            name = sanitize_filepath(pack_map.read(path_length).decode("utf-8", "ignore"))

            fileFormat = re.search("\.([a-zA-Z0-9]+)$", name)

            if fileFormat is None:
                pack_map.seek(cursor + 1)
                continue

            fileFormat = fileFormat.group(1)

            files.append([name, pack_map.tell(), data_length, fileFormat, extra_bytes])
            pack_map.seek(pack_map.tell() + data_length)
        else:
            pack_map.seek(cursor + 1)

    pack_map.close()
    os.close(pack_file)

    tree = listToTree(files, [])

    return tree


def generate_encrypted_tree(pack_path, callback):
    key = KEY

    pack_file = fopen( path=pack_path )

    pack_map = fmap( file = pack_file )

    files = []
    perc = 0
    cursor = 0
    fileMapLength = pack_map.size()

    while cursor < fileMapLength - 19:

        current_perc = int(cursor / (fileMapLength / 100))
        if current_perc > perc:
            perc = current_perc
            callback(perc)

        pack_map.seek(cursor)
        currentByte = pack_map.read_byte()
        if currentByte ^ key[ cursor % len(key) ] == 2:
            pack_map.seek( cursor - 4 )
            container_length, path_length, data_length, extra_bytes = get_params( xorBytes(pack_map.read(PACK_FILE_HEADER_LENGTH), key, cursor - 4 ) ) # pack_map.tell() - PACK_FILE_HEADER_LENGTH = cursor - 4
            if container_length == path_length + data_length + 19: # make sure it's a valid file

                    name = sanitize_filepath( xorBytes(pack_map.read(path_length), key,  pack_map.tell() - path_length).decode("utf-8", "ignore"))

                    fileFormat = re.search("\.([a-zA-Z0-9]+)$", name)

                    if fileFormat is None:
                        cursor += 1
                        continue

                    fileFormat = fileFormat.group(1)

                    files.append([name, pack_map.tell(), data_length, fileFormat, extra_bytes])
                    cursor = pack_map.tell() + data_length
            else:
                cursor += 1
        else:
            cursor += 1

    pack_map.close()
    os.close(pack_file)

    tree = listToTree(files, [])

    return tree