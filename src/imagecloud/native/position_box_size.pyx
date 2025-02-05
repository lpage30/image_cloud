# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
from libc.math cimport round, abs

cdef Position to_position(
    int left,
    int upper
):
    cdef Position r
    r.left = left
    r.upper = upper
    return r

def py_to_position(
    int left,
    int upper
) -> Position:
    return to_position(left, upper)

cdef ResizeType to_resize_type(int resize_type):
    if 1 == resize_type:
        return ResizeType.MAINTAIN_ASPECT_RATIO
    elif 2 == resize_type:
        return ResizeType.MAINTAIN_PERCENTAGE_CHANGE
    return ResizeType.NO_RESIZE_TYPE

cdef Size to_size(
    int width,
    int height
):
    cdef Size r
    r.width = width
    r.height = height
    return r

def py_to_size(
    int width,
    int height
) -> Size:
    return to_size(width, height)

cdef float aspect_ratio(
    Size size
):
    return size.width / size.height

cdef float percent_change(
    int step,
    Size size
):
    return abs(step) / size.width

cdef Size adjust_size(
    int step,
    Size size,
    ResizeType resize_type
):
    cdef int increase = 1
    cdef float pct_change = percent_change(step, size)
    if step < 0:
        increase = 0
        step = abs(step)
    
    if ResizeType.MAINTAIN_ASPECT_RATIO == resize_type:
        if 0 != increase:
            return to_size(
                size.width + step,
                int(round((size.width + step) / aspect_ratio(size)))
            )
        else:
            return to_size(
                size.width - step,
                int(round((size.width - step) / aspect_ratio(size)))
            )
    elif ResizeType.MAINTAIN_PERCENTAGE_CHANGE == resize_type:
        if 0 != increase:
            return to_size(
                size.width + int(round(pct_change * size.width)),
                size.height + int(round(pct_change * size.height))
            )
        else:
            return to_size(
                size.width - int(round(pct_change * size.width)),
                size.height - int(round(pct_change * size.height))
            )
    if 0 != increase:
        return to_size(
            size.width + step,
            size.height + step
        )
    else:
        return to_size(
            size.width - step,
            size.height - step,
        )

cdef Size transpose_size(
    Transpose transpose,
    Size size
):
    if transpose == Transpose.ROTATE_90 or transpose == Transpose.ROTATE_270:
        return to_size(size.height, size.width)
    return size

cdef Size untranspose_size(
    Transpose transpose,
    Size size
):
    return transpose_size(transpose, size)


cdef BoxCoordinates to_box(
    Position position,
    Size size
):
    cdef BoxCoordinates r
    r.left = position.left
    r.upper = position.upper
    r.right = position.left + size.width
    r.lower = position.upper + size.height
    return r

def py_to_box(
    Position position,
    Size size
) -> BoxCoordinates:
    return to_box(position, size)

cdef BoxCoordinates empty_box():
    cdef BoxCoordinates r
    r.left = -1
    r.upper = -1
    r.right = -1
    r.lower = -1
    return r

cdef int is_empty_box(
    BoxCoordinates box
):
    return 1 if box.left == -1 and box.upper == -1 and box.right == -1 and box.lower == -1 else 0

cdef BoxCoordinates remove_margin(
    int margin,
    BoxCoordinates box
):
    cdef int padding = int(margin / 2)
    cdef Position pos = to_position(box.left + padding, box.upper + padding)
    cdef Size size = to_size((box.right - padding) - pos.left, (box.lower - padding) - pos.upper)
    return to_box(pos, size)

cdef SizeDistance calculate_closest_size_distance(
    Size size,
    int area,
    int step_size,
    ResizeType resize_type
):    
    cdef Size grow_size = adjust_size(step_size, size, resize_type)
    cdef Size shrink_size = adjust_size(-1 * step_size, size, resize_type)
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


cdef SampledResize sample_resize_to_area(
    Size size,
    int area,
    int step_size,
    ResizeType resize_type
):
    cdef int sampling_count = 0
    cdef Size last_size = size
    cdef SizeDistance best_size_distance
    cdef SizeDistance last_size_distance
    cdef int last_distances[6]
    cdef int found_best = 0
    cdef SampledResize result

    while found_best == 0:
        sampling_count += 1
        best_size_distance = calculate_closest_size_distance(last_size, area, step_size, resize_type)
        
        if sampling_count == 1:
            last_size_distance = best_size_distance
            last_distances[(sampling_count - 1) % len(last_distances)] = last_size_distance.distance
            continue
        
        if last_size_distance.distance < best_size_distance.distance:
            found_best = 1
            continue
        else:
            found_best = 1
            for i in range(sampling_count-1,max(0, sampling_count - len(last_distances)),-1):
                if last_distances[i % len(last_distances)] != best_size_distance.distance:
                    found_best = 0
                    break
            if found_best != 1:
                last_distances[(sampling_count - 1) % len(last_distances)] = best_size_distance.distance
                last_size_distance = best_size_distance

    result.sampling_total = sampling_count
    result.new_size = last_size_distance.size
    return result

def py_sample_resize_to_area(
    Size size,
    int area,
    int step_size,
    ResizeType resize_type
) -> SampledResize:
    return sample_resize_to_area(size, area, step_size, resize_type)