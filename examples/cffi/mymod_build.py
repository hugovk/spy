import os
from cffi import FFI
ffibuilder = FFI()

ffibuilder.cdef("""
    int add(int x, int y);
""")

src = """
int32_t spy_mymod$add(int32_t x, int32_t y);

#define add spy_mymod$add
"""

SPY_ROOT = '/home/antocuni/anaconda/spy'
if 'pyodide' in os.environ:
    # building for pyodide
    TARGET = 'emscripten'
else:
    TARGET = 'native'

ffibuilder.set_source(
    "mymod",
    src,
    sources=['mymod.c'],
    libraries=['spy'],
    define_macros=[
        (f'SPY_TARGET_{TARGET.upper()}', None),
        ('SPY_RELEASE', None),
    ],
    include_dirs=[f'{SPY_ROOT}/spy/libspy/include'],
    library_dirs=[f'{SPY_ROOT}/spy/libspy/build/{TARGET}/release'],
)


if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
