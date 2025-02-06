# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
from libc.math cimport round, abs, fmod, fmin, fmax
cimport cython

cdef Position to_position(
    int left,
    int upper
) noexcept nogil:
    cdef Position r
    r.left = left
    r.upper = upper
    return r

def py_to_position(
    int left,
    int upper
) -> Position:
    return to_position(left, upper)

cdef ResizeType to_resize_type(int resize_type) noexcept nogil:
    if 1 == resize_type:
        return ResizeType.MAINTAIN_ASPECT_RATIO
    elif 2 == resize_type:
        return ResizeType.MAINTAIN_PERCENTAGE_CHANGE
    return ResizeType.NO_RESIZE_TYPE

cdef Size to_size(
    int width,
    int height
) noexcept nogil:
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
) noexcept nogil:
    return size.width / size.height

cdef float percent_change(
    int step,
    Size size
) noexcept nogil:
    return abs(step) / size.width

cdef Size adjust_size(
    int step,
    Size size,
    ResizeType resize_type
) noexcept nogil:
    cdef int increase = 1
    cdef float pct_change = percent_change(step, size)
    if step < 0:
        increase = 0
        step = abs(step)
    
    if ResizeType.MAINTAIN_ASPECT_RATIO == resize_type:
        if 0 != increase:
            return to_size(
                size.width + step,
                <int>round((size.width + step) / aspect_ratio(size))
            )
        else:
            return to_size(
                size.width - step,
                <int>round((size.width - step) / aspect_ratio(size))
            )
    elif ResizeType.MAINTAIN_PERCENTAGE_CHANGE == resize_type:
        if 0 != increase:
            return to_size(
                size.width + <int>round(pct_change * size.width),
                size.height + <int>round(pct_change * size.height)
            )
        else:
            return to_size(
                size.width - <int>round(pct_change * size.width),
                size.height - <int>round(pct_change * size.height)
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
) noexcept nogil:
    if transpose == Transpose.ROTATE_90 or transpose == Transpose.ROTATE_270:
        return to_size(size.height, size.width)
    return size

cdef Size untranspose_size(
    Transpose transpose,
    Size size
) noexcept nogil:
    return transpose_size(transpose, size)


cdef BoxCoordinates to_box(
    Position position,
    Size size
) noexcept nogil:
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

cdef BoxCoordinates empty_box() noexcept nogil:
    cdef BoxCoordinates r
    r.left = -1
    r.upper = -1
    r.right = -1
    r.lower = -1
    return r

cdef int is_empty_box(
    BoxCoordinates box
) noexcept nogil:
    return 1 if box.left == -1 and box.upper == -1 and box.right == -1 and box.lower == -1 else 0

cdef BoxCoordinates remove_margin(
    int margin,
    BoxCoordinates box
) noexcept nogil:
    cdef int padding = <int>(margin / 2)
    cdef Position pos = to_position(box.left + padding, box.upper + padding)
    cdef Size size = to_size((box.right - padding) - pos.left, (box.lower - padding) - pos.upper)
    return to_box(pos, size)

cdef SizeDistance calculate_closest_size_distance(
    Size size,
    int area,
    int step_size,
    ResizeType resize_type
) noexcept nogil:    
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
) noexcept nogil:
    cdef int sampling_count = 0
    cdef Size last_size = size
    cdef SizeDistance best_size_distance
    cdef SizeDistance last_size_distance
    cdef int last_distances_len = 6
    cdef int last_distances[6]
    cdef int found_best = 0
    cdef SampledResize result

    while found_best == 0:
        sampling_count += 1
        best_size_distance = calculate_closest_size_distance(last_size, area, step_size, resize_type)
        
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

cdef Position[::1] create_position_array(int size):
    cdef Position[::1] result = cython.view.array(shape=(size,), itemsize=sizeof(Position), format='i i')
    return result

def py_create_position_array(int size) -> Position[::1]:
    return create_position_array(size)

cdef Size[::1] create_size_array(int size):
    cdef Size[::1] result = cython.view.array(shape=(size,), itemsize=sizeof(Size), format='i i')
    return result

def py_create_size_array(int size) -> Size[::1]:
    return create_size_array(size)

cdef BoxCoordinates[::1] create_box_array(int size):
    cdef BoxCoordinates[::1] result = cython.view.array(shape=(size,), itemsize=sizeof(BoxCoordinates), format='i i i i')
    return result

def py_create_box_array(int size) -> BoxCoordinates[::1]:
    return create_box_array(size)


cdef int quarter_box(
    BoxCoordinates box,
    BoxPartitionType target_partition_type,
    BoxCoordinates[::1] input_output_quarters,
    int index,
    BoxPartitionType partition_type
) noexcept nogil:
    cdef int new_index = index
    cdef BoxPartitionType next_partition_type
    cdef int partition_width = <int>round((box.right - box.left) / 2)
    cdef int partition_height = <int>round((box.lower - box.upper) / 2)
    cdef BoxCoordinates left_upper
    cdef BoxCoordinates right_upper
    cdef BoxCoordinates right_lower
    cdef BoxCoordinates left_lower
    
    left_upper.left = box.left
    left_upper.upper = box.upper
    left_upper.right = left_upper.left + partition_width
    left_upper.lower = left_upper.upper + partition_height

    right_upper.left = left_upper.right
    right_upper.upper = left_upper.upper
    right_upper.right = right_upper.left + partition_width
    right_upper.lower = right_upper.upper + partition_height

    right_lower.left = right_upper.left
    right_lower.upper = right_upper.lower
    right_lower.right = right_lower.left + partition_width
    right_lower.lower = right_lower.upper + partition_height

    left_lower.left = left_upper.left
    left_lower.upper = left_upper.lower
    left_lower.right = right_lower.left
    left_lower.lower = right_lower.lower

    if partition_type == target_partition_type:
        input_output_quarters[new_index] = left_upper
        input_output_quarters[new_index + 1] = right_upper
        input_output_quarters[new_index + 2] = right_lower
        input_output_quarters[new_index + 3] = left_lower
        return new_index + 4
    elif partition_type == BoxPartitionType.FOUR:
        next_partition_type = BoxPartitionType.SIXTEEN
    else:
        next_partition_type = BoxPartitionType.SIXTY_FOUR

    new_index = new_index + quarter_box(
        left_upper,
        target_partition_type,
        input_output_quarters,
        new_index, 
        next_partition_type
    )
    new_index = new_index + quarter_box(
        right_upper,
        target_partition_type,
        input_output_quarters,
        new_index, 
        next_partition_type
    )
    new_index = new_index + quarter_box(
        right_lower,
        target_partition_type,
        input_output_quarters,
        new_index, 
        next_partition_type
    )
    new_index = new_index + quarter_box(
        left_lower,
        target_partition_type,
        input_output_quarters,
        new_index, 
        next_partition_type
    )
    return new_index
        

cdef int partition_box_into_array(
    BoxCoordinates box,
    BoxPartitionType partition_type, 
    BoxCoordinates[::1] input_output_partitions,
) noexcept nogil:
    cdef BoxPartitionType target_partition_type = partition_type
    cdef int result = 0

    if 0 == input_output_partitions.shape[0]:
        return 0
    if input_output_partitions.shape[0] < BoxPartitionType.FOUR:
        input_output_partitions[0] = box
        return 1
    if input_output_partitions.shape[0] < BoxPartitionType.SIXTEEN:
        target_partition_type = BoxPartitionType.FOUR
    elif input_output_partitions.shape[0] < BoxPartitionType.SIXTY_FOUR:
        target_partition_type = BoxPartitionType.SIXTEEN if BoxPartitionType.SIXTEEN < partition_type else partition_type

    return quarter_box(box, target_partition_type, input_output_partitions, 0, BoxPartitionType.FOUR)


    
    

    
