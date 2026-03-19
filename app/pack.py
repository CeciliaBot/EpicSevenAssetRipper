from .settings        import getAutosaveFileTree
from .util.file       import path_exists, get_pack_parts, mmap, fopen
from .constants       import KEY, KEY_LEN
from .util.types      import FileTreeType
from .util.tree       import generate_dict_tree
from .util.thread     import ThreadData
from .util.exceptions import NotDataPackZip
from .util.bytearray  import ByteArray
from .extract         import extract
import os
import json
from typing           import Literal

class DataPack:
    _path: str = None
    _file: int = None
    _tree: FileTreeType = None
    _type: Literal['zip', 'tar', 'pack'] = None
    _is_encrypted: bool = False
    _parts: list[str] = None

    def __init__(self, path):
        if path_exists(path):
            self._path = path
            self._file = fopen( self._path )
            self.try_automaitc_tree_read()
            ext = os.path.splitext(self._path)[1]
            if ext == '.tar':
                self._type = 'tar'
            elif ext == '.zip':
                self._type = 'zip'
                self.read_bytes = self._zip_read_bytes
            else:
                fmap = self.mmap()
                header = fmap.read(5)
                fmap.close()
                self._type= 'pack'
                if header == b'\x71\x40\xBD\x73\x93':
                    self._is_encrypted = True
                    self.read_bytes = self._xor_read
                    self._parts = get_pack_parts(self._path)
                    if self._parts: print(f'Loaded data.pack and ~{len(self._parts) - 1} parts!')
                elif header == b'\x50\x4C\x50\x63\x4B':
                    self._is_encrypted = False
                else:
                    raise NotDataPackZip('not_data_pack_or_zip')

    def get_path(self):
        return self._path

    def exists(self):
        return self._path and path_exists(self._path)
    
    def parent_dir(self):
        return os.path.dirname( self._path )
    
    def fileno(self):
        return self._file

    def tree(self):
        return self._tree
    
    def set_tree(self, tree: FileTreeType):
        self._tree = tree

    def try_automaitc_tree_read(self):
        if self.parent_dir():
            possible_path = os.path.join( self.parent_dir(), 'tree.json' )
            try:
                self.load_json_tree_from_path(possible_path)
            except:
                pass

    def load_json_tree_from_path(self, path: str):
        if path_exists( path ):
            with open(path, 'r') as f:
                self.set_tree( json.load(f) )

    def file_open(self):
        return fopen( self._path )

    def mmap(self):
        '''
            Return memory map of the file, remember to close() once you are done
        '''
        return mmap(file=self.fileno() )

    def get_file_from_tree(self, file_path):
        # Given a string file path reutrn the file's dictionary: for example 'face/c1002_s.png'
        if self.tree() == None:
            return None
        
        tfile = file_path.split('/')

        cfile = self.tree()

        for direct in tfile:
            found = False
            if cfile:
                for f in cfile:
                    if f['name'] == direct:
                        cfile = f.get('children', f)
                        found = True
                        break
                if found == False:
                    cfile = None
                    break

        return cfile

    @staticmethod
    def _xor_read(fmap, offset: int, size: int) -> ByteArray:
        '''
            This method doesn't move the cursor, offset is only used for 
        '''
        l = ByteArray(fmap.read(size))
        for i in range(len(l)):
            l[i] = l[i] ^ KEY[ (offset+i) % KEY_LEN]
        return l
    
    @staticmethod
    def _plain_read(fmap, _: int, size: int):
        return ByteArray( fmap.read(size) )

    @staticmethod
    def _zip_read_bytes(file, offset, size):
        return 

    # Test
    read_bytes = _plain_read

    def build_tree(self, thread: ThreadData = None):
        if not thread:
            thread=ThreadData()
        self._tree = generate_dict_tree(self, thread=thread)

        if getAutosaveFileTree():
            with open(os.path.join(self.parent_dir(), 'tree.json'), 'w') as f:
                f.write(json.dumps(self._tree))

    def extract(self, files: FileTreeType, path: str, thread: ThreadData = None):
        if not thread:
            thread=ThreadData()
        extract(self, files, path, thread=thread)

    def destroy(self) -> None:
        try:
            if self.fileno() is not None:
                os.close( self.fileno() )
            self._file = None
            self._path = None
            self.set_tree(None)
            self._type = None
            self._is_encrypted = None
        except Exception:
            pass