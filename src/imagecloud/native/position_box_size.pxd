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

cdef to_position(int left, int upper)

cdef empty_position()

cdef is_empty_position(Position pos)

cdef to_size(int width, int height)

cdef empty_size()

cdef adjust_size(int step, Size size, int maintain_aspect_ratio)

cdef transpose_size(Transpose transpose, Size size)

cdef untranspose_size(Transpose transpose, Size size)

cdef to_box(Position position, Size size)

cdef empty_box()

cdef is_empty_box(BoxCoordinates box)

cdef remove_margin(int margin, BoxCoordinates box)

cdef calculate_closest_size_distance(Size size, int area, int step_size, int maintain_aspect_ratio)

cdef sample_resize_to_area(Size size, int area, int step_size, int maintain_aspect_ratio)