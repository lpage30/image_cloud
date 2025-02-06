# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
from imagecloud.native.position_box_size cimport (
    Position,
    Size
)

cdef int to_1d_array_len(Size size) noexcept nogil

cdef Position to_2d_array_position(int oneDArrayPosition, int twoDArrayWidth) noexcept nogil

cdef double ln_rand() noexcept nogil

cdef int ln_rand_int(int lower, int upper) noexcept nogil
