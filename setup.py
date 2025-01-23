from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("src/imagecloud/common/query_integral_image.pyx")
)