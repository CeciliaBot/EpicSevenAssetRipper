
from app.constants    import KEY
import os
import re
import json
import pathlib
import importlib
from pathvalidate     import sanitize_filepath
from app.utils_file   import fopen, fwrite, fmap
from app.utils        import xorBytes, hasEnoughStorage, countFilesInTree, sizeFilesInTree

# Load all optional modules in before and after hooks
hooks = {}
try:
    for hook in ['before', 'after']:
        hooks[hook] = {}
        path = os.path.join('app', 'hooks', hook + '_write')
        files = os.listdir(path)
        for file in files:
            extension = re.search("(.+?)\.py$", file)
            if extension:
                ext = extension.group(1)
                spec = importlib.util.spec_from_file_location(ext, os.path.join(path, file))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # add module to hooks dictionary
                hooks[hook][ext] = module
except:
    pass

def readBytesWhileDecrypting(file, size, key, offset):
    return xorBytes(file.read(size), key, offset)

def readBytesPlain(file, size, key, offset):
    return file.read(size)

def callHooks(cycle, file_format, file_path, tree_file, data_bytes):
    try:
        hooks[cycle][file_format].main(file_path, data_bytes, tree_file)
    except KeyError: # no hook for file type
        pass

class ExtractFiles():
    def __init__(self, path, pack_file, files, pack_decrypted, progress_callback = lambda val: print(val)):
        self.folder_path = path

        self.pack_file = fopen( path = pack_file )

        self.pack_map = fmap( file = self.pack_file )

        self.fileList = files

        if type(files) != list:
            self.fileList = [files]

        required_space = sizeFilesInTree(self.fileList)
        disk = os.path.split(self.folder_path)

        if hasEnoughStorage(disk[0], required_space) == False:
            raise NotEnoughSpaceOnDisk("Not enough space on the disk to write all the files!\n\nDisk space: " + convert_size(freeDiskSpace(disk[0])) + "\nFile size: "  + convert_size(required_space))

        self.readBytes = readBytesWhileDecrypting

        if pack_decrypted:
            self.readBytes = readBytesPlain

        self.numberOfFiles = countFilesInTree(self.fileList)
        self.filesWritten = 0

        self.write_folder(self.folder_path, self.fileList, self.pack_map, progress_callback.emit)

        self.pack_map.close()
        os.close(self.pack_file)

        print("done")


    def write_folder(self, flat_path, array, mmapfile, update):
        pathlib.Path(flat_path).mkdir(parents=True, exist_ok=True) # Create folder if doesn't exist

        for ifile in array:
            if ifile["type"] == 'folder':
                self.write_folder( os.path.join(flat_path, ifile["name"]), ifile["children"], mmapfile, update )
            else:
                if "color" in ifile:
                    if ifile["color"] == "red": # deleted file skip
                        continue
                
                update( int(self.filesWritten / self.numberOfFiles * 100)) # , ifile["name"]
                mmapfile.seek(ifile["offset"])
                writing_path = os.path.join( flat_path, sanitize_filepath(ifile["name"]) )
                data = self.readBytes( mmapfile, ifile["size"], KEY, ifile["offset"] )
                callHooks("before", ifile["format"], writing_path, ifile, data)
                fwrite(
                    path = writing_path,
                    container = data
                )
                callHooks("after", ifile["format"], writing_path, ifile, data)
                self.filesWritten += 1