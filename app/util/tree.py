import os
from .thread            import ThreadData
from .exceptions        import OperationAbortedByUser
from .types             import FolderType, FileType
from typing             import TYPE_CHECKING
from .pack_read         import PackFileScanner


if TYPE_CHECKING:
    from ..pack         import DataPack
else:
    DataPack = None

def create_folder(name: str, files = 0, size = 0, children: list[FileType, FolderType] = None) -> FolderType:
    return {
        'type': 'folder',
        'name': name,
        'files': files,
        'size': size,
        'children': children or []
    }

def create_file(name:str, full_name: str, size:int=0, offset:int=0, extra_bytes=None ) -> FileType:
    d = {
        'type': 'file',
        'name': name,
        'full_path': full_name,
        'format': os.path.splitext(full_name)[1][1:],
        'size': size,
        'offset': offset,
    }
    if extra_bytes:
        d['extra_bytes'] = extra_bytes

    return d

def folder_increase_size_files(folder: FolderType, size_change: int = 0, files_count: int = 0):
    folder['size'] += size_change
    folder['files'] += files_count


# class PackFileScanner:
#     pack = None
#     file = None
#     find = None
#     temp_zip_arr: list[zipfile.ZipInfo] = []
#     offset = 0

#     def __init__(self, pack: DataPack):
#         self.pack = pack
#         if pack._type == 'tar':
#             self.file = tarfile.TarFile(pack._path, 'r')
#             self.next = self.file.next

#         elif pack._type == 'zip':
#             self.file = zipfile.ZipFile(pack._path, 'r')
#             self.temp_zip_arr = self.file.infolist()
#             self.next = self._zip_next

#         else:
#             self.file = pack.mmap()
#             self.next = self._pack_next
#             if pack._is_encrypted:
#                 self.find = self._mmap_encrypted_find
#             else:
#                 self.find = self.file.find

#     def _zip_next(self):
#         l = len(self.temp_zip_arr)

#         while self.offset < l:
#             f = self.temp_zip_arr[self.offset]

#             size = getattr( f, 'file_size' )
#             self.offset+=1

#             if size:
#                 # file
#                 return MemberInfo(name=f.filename, size=f.file_size, offset_data=0, mtime=0, isfile=lambda:True)
#             else:
#                 # folder
#                 continue
        
    
#     # def find(*args):
#     #     pass

#     # replace the memory map function with this if pack is encrypted
#     def _mmap_encrypted_find(self, value, offset = None, stop = None):
#         f: mmap.mmap = self.file
        
#         if offset is not None:
#             f.seek(offset)
#         else:
#             offset = f.tell()

#         if not stop:
#             stop = f.size() - 1

#         while offset < stop:
            
#             if f.read_byte() ^ KEY[ offset % KEY_LEN ] == 2:
#                 return offset

#             offset += 1

#         return -1

#     def _pack_next(self):
#         f = self.file
#         pack_read = self.pack.read_bytes
#         stop = f.size() - 19

#         while True:
#             cursor = self.find(b'\x02', f.tell(), stop=stop)

#             if cursor == -1:
#                 break

#             f.seek(cursor - 4)

#             container_length, path_length, data_length, extra_bytes = get_params(pack_read(f, cursor - 4, PACK_FILE_HEADER_LENGTH))

#             if container_length != path_length + data_length + 19: # Not a valid file, continue looking
#                 f.seek(cursor + 1)
#             else:
#                 try:
#                     # if the path is not a clean "utf-8" it will raise an exception without the "ignore"
#                     # if the it's actually a file it won't trigger the exception
#                     name = sanitize_filepath( pack_read(f, f.tell(), path_length).decode("utf-8") )
#                     offset_data = f.tell()
#                     f.seek(offset_data + data_length)
#                     return MemberInfo(name=name, size=data_length, offset_data=offset_data, mtime=extra_bytes, isfile=lambda: True)
#                 except UnicodeDecodeError:
#                     f.seek(cursor+1)
            
#         return None
            
#     def next(self) -> MemberInfo | None:
#         '''
#             Replace this method with self._pack_next or tarlib.next or similar
#         '''
#         return None

#     def close(self):
#         if self.file:
#             self.file.close()



def generate_dict_tree(pack: DataPack, thread: ThreadData):
    f = PackFileScanner(pack)

    progress_percentage = 0

    res: list[FolderType, FileType] = []

    size = f.size() # os.path.getsize(pack._path)

    files_found = 0

    while True:

        if thread.is_stopping():
            return res
            # raise OperationAbortedByUser('Operation was interrupted by the user')

        member = f.next()

        if not member:
            break

        is_file = member.isfile()
        if not is_file:
            continue
        
        segments = member.name.split('/')
        direct = res
        parents: list[FolderType] = []

        while True:
            if len(segments) > 1:
                s = segments.pop(0)
                x = False
                for item in direct:
                    if item['type'] == 'folder' and item['name'] == s:
                        direct = item['children']
                        parents.append(item)
                        x = True
                        break
                # Not found
                if not x:
                    direct.append( create_folder( s ) )
                    parents.append(direct[-1])
                    direct = direct[-1]['children'] # return the items just created
            else:
                break

        direct.append( create_file(
            segments[0],
            member.name,
            member.size,
            member.offset_data,
            extra_bytes=member.mtime if isinstance(member.mtime, list) and bytes(member.mtime) != b'\x00\x00\x00\x00\x00' else None
        ))

        files_found+=1
        
        
        for parent in parents: # For each parent in the tree update their size
            folder_increase_size_files(parent, files_count=1, size_change=member.size)

        percentage = round((member.offset_data + member.size)/size*100)

        if percentage > progress_percentage:
            progress_percentage = percentage
            thread.progress((percentage,)) # keep the comma 

    f.close()
    print(f'{files_found} files found!')
    return res

def count_files_tree(file_tree):
    file_count = 0

    def recursive(files):
        nonlocal file_count
        for file in files:
            if file['type'] == 'folder':
                recursive(file['children'])
            else:
                if not file.get('ignore', False):
                    file_count+=1

    recursive(file_tree)

    return file_count

def count_size_tree(file_tree):
    file_size = 0

    def recursive(files):
        nonlocal file_size
        for file in files:
            if file['type'] == 'folder':
                recursive(file['children'])
            else:
                if not file.get('ignore', False):
                    file_size+=file['size']

    recursive(file_tree)

    return file_size



