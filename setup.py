from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize([
        'src/imagecloud/native/*.pyx',
        'src/imagecloud/native/parallel/*.pyx',
    ]),
    package_data = {
        'imagecloud.native': [
            '*.pxd',
            '*.pyx'
        ],
        'imagecloud.native.parallel': [
            '*.pxd',
            '*.pyx'
        ]
    }
)