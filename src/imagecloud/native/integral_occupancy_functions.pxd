# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
from imagecloud.native.position_box_size cimport (
    ResizeType,
    Size,
    BoxCoordinates,
    Transpose
)

cdef struct SampledFreeBoxResult:
    int found
    int sampling_total
    Size new_size
    BoxCoordinates free_box
    BoxCoordinates actual_box
    Transpose orientation

cdef int is_free_position(
    unsigned int[:,:] occupancy_map, 
    BoxCoordinates box
)

cdef BoxCoordinates find_free_box(
    unsigned int[:,:] occupancy_map,
    unsigned int[:] position_scratch_buffer,
    Size size, random_state
)

cdef SampledFreeBoxResult sample_to_find_free_box(
    unsigned int[:,:] occupancy_map,
    unsigned int[:] position_scratch_buffer,
    Size size,
    Size min_size,
    int margin,
    ResizeType resize_type,
    int step_size,
    random_state
)