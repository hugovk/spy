from cffi import FFI
ffibuilder = FFI()

ffibuilder.cdef("""
    int add(int x, int y);
""")


src = """
int32_t spy_mymod$add(int32_t x, int32_t y);

#define add spy_mymod$add
"""
ffibuilder.set_source(
    "mymod",
    src,
    sources=['mymod.c'],
    libraries=['spy'],
    define_macros=[
        ('SPY_TARGET_NATIVE', None),
        ('SPY_RELEASE', None),
    ],
    include_dirs=['/home/antocuni/anaconda/spy/spy/libspy/include'],
    #library_dirs=['/home/antocuni/anaconda/spy/spy/libspy/build/emscripten/release'],
    library_dirs=['/home/antocuni/anaconda/spy/spy/libspy/build/native/release'],
)


if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
