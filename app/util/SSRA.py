import os, glob
from typing       import TYPE_CHECKING
if TYPE_CHECKING: from ..pack   import DataPack
else: DataPack = None
import mmap
from .bytearray import ByteArray

def read_c_string(bytes: bytes, offset: int):
    try:
        i = bytes.index(b'\x00', offset)
        c_string = bytes[offset:i]
        return c_string.decode(encoding='utf-8')
    except ValueError:
        return None

def pad_number(number: int):
    if number < 10:
        return '0' + str(number)
    else:
        return str(number)

# I need to double check this sometime in the future... maybe

class SSRA:
    pack: DataPack = None
    manifest_path: str = None
    manifest: ByteArray = None
    strings: bytes = b''

    group_names: dict[int, str] = None
    files = []

    def __init__(self, pack: DataPack):
        self.pack = pack
        self.manifest_path = pack.get_path()
        self.chunks_path = os.path.join( self.pack.parent_dir(), 'chunks' )
        manifest = ByteArray( pack.mmap() )
        self.manifest = manifest
        manifest.seek(4)
        version = manifest.read_uint32()
        manifest.read_uint32()
        chunk_count = manifest.read_uint32()
        file_count = manifest.read_uint32()
        flags = manifest.read_uint32()
        strings_offset = manifest.read_uint64()
        string_size = manifest.read_uint64()
        chunk_table_offset = manifest.read_uint64()
        file_table_offset = manifest.read_uint64()
        extra_bytes = manifest.read_uint64()

        self.strings = manifest.bytes[strings_offset:string_size+strings_offset]
        print( 'SSRA Loaded: Version:', version, 'Files', file_count )

        self.read_groups(strings_offset + string_size)
        self.read_chunks(chunk_count, chunk_table_offset)

        self.files = self.read_file_table(file_count, file_table_offset)


    def get_string(self, offset: int):
        return read_c_string(self.strings, offset)

    def list_physical_chunks(self):
        chunk_path = self.chunks_path
        try:
            paths = []
            for file in os.listdir(chunk_path):
                if file.endswith(".ssrc"):
                    paths.append( file )

            return paths
        except Exception as e:
            print(e)
            return []

    def read_groups(self, offset: int):
        self.group_names = {}
        self.manifest.seek( offset )
        if self.manifest.read_uint32() == 1397772871: # GRPS
            count = self.manifest.read_uint32()
            str_size = self.manifest.read_uint32()
            self.manifest.read_uint32()
            entries_offset = self.manifest.tell()
            str_offset = entries_offset + (count*24)
            strings = self.manifest.bytes[ str_offset : str_offset+str_size]
            for i in range(count):
                self.manifest.seek( entries_offset + (i*24) )
                index = self.manifest.read_uint32()
                name_offset = self.manifest.read_uint32()
                name = read_c_string(strings, name_offset)
                if name is not None:
                    self.group_names[index] = name

    def read_chunks(self, chunk_count: int, chunk_table_offset: int):
        self.manifest.seek(chunk_table_offset)
        chunks = []
        chunks_by_group = {}
        for i in range(chunk_count):
            chunk_id = self.manifest.read_uint32()
            group_id = self.manifest.read_uint16()
            self.manifest.read_uint16()
            uncompressed_size = self.manifest.read_uint64()
            compressed_size = self.manifest.read_uint64()
            checksum = self.manifest.read_uint64()

            chunk_name = None
            if group_id == 0xFFFF:
                raise Exception('Need to implement hotfix chunk')
            elif group_id in self.group_names:
                chunk_name = f'{self.group_names[group_id]}_b{pad_number(chunk_id)}_0.ssrc'
            else:
                chunk_name = f'{chunk_id}_{group_id}.ssrc' # ??

            chunks.append({
                'name': chunk_name,
                'id': chunk_id,
                'group': group_id,
                'uncompressed': uncompressed_size,
                'compressed': compressed_size,
                'checksum': checksum,
                'chunk': SSRChunk( chunk_name, os.path.join(self.chunks_path, chunk_name), compressed_size, uncompressed_size )
            })

        for i in chunks:
            g_id = i['group']
            if g_id not in chunks_by_group:
                chunks_by_group[g_id] = []
            chunks_by_group[g_id].append(i)

        for group in chunks_by_group:
            current_offset = 0
            chunks_by_group[group].sort(key=lambda x: x["id"])
            for i in chunks_by_group[group]:
                i['chunk'].global_offset = current_offset
                current_offset += i['uncompressed']

        self.chunks = chunks

    def read_file_table(self, count: int, offset: int):
        m = self.manifest
        m.seek(offset)
        files = []
        for i in range(count):
            hash = m.read_uint32()
            m.read_uint32()
            chunk_offset = m.read_uint64()
            compressed_size = m.read_uint32()
            uncompressed_size = m.read_uint32()
            m.read_uint32()
            name_offset = m.read_uint32()
            compressed = m.read_uint8() == 1
            encrypted = m.read_uint8() == 1
            chunk_id = m.read_uint16()
            flags = m.read_uint32()
            file_name = self.get_string(name_offset)

            chunk_owner=None

            for chunk in self.chunks:
                if (
                    chunk['group'] == chunk_id and
                    chunk['chunk'].inlcudes_offset(chunk_offset)
                ):
                    chunk_owner = chunk
                    break

            files.append({
                'name': file_name,
                'hash': hash,
                'offset': chunk_offset,
                'compressed_size': compressed_size,
                'uncompressed_size': uncompressed_size,
                'compressed': compressed,
                'encrypted': encrypted,
                'chunk_id': chunk_id,
                'flags': flags,
                'chunk': chunk_owner
            })
            
        return files

    def read_file_content(self, file_path: str):
        f = None
        for i in self.files:
            if file_path == i['name']:
                f = i
                break

        if f is None:
            print(f'File {file_path} not found in manifest.ssra')
            return None

        return f['chunk']['chunk'].get_file(f['offset'], f['compressed_size'], f['uncompressed_size'])



from .file import fopen, mmap
import zstandard
class SSRChunk:
    fileno: int = None
    name: str = None
    groups: list[int] = []
    global_offset = 0

    def __init__(self, name: str, path: str, compressed_size: int, uncompressed_size: int):
        self.name = name
        self.chunk_exists = os.path.exists(path)
        self.fileno = fopen(path, False) if self.chunk_exists else None
        self.groups = []
        self.global_offset = 0
        self.is_compressed = uncompressed_size > compressed_size
        self.compressed_size = compressed_size
        self.size = uncompressed_size
        self.available = self.chunk_exists is True
        self.zstd = zstandard.ZstdDecompressor()

    def inlcudes_offset(self, offset: int):
        return self.global_offset <= offset and self.global_offset + self.size > offset

    def get_file(self, offset: int, size: int, uncompressed: int):
        local_offset = offset -self.global_offset

        if self.available is None or self.fileno is None:
            raise Exception('no SSRC', self.name)

        _mmap = mmap(self.fileno)

        _mmap.seek(local_offset)
        data = _mmap.read(size)

        if size < uncompressed:
            data = self.zstd.decompress(data, max_output_size=uncompressed)

        return data

        