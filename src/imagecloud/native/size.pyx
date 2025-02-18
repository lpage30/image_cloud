# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
from libc.math cimport round, abs, fmod, fmin, fmax
cimport cython
cdef extern from "stdio.h":
    int snprintf(char *str, size_t size, const char *format, ...) noexcept nogil
from imagecloud.native.base_logger cimport (  
    log_debug 
)
cdef struct SizeDistance:
    Size size
    int distance

cdef SizeDistance resize_closest_to_area(Size self, int area, int step_size, ResizeType resize_type) noexcept nogil:
    cdef Size grow_size = adjust(self, step_size, resize_type)
    cdef Size shrink_size = adjust(self, -1 * step_size, resize_type)
    cdef int grow_distance = abs(area - (grow_size.width * grow_size.height))
    cdef int shrink_distance = abs(area - (shrink_size.width * shrink_size.height))

    cdef SizeDistance result
    if grow_distance <= shrink_distance:
        result.size = grow_size
        result.distance = grow_distance
    else:
        result.size = shrink_size
        result.distance = shrink_distance
    return result

cdef ResizeType to_resize_type(int t) noexcept nogil:
    if 1 == t:
        return ResizeType.MAINTAIN_ASPECT_RATIO
    if 2 == t:
        return ResizeType.MAINTAIN_PERCENTAGE_CHANGE
    return ResizeType.NO_RESIZE_TYPE



cdef Size create_size(int width, int height) noexcept nogil:
    cdef Size self
    self.width = width
    self.height = height
    return self

cdef const char* size_to_string(Size self) noexcept nogil:
    cdef char sbuf[32]
    snprintf(sbuf, 32, "Size(%d,%d)", self.width, self.height)
    return sbuf

cdef int size_area(Size self) noexcept nogil:
    return self.width * self.height

cdef int size_less_than(Size self, Size other) noexcept nogil:
    if self.width < other.width or self.height < other.height:
        return 1
    return 0
cdef Size adjust(Size self, int step, ResizeType resize_type) noexcept nogil:
    cdef float pct_change = abs(step) / self.width
    cdef float aspect_ratio = self.width / self.height
    
    if ResizeType.MAINTAIN_ASPECT_RATIO == resize_type:
        return Size(
            self.width + step,
            <int>round((self.width + step) / aspect_ratio)
        )
    elif ResizeType.MAINTAIN_PERCENTAGE_CHANGE == resize_type:
        if 0 <= step:
            return Size(
                self.width + <int>round(pct_change * self.width),
                self.height + <int>round(pct_change * self.height)
            )
        else:
            return Size(
                self.width - <int>round(pct_change * self.width),
                self.height - <int>round(pct_change * self.height)
            )
    return Size(
        self.width + step,
        self.height + step
    )

cdef Size transpose(Size self, Transpose transpose) noexcept nogil:
    if transpose == Transpose.ROTATE_90 or transpose == Transpose.ROTATE_270:
        return create_size(self.height, self.width)
    return self

cdef Size untranspose(Size self, Transpose transpose) noexcept nogil:
    if transpose == Transpose.ROTATE_90 or transpose == Transpose.ROTATE_270:
        return create_size(self.height, self.width)
    return self

cdef Size sampled_resize_closest_to_area(Size self, int area, int step_size, ResizeType resize_type) noexcept nogil:
    cdef int sampling_count = 0
    cdef Size last_size = self
    cdef SizeDistance best_size_distance
    cdef SizeDistance last_size_distance
    cdef int last_distances_len = 6
    cdef int last_distances[6]
    cdef int found_best = 0

    while found_best == 0:
        sampling_count += 1
        best_size_distance = resize_closest_to_area(last_size, area, step_size, resize_type)
        
        if sampling_count == 1:
            last_size_distance = best_size_distance
            last_distances[<int>fmod((sampling_count - 1), last_distances_len)] = last_size_distance.distance
            continue
        
        if last_size_distance.distance < best_size_distance.distance:
            found_best = 1
            continue
        else:
            found_best = 1
            for i in range(sampling_count-1, <int>fmax(0, sampling_count - last_distances_len),-1):
                if last_distances[<int>fmod(i, last_distances_len)] != best_size_distance.distance:
                    found_best = 0
                    break
            if found_best != 1:
                last_distances[<int>fmod((sampling_count - 1), last_distances_len)] = best_size_distance.distance
                last_size_distance = best_size_distance

    return last_size_distance.size

cdef WeightedSize create_weighted_size(float weight, Size size) noexcept nogil:
    cdef WeightedSize self
    self.weight = weight
    self.size = size
    return self

cdef const char* weighted_size_to_string(WeightedSize self) noexcept nogil:
    cdef char wbuf[64]
    snprintf(wbuf, 64, "WeightedSize(%.2f, Size(%d,%d))", self.weight, self.size.width, self.size.height)
    return wbuf


def native_create_size(
    width: int, 
    height: int
): # return native_size
    return create_size(width, height)

def native_adjust(
    native_size,
    step: int,
    resize_type: int
): # return native_size
    return adjust(native_size, step, to_resize_type(resize_type))


def native_create_weighted_size(
    weight: float,
    native_size
): # return native_weightedsize
    return create_weighted_size(weight, native_size)

def native_create_weighted_size_array(
    size: int
): # native_weighted_sizes
    cdef WeightedSize[::1] result = cython.view.array(shape=(size,), itemsize=sizeof(WeightedSize), format="f i i")
    return result

def native_resize_to_proportionally_fit(
    native_weighted_sizes,
    native_fit_size,
    resize_type: int,
    step_size: int,
    margin: int
): # return native_weighted_sizes
    """
    use weights to determine proportion of fit_size for each image
    fit each image to their proportion by iteratively changing the size until the closest fit is made
    return fitted images with their proportions
    """

    cdef ResizeType eresize_type = to_resize_type(resize_type)
    cdef WeightedSize[:] result = native_create_weighted_size_array(native_weighted_sizes.shape[0])

    cdef float total_weight = 0.0
    cdef float proportion_weight = 0.0
    cdef int fit_area = size_area(native_fit_size)
    cdef int fitted_images = 0
    cdef Size new_size
    cdef int resize_area = 0
    cdef Size sampled_resize
    cdef int index = 0
    cdef WeightedSize weighted_size

    for index in range(native_weighted_sizes.shape[0]):
        weighted_size = native_weighted_sizes[index]
        total_weight = total_weight + weighted_size.weight
    
    for index in range(native_weighted_sizes.shape[0]):
        weighted_size = native_weighted_sizes[index]
        proportion_weight = weighted_size.weight / total_weight
        resize_area = <int>round(proportion_weight * fit_area)
        new_size = adjust(weighted_size.size, margin, ResizeType.NO_RESIZE_TYPE)
        sampled_resize = sampled_resize_closest_to_area(new_size, resize_area, step_size, eresize_type)
        new_size = adjust(sampled_resize, -1 * margin, ResizeType.NO_RESIZE_TYPE)
        result[index] = create_weighted_size(weighted_size.weight, new_size)
    
    return result
