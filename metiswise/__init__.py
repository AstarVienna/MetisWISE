# On some operating systems (e.g. Guix), it is necessary to import zlib before
# importing cpl or numpy, otherwise this error might occur:
# ImportError: libz.so.1: cannot open shared object file: No such file or directory
# zlib is therefore imported here just to be sure it is imported first.
import zlib

__all__ = ['zlib']
