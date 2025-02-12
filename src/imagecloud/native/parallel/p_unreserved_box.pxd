# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
from imagecloud.native.position_box_size cimport (
    BoxCoordinates,
    Position,
    ResizeType,
    Size,
    Transpose
)

cdef struct PSampledUnreservedBoxResult:
    int found
    int sampling_total
    Size new_size
    BoxCoordinates unreserved_box
    BoxCoordinates actual_box
    Transpose orientation


cdef int p_is_unreserved_position(
    unsigned int[:,:] reservation_map, 
    BoxCoordinates box,
    int parallelism,
    BoxCoordinates[::1] box_scratch_buffer
) noexcept nogil


cdef BoxCoordinates p_find_unreserved_box(
    unsigned int[:,:] reservation_map,
    Size size,
    int parallelism,
    Position[::1] position_scratch_buffer,
    BoxCoordinates[::1] box_scratch_buffer
) noexcept nogil


cdef PSampledUnreservedBoxResult p_sample_to_find_unreserved_box(
    unsigned int[:,:] reservation_map,
    Size size,
    Size min_size,
    int margin,
    ResizeType resize_type,
    int step_size,
    int parallelism,
    Position[::1] position_scratch_buffer,
    BoxCoordinates[::1] box_scratch_buffer
) noexcept nogil