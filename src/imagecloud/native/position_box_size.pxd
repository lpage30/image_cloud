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
) noexcept nogil

cdef ResizeType to_resize_type(int resize_type) noexcept nogil

cdef Size to_size(
    int width,
    int height
) noexcept nogil

cdef float aspect_ratio(
    Size size
) noexcept nogil

cdef float percent_change(
    int step,
    Size size
) noexcept nogil

cdef Size adjust_size(
    int step,
    Size size,
    ResizeType resize_type
) noexcept nogil

cdef Size transpose_size(
    Transpose transpose,
    Size size
) noexcept nogil

cdef Size untranspose_size(
    Transpose transpose,
    Size size
) noexcept nogil

cdef BoxCoordinates to_box(
    Position position,
    Size size
) noexcept nogil

cdef BoxCoordinates empty_box() noexcept nogil

cdef int is_empty_box(
    BoxCoordinates box
) noexcept nogil

cdef BoxCoordinates remove_margin(
    int margin,
    BoxCoordinates box
) noexcept nogil

cdef SizeDistance calculate_closest_size_distance(
    Size size,
    int area,
    int step_size,
    ResizeType resize_type
) noexcept nogil

cdef SampledResize sample_resize_to_area(
    Size size,
    int area,
    int step_size,
    ResizeType resize_type
) noexcept nogil

cdef Position[::1] create_position_array(int size)

cdef Size[::1] create_size_array(int size)

cdef BoxCoordinates[::1] create_box_array(int size)


# Box parititons are the result of iteratively quartering things
cdef enum BoxPartitionType:
    FOUR = 4   # original box cut into 4 quarters
    SIXTEEN = 16   # FOUR and then each of the 4 is cut into 4 quarters
    SIXTY_FOUR = 64  # SIXTEEN and then each of the 16 is cut into 4 quarter

cdef int partition_box_into_array(
    BoxCoordinates box,
    BoxPartitionType partition_type, 
    BoxCoordinates[::1] input_output_partitions,
) noexcept nogil