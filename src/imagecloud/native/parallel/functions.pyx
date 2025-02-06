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

cdef int to_1d_array_len(Size size) noexcept nogil:
    return size.width * size.height

cdef Position to_2d_array_position(int oneDArrayPosition, int twoDArrayWidth) noexcept nogil:
    return to_position(
        int(oneDArrayPosition / twoDArrayWidth),
        int(fmod(oneDArrayPosition, twoDArrayWidth))
    )

cdef double ln_rand() noexcept nogil:
    cdef double r = rand() / float(RAND_MAX)
    return log(r)

cdef int ln_rand_int(int lower, int upper) noexcept nogil:
    cdef int diff = <int>((upper - lower) * ln_rand())
    return lower + diff

