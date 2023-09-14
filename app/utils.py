import os
import shutil
import math
from app.utils_file     import fopen, fmap

def xorBytes(value, key, index):
    keyLen = len(key)
    l = list(value)
    x = []
    i = index
    for el in l:
        x.append( el ^ key[i % keyLen] )
        i += 1
    return bytes(x)

def checkValidDataPack(path):
    data_pack = fopen( path=path )

    data_pack_map = fmap( file = data_pack )

    header = data_pack_map.read(5)

    valid = 0

    if header == b'\x71\x40\xBD\x73\x93':
       valid = 1 # encrypted
    elif header == b'\x50\x4C\x50\x63\x4B':
       valid = 2 # decrypted

    os.close(data_pack)

    return valid

def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def freeDiskSpace(path = '/'):
    disk = shutil.disk_usage(path)
    return disk.free

def hasEnoughStorage(path = '/', file_size = 0):
    if freeDiskSpace(path) < file_size:
        return False
    return True

def createFolderIfDoesnt(array, key):
    for a in array:
        if a is not None:
                if a["name"] == key and a["type"] == "folder":
                    return a
    
    array.append({"type": "folder", "name": key, "size": 0, "files": 0, "children": []})
    return array[-1]

def listToTree(files, tree = []):
    for cfile in files:
        path = cfile[0].split("/")
        ctree = []
        cfolder = tree

        while len(path) > 1:
            ctree.append(createFolderIfDoesnt(cfolder, path.pop(0)))
            cfolder = ctree[-1]["children"]

        for dir in ctree:
            dir["files"] += 1
            dir["size"] += cfile[2]

        doc = {"type": "file", "name": path[0], "format": cfile[3], "full_path": cfile[0], "offset": cfile[1], "size": cfile[2]}
        if bytes(cfile[4]) != b'\x00\x00\x00\x00\x00':
            doc["extra_bytes"] = cfile[4]

        cfolder.append(doc)

    return tree

def recursiveTreeFlat(tree, flat):
    for item in tree:
        if item["type"] == "folder":
            recursiveTreeFlat(item["children"], flat)
        else:
            flat.append(item)

def treeToList(tree):
    flatList = []
    trees = tree

    if type(tree) != list:
        trees = [tree]

    recursiveTreeFlat(trees, flatList)
    return flatList

def countFilesInTree(tree):
    files = 0
    for ifile in tree:
        if ifile["type"] == "folder":
            files += ifile["files"]
        else:
            files += 1

    return files

def sizeFilesInTree(tree):
    files = 0
    for ifile in tree:
        files += ifile["size"]

    return files