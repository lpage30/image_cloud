# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
from libc.math cimport round, abs

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


cdef to_position(int left, int upper):
    cdef Position r
    r.left = left
    r.upper = upper
    return r

def py_to_position(int left, int upper):
    return to_position(left, upper)

cdef to_size(int width, int height):
    cdef Size r
    r.width = width
    r.height = height
    return r

def py_to_size(int width, int height):
    return to_size(width, height)

cdef adjust_size(int step, Size size, int maintain_aspect_ratio):
    cdef int increase = 1
    cdef double percent_change = 1.0
    cdef Size step_size = to_size(0,0)
    if step < 0:
        increase = 0
        step = abs(step)
    
    if 0 < maintain_aspect_ratio:
        percent_change = step / size.width
        step_size = to_size(
            int(round(percent_change * size.width)),
            int(round(percent_change * size.height))
        )
    else:
        step_size = to_size(step, step)

    if 0 != increase:
        return to_size(size.width + step_size.width, size.height + step_size.height)
    else:
        return to_size(size.width - step_size.width, size.height - step_size.height)


cdef transpose_size(Transpose transpose, Size size):
    if transpose == Transpose.ROTATE_90 or transpose == Transpose.ROTATE_270:
        return to_size(size.height, size.width)
    return size

cdef untranspose_size(Transpose transpose, Size size):
    return transpose_size(transpose, size)


cdef to_box(Position position, Size size):
    cdef BoxCoordinates r
    r.left = position.left
    r.upper = position.upper
    r.right = position.left + size.width
    r.lower = position.upper + size.height
    return r

def py_to_box(Position position, Size size):
    return to_box(position, size)

cdef remove_margin(int margin, BoxCoordinates box):
    cdef int padding = int(margin / 2)
    cdef Position pos = to_position(box.left + padding, box.upper + padding)
    cdef Size size = to_size((box.right - padding) - pos.left, (box.lower - padding) - pos.upper)
    return to_box(pos, size)


