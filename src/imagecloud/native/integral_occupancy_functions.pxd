# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
from imagecloud.native.position_box_size cimport ( 
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

cdef is_free_position(unsigned int[:,:] occupancy_map, BoxCoordinates box)

cdef find_free_box(unsigned int[:,:] occupancy_map, Size size, random_state)

cdef sample_to_find_free_box(
    unsigned int[:,:] occupancy_map, 
    Size size,
    Size min_size,
    int margin,
    int maintain_aspect_ratio, # false(0)/true(non-zero),
    int step_size,
    random_state
)