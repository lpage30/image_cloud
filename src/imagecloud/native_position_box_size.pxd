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

cdef to_position(int left, int upper)


cdef to_size(int width, int height)

cdef adjust_size(int step, Size size, int maintain_aspect_ratio)

cdef transpose_size(Transpose transpose, Size size)

cdef untranspose_size(Transpose transpose, Size size)


cdef to_box(Position position, Size size)

cdef remove_margin(int margin, BoxCoordinates box)