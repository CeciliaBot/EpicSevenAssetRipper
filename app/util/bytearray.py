import struct

class ByteArray(bytearray):
    '''
        Same as bytearray but with added read, seek, tell, peek and skip. Can be used instead of io.bytesio for some methods
    '''

    _cursor = 0

    def _read(self, length:int=1): # Read n bytes and move cursor
        c = self._cursor
        self._cursor = min( len(self) , self._cursor+length )

        return self[c:self._cursor]
    
    def seek(self, index: int):
        '''
            Set the cursor's position
        '''
        self._cursor = index

    def skip(self, length: int=1):
        '''
            Advance n bytes without returning anything
        '''
        self._cursor += length

    def peek(self, length: int = 1):
        '''
            Return the next n bytes without advancing the array position
        '''
        return bytes( self[self._cursor:self._cursor+length] )
    
    def read(self, size: int = 1):
        '''
            Read and return the next n bytes
        '''
        return bytes( self._read(size if size else len(self) - self._cursor) )
    
    def tell(self):
        '''
            Return the cursor's position
        '''
        return self._cursor
    
    def read_int(self, size: int, byteorder='little', signed=False):
        '''
            Read n bytes and return them as int
        '''
        return int.from_bytes(self._read(size), byteorder=byteorder, signed=signed)

    def read_int8(self):
        return int.from_bytes(self._read(1), signed=False)
        
    def read_uint8(self):
        return int.from_bytes(self._read(1), signed=False)
        
    def read_int16(self, big = False):
        return int.from_bytes(self._read(2), byteorder='big' if big else 'little', signed=True)
        
    def read_uint16(self, big = False):
        return int.from_bytes(self._read(2), byteorder='big' if big else 'little', signed=False)
        
    def read_int32(self, big = False):
        return int.from_bytes(self._read(4), byteorder='big' if big else 'little', signed=True)
        
    def read_uint32(self, big = False):
        return int.from_bytes(self._read(4), byteorder='big' if big else 'little', signed=False)
        
    def read_int64(self, big = False):
        return int.from_bytes(self._read(8), byteorder='big' if big else 'little', signed=True)
        
    def read_uint64(self, big = False):
        return int.from_bytes(self._read(8), byteorder='big' if big else 'little', signed=False)
        
    def read_float(self, big = False):
        return struct.unpack('>f' if big else '<f', self._read(4))[0]
        
    def read_float64(self, big = False):
        return struct.unpack('>f' if big else '<f', self._read(8))[0]

    @property
    def bytes(self):
        return bytes(self)
    
    @staticmethod
    def to_int(bytes: bytes, byteorder='little', signed=False):
        return int.from_bytes(bytes, byteorder=byteorder, signed=signed)

    @staticmethod
    def to_float(bytes: bytes, byteorder='little'):
        return struct.unpack('>f' if byteorder=='big' else '<f', bytes)[0]