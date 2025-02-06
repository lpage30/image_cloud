# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
from imagecloud.native.position_box_size cimport (
    Position,
    Size
)

cdef int to_one_dimension_array_len(
    Size two_dimension_array_size
) noexcept nogil

cdef Position to_two_dimension_array_position(
    int one_dimension_array_position,
    int two_dimension_array_width
) noexcept nogil

cdef double ln_rand() noexcept nogil

cdef int ln_rand_int(int lower, int upper) noexcept nogil
