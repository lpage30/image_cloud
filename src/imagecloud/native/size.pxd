# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False

cdef enum ResizeType:
    NO_RESIZE_TYPE = -1
    MAINTAIN_ASPECT_RATIO = 1
    MAINTAIN_PERCENTAGE_CHANGE = 2

cdef ResizeType to_resize_type(int t) noexcept nogil

cdef enum Transpose:
    NO_TRANSPOSE = -1
    FLIP_LEFT_RIGHT = 0
    FLIP_TOP_BOTTOM = 1
    ROTATE_90 = 2
    ROTATE_180 = 3
    ROTATE_270 = 4
    TRANSPOSE = 5
    TRANSVERSE = 6

cdef struct Size:
    int width
    int height

cdef Size create_size(int width, int height) noexcept nogil

cdef const char* size_to_string(Size self) noexcept nogil

cdef int size_area(Size self) noexcept nogil

cdef int size_less_than(Size self, Size other) noexcept nogil

cdef Size adjust(Size self, int step, ResizeType resize_type) noexcept nogil

cdef Size transpose(Size self, Transpose transpose) noexcept nogil

cdef Size untranspose(Size self, Transpose transpose) noexcept nogil

cdef Size sampled_resize_closest_to_area(Size self, int area, int step_size, ResizeType resize_type) noexcept nogil


cdef struct WeightedSize:
    float weight
    Size size

cdef WeightedSize create_weighted_size(float weight, Size size) noexcept nogil
cdef const char* weighted_size_to_string(WeightedSize self) noexcept nogil
    
    