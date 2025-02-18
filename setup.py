from setuptools import setup, Extension
from sys import platform
from Cython.Build import cythonize
# OSX needs some 'special attention': https://stackoverflow.com/questions/28010801/compiling-parallelized-cython-with-clang
# https://github.com/debsankha/cython-parallel-mac-m1
extra_link_args = ['-fopenmp']
#if platform == 'darwin':
#    extra_link_args = ['-lmpi', '-lomp']

extensions = [
    Extension(
        '*',
        ['src/imagecloud/native/*.pyx'],
        extra_compile_args=['-fopenmp'],
        extra_link_args=extra_link_args,        
    )
]
extensions_package_data = {
    'imagecloud.native': [
        '*.pxd',
        '*.pyx'
    ]
}
setup(
    ext_modules=cythonize(extensions),
    package_data = extensions_package_data
)