# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
cimport cython
from libc.math cimport round
cdef extern from "stdio.h":
    int snprintf(char *str, size_t size, const char *format, ...) noexcept nogil
from imagecloud.native.size cimport create_size
from imagecloud.native.base_logger cimport  (
    log_error
)



cdef Box create_box(int left, int upper, int right, int lower) noexcept nogil:
    cdef Box self
    self.left = left
    self.upper = upper
    self.right = right
    self.lower = lower
    return self

cdef const char* box_to_string(Box self) noexcept nogil:
    cdef char bbuf[64]
    snprintf(bbuf, 64, "Box(%d,%d,%d,%d)", self.left, self.upper, self.right, self.lower)
    return bbuf

cdef int box_width(Box self) noexcept nogil:
    return self.right - self.left

cdef int box_height(Box self) noexcept nogil:
    return self.lower - self.upper

cdef int box_area(Box self) noexcept nogil:
    return box_width(self) * box_height(self)

cdef Size size(Box self) noexcept nogil:
    return create_size(
        box_width(self),
        box_height(self)
    )
cdef int box_equals(Box self, Box other) noexcept nogil:
    if other.left == self.left and other.upper == self.upper and other.right == self.right and other.lower == self.lower:
        return 1
    return 0

cdef Box g_empty_box = create_box(
    -1,
    -1,
    -1,
    -1
)
cdef Box empty_box() noexcept nogil:
    global g_empty_box
    return g_empty_box

cdef int is_empty(Box self) noexcept nogil:
    global g_empty_box
    return box_equals(self, g_empty_box)

cdef int contains(Box self, Box other) noexcept nogil:
    if (self.left <= other.left and self.upper <= other.upper and 
        self.right >= other.right and self.lower >= other.lower):
        return 1
    return 0

cdef Box add_margin(Box self, int margin) noexcept nogil:
    cdef int padding = <int>round(margin / 2)
    return create_box(
        self.left - padding,
        self.upper - padding,
        self.right + padding,
        self.lower + padding
    )

cdef Box remove_margin(Box self, int margin) noexcept nogil:
    cdef int padding = <int>round(margin / 2)
    return create_box(
        self.left + padding,
        self.upper + padding,
        self.right - padding,
        self.lower - padding
    )

def native_create_box(
    left: int,
    upper: int,
    right: int,
    lower: int
): # return native_box
    return create_box(left, upper, right, lower)