from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize([
        'src/imagecloud/native_position_box_size.pyx',
        'src/imagecloud/native_integral_occupancy_functions.pyx'
    ]),
    package_data = {
        'imagecloud': [
            'native_position_box_size.pxd',
            'native_position_box_size.pyx',
            'native_integral_occupancy_functions.pxd',
            'native_integral_occupancy_functions.pyx'
        ]
    }
)