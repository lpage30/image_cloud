# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# distutils: language = c++
# distutils: extra_compile_args = -std=c++11
cimport cython
from libcpp.atomic cimport atomic
from libc.math cimport fmod
from cython.parallel import parallel, prange
from imagecloud.native.functions cimport (
    ln_rand_int,
    to_one_dimension_array_len,
    to_two_dimension_array_position
)
from imagecloud.native.position_box_size cimport (
    adjust_size,
    BoxCoordinates,
    BoxPartitionType,
    create_position_array,
    create_box_array,
    empty_box,
    is_empty_box,
    partition_box_into_array,
    Position,
    remove_margin,
    ResizeType,
    Size,
    to_box,
    to_position,
    to_resize_type,
    to_size,
    Transpose,
    transpose_size,
    untranspose_size
)
    
cdef BoxPartitionType parallelism_to_partition_type(int parallelism) noexcept nogil:
    if parallelism <= BoxPartitionType.FOUR:
        return BoxPartitionType.FOUR   
    elif parallelism <= BoxPartitionType.SIXTEEN:
        return BoxPartitionType.SIXTEEN
    else:
        return BoxPartitionType.SIXTY_FOUR
        


cdef int is_unreserved_position(
    unsigned int[:,:] occupancy_map, 
    BoxCoordinates box
) noexcept nogil:

    for x in range(box.left, box.right):
        for y in range(box.upper, box.lower):
            if occupancy_map[x, y] != 0:
                return 0
    return 1


cdef int p_is_unreserved_position(
    unsigned int[:,:] occupancy_map, 
    BoxCoordinates box,
    int parallelism,
    BoxCoordinates[::1] box_scratch_buffer
) noexcept nogil:

    cdef BoxCoordinates[::1] partitions = box_scratch_buffer
    cdef int result = 1
    cdef int i = 0
    cdef int partition_count = partition_box_into_array(
        box,
        parallelism_to_partition_type(parallelism),
        partitions
    )
    
    with nogil, parallel(num_threads=parallelism):
        for i in prange(partition_count):
            result = is_unreserved_position(occupancy_map, partitions[i])
            if 0 == result:
                break
    return result



cdef BoxCoordinates p_find_unreserved_box(
    unsigned int[:,:] occupancy_map,
    Size size,
    int parallelism,
    Position[::1] position_scratch_buffer,
    BoxCoordinates[::1] box_scratch_buffer
) noexcept nogil:

    cdef Size scan_size = to_size(
        occupancy_map.shape[0] - size.width, 
        occupancy_map.shape[1] - size.height
    )
    cdef int total_points = to_one_dimension_array_len(scan_size)
    cdef Position pos = to_position(0,0)
    cdef atomic[int] apos_index
    cdef int pos_index = -1
    cdef int p = 0
    apos_index.store(pos_index)
    with nogil, parallel(num_threads=parallelism):
        for p in prange(total_points):
            pos = to_two_dimension_array_position(p, scan_size.width)
            if 1 == p_is_unreserved_position(occupancy_map, to_box(pos, size), parallelism, box_scratch_buffer):
                pos_index = apos_index.fetch_add(1)
                position_scratch_buffer[pos_index] = pos

    if -1 == pos_index:
        return empty_box()
    
    return to_box(
        position_scratch_buffer[ln_rand_int(0, pos_index)],
        size
    )


cdef PSampledUnreservedBoxResult p_sample_to_find_unreserved_box(
    unsigned int[:,:] occupancy_map,
    Size size,
    Size min_size,
    int margin,
    ResizeType resize_type,
    int step_size,
    int parallelism,
    Position[::1] position_scratch_buffer,
    BoxCoordinates[::1] box_scratch_buffer
) noexcept nogil:

    cdef int maximum_samplings = 1000000
    cdef int i = 0
    cdef int rotate = 0
    cdef Size new_size = size
    cdef int shrink_step_size = -1 * step_size
    cdef Transpose orientation = Transpose.NO_TRANSPOSE
    cdef BoxCoordinates unreserved_box
    cdef PSampledUnreservedBoxResult result
    result.found = 0
    result.sampling_total = 0 
    result.new_size = new_size

    with nogil, parallel(num_threads=parallelism):
        for i in prange(maximum_samplings):
            rotate = <int>fmod(i, 2)
            if new_size.width < min_size.width or new_size.height < min_size.height:
                result.found = 0
                result.sampling_total = i + 1 
                result.new_size = new_size
                break

            if 0 != rotate:
                orientation = Transpose.ROTATE_90
                new_size = transpose_size(orientation, new_size)
                
            unreserved_box = p_find_unreserved_box(
                occupancy_map,
                adjust_size(margin, new_size, ResizeType.NO_RESIZE_TYPE),
                parallelism,
                position_scratch_buffer,
                box_scratch_buffer
            )
            if not(is_empty_box(unreserved_box)):
                result.found = 1
                result.sampling_total = i + 1
                result.new_size = new_size
                result.unreserved_box = unreserved_box
                result.actual_box = remove_margin(margin, unreserved_box)
                result.orientation = orientation
                break
        
            if 0 != rotate:
                new_size = untranspose_size(orientation, new_size)
                new_size = adjust_size(shrink_step_size, new_size, resize_type)
                orientation = Transpose.NO_TRANSPOSE

    return result


def py_p_is_unreserved_position(
    unsigned int[:,:] occupancy_map, 
    BoxCoordinates box,
    int parallelism,
    
) -> bool:
    cdef BoxCoordinates[::1] box_scratch_buffer = create_box_array(parallelism_to_partition_type(parallelism))
    return True if 0 != p_is_unreserved_position(occupancy_map, box, parallelism, box_scratch_buffer) else False

def py_p_find_unreserved_box(
    unsigned int[:,:] occupancy_map,
    Size size,
    int parallelism,
) -> BoxCoordinates | None:
    cdef Position[::1] position_scratch_buffer = create_position_array(occupancy_map.shape[0] * occupancy_map.shape[1])
    cdef BoxCoordinates[::1] box_scratch_buffer = create_box_array(parallelism_to_partition_type(parallelism))
    
    cdef BoxCoordinates result = p_find_unreserved_box(
        occupancy_map, 
        size,
        parallelism,
        position_scratch_buffer,
        box_scratch_buffer
    )
    return None if is_empty_box(result) else result

def py_p_sample_to_find_unreserved_box(
    unsigned int[:,:] occupancy_map,
    Size size,
    Size min_size,
    int margin,
    int resize_type,
    int step_size,
    int parallelism
) -> PSampledUnreservedBoxResult:

    cdef Position[::1] position_scratch_buffer = create_position_array(occupancy_map.shape[0] * occupancy_map.shape[1])
    cdef BoxCoordinates[::1] box_scratch_buffer = create_box_array(parallelism_to_partition_type(parallelism))

    return p_sample_to_find_unreserved_box(
        occupancy_map,
        size,
        min_size,
        margin,
        to_resize_type(resize_type),
        step_size,
        parallelism,
        position_scratch_buffer,
        box_scratch_buffer
    )