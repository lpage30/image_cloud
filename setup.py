from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize([
        'src/imagecloud/native/*.pyx',
    ]),
    package_data = {
        'imagecloud.native': [
            '*.pxd',
            '*.pyx'
        ]
    }
)