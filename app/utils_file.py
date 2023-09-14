import os
import mmap
import platform

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

def fwrite(path, container):
   f = fopen(path, True)
   os.write(f, container)
   os.close(f)

def fmap(file, length = 0, offset = 0, write = False): # Cross platform File Map
   access = None

   if platform.system() == 'Windows':
      if write:
         access = mmap.ACCESS_WRITE
      else:
         access = mmap.ACCESS_READ
   else:
      if write:
         access = mmap.PROT_WRITE
      else:
         access = mmap.PROT_READ

   return mmap.mmap(fileno = file, length = length, offset = offset, access = access)