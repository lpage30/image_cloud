# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
from imagecloud.native.position_box_size cimport (
     Position,
     ResizeType,
     Size,
     BoxCoordinates,
     Transpose,
     empty_box,
     is_empty_box,
     to_position,
     to_box, 
     to_resize_type,
     to_size,
     transpose_size,
     adjust_size,
     remove_margin,
     untranspose_size
)

cdef int is_unreserved_position(
    unsigned int[:,:] reservation_map, 
    BoxCoordinates box
) noexcept nogil:
    for x in range(box.left, box.right):
        for y in range(box.upper, box.lower):
            if reservation_map[x, y] != 0:
                return 0
    return 1

cdef BoxCoordinates find_unreserved_box(
    unsigned int[:,:] reservation_map,
    unsigned int[:] position_scratch_buffer,
    Size size,
    random_state
):
    cdef Size scan_size = to_size(
        reservation_map.shape[0] - size.width, 
        reservation_map.shape[1] - size.height
    )
    cdef position_index = 0
    cdef unreserved_position_index = 0
    
    cdef int x = 0
    cdef int y = 0
    for x in range(scan_size.width):
        for y in range(scan_size.height):
            if is_unreserved_position(reservation_map, to_box(to_position(x, y), size)):
                position_scratch_buffer[position_index] = x
                position_scratch_buffer[position_index + 1] = y
                position_index = position_index + 2
    
    if 0 == position_index:
        return empty_box()

    # positions is an array of ints extended with position left and upper
    # we want to randomly pick the index of a position left
    unreserved_position_index = random_state.randint(0, (position_index//2) - 1 ) * 2
    return to_box(
        to_position(
            position_scratch_buffer[unreserved_position_index],
            position_scratch_buffer[unreserved_position_index + 1]
        ),
        size
    )

cdef SampledUnreservedBoxResult sample_to_find_unreserved_box(
    unsigned int[:,:] reservation_map, 
    unsigned int[:] position_scratch_buffer,
    Size size,
    Size min_size,
    int margin,
    ResizeType resize_type,
    int step_size,
    random_state
):
    cdef int sampling_count = 0
    cdef int rotate = 0
    cdef Size new_size = size
    cdef int shrink_step_size = -1 * step_size
    cdef Transpose orientation = Transpose.NO_TRANSPOSE
    cdef BoxCoordinates unreserved_box
    cdef SampledUnreservedBoxResult result

    while True:
        sampling_count += 1
        if new_size.width < min_size.width or new_size.height < min_size.height:
            result.found = 0
            result.sampling_total = sampling_count 
            result.new_size = new_size
            return result

        if 0 != rotate:
            orientation = Transpose.ROTATE_90
            new_size = transpose_size(orientation, new_size)
                
        unreserved_box = find_unreserved_box(
            reservation_map,
            position_scratch_buffer,
            adjust_size(margin, new_size, ResizeType.NO_RESIZE_TYPE),
            random_state
        )
        if not(is_empty_box(unreserved_box)):
            result.found = 1
            result.sampling_total = sampling_count
            result.new_size = new_size
            result.unreserved_box = unreserved_box
            result.actual_box = remove_margin(margin, unreserved_box)
            result.orientation = orientation
            return result
        
        if 0 != rotate:
            new_size = untranspose_size(orientation, new_size)
            new_size = adjust_size(shrink_step_size, new_size, resize_type)
            orientation = Transpose.NO_TRANSPOSE
            rotate = 0
        else:
            rotate = 1


def py_is_unreserved_position(
    unsigned int[:,:] reservation_map,
    BoxCoordinates box
) -> bool:
    return True if 0 != is_unreserved_position(reservation_map, box) else False


def py_sample_to_find_unreserved_box(
    unsigned int[:,:] reservation_map,
    unsigned int[:] position_scratch_buffer,
    Size size,
    Size min_size,
    int margin,
    int resize_type,
    int step_size,
    random_state
) -> SampledUnreservedBoxResult:
    return sample_to_find_unreserved_box(
        reservation_map,
        position_scratch_buffer,
        size,
        min_size,
        margin,
        to_resize_type(resize_type),
        step_size,
        random_state
    )