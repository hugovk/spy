from setuptools import setup, Extension

setup(
    name="mymod",
    setup_requires=['cffi'],
    cffi_modules=["mymod_build.py:ffibuilder"],
)
