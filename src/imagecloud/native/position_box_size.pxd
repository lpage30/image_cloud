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
    NO_TRANSPOSE = -1
    FLIP_LEFT_RIGHT = 0
    FLIP_TOP_BOTTOM = 1
    ROTATE_90 = 2
    ROTATE_180 = 3
    ROTATE_270 = 4
    TRANSPOSE = 5
    TRANSVERSE = 6

cdef enum ResizeType:
    NO_RESIZE_TYPE = -1
    MAINTAIN_ASPECT_RATIO = 1
    MAINTAIN_PERCENTAGE_CHANGE = 2

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

cdef ResizeType to_resize_type(int resize_type)

cdef Size to_size(
    int width,
    int height
)

cdef float aspect_ratio(
    Size size
)

cdef float percent_change(
    int step,
    Size size
)

cdef Size adjust_size(
    int step,
    Size size,
    ResizeType resize_type
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
    ResizeType resize_type
)

cdef SampledResize sample_resize_to_area(
    Size size,
    int area,
    int step_size,
    ResizeType resize_type
)