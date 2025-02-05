# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False

cdef struct Position:
    int left
    int upper

cdef struct Size:
    int width
    int height

cdef struct BoxCoordinates:
    int left
    int upper
    int right
    int lower

cdef enum Transpose:
    NONE = -1
    FLIP_LEFT_RIGHT = 0
    FLIP_TOP_BOTTOM = 1
    ROTATE_90 = 2
    ROTATE_180 = 3
    ROTATE_270 = 4
    TRANSPOSE = 5
    TRANSVERSE = 6

cdef struct SizeDistance:
    Size size
    int distance

cdef struct SampledResize:
    int sampling_total
    Size new_size    

cdef Position to_position(
    int left,
    int upper
)

cdef Size to_size(
    int width,
    int height
)

cdef Size adjust_size(
    int step,
    Size size,
    int maintain_aspect_ratio
)

cdef Size transpose_size(
    Transpose transpose,
    Size size
)

cdef Size untranspose_size(
    Transpose transpose,
    Size size
)

cdef BoxCoordinates to_box(
    Position position,
    Size size
)

cdef BoxCoordinates empty_box()

cdef int is_empty_box(
    BoxCoordinates box
)

cdef BoxCoordinates remove_margin(
    int margin,
    BoxCoordinates box
)

cdef SizeDistance calculate_closest_size_distance(
    Size size,
    int area,
    int step_size,
    int maintain_aspect_ratio
)

cdef SampledResize sample_resize_to_area(
    Size size,
    int area,
    int step_size,
    int maintain_aspect_ratio
)