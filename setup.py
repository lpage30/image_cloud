from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("src/imagecloud/native_integral_occupancy_functions.pyx")
)