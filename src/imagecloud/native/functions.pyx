# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False

from libc.math cimport log, round, fmod
from libc.stdlib cimport rand, srand, RAND_MAX
from libc.time cimport time
from imagecloud.native.position_box_size cimport (
    Size,
    to_position
)

srand(time(NULL))

cdef int to_one_dimension_array_len(
    Size two_dimension_array_size
) noexcept nogil:
    return two_dimension_array_size.width * two_dimension_array_size.height

cdef Position to_two_dimension_array_position(
    int one_dimension_array_position,
    int two_dimension_array_width
) noexcept nogil:
    return to_position(
        <int>(one_dimension_array_position / two_dimension_array_width),
        <int>fmod(one_dimension_array_position, two_dimension_array_width)
    )

cdef double ln_rand() noexcept nogil:
    cdef double r = rand() / float(RAND_MAX)
    return log(r)

cdef int ln_rand_int(int lower, int upper) noexcept nogil:
    cdef int diff = <int>((upper - lower) * ln_rand())
    return lower + diff

