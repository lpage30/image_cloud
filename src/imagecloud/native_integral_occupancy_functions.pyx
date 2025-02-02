# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
from cpython cimport array
from imagecloud.native_position_box_size cimport (
     Position,
     Size,
     BoxCoordinates,
     Transpose,
     to_position,
     to_box, 
     to_size,
     transpose_size,
     adjust_size,
     remove_margin,
     untranspose_size
)


cdef is_free_position(unsigned int[:,:] occupancy_map, BoxCoordinates box):
    for x in range(box.left, box.right):
        for y in range(box.upper, box.lower):
          if occupancy_map[x, y] != 0:
            return False
    return True

def py_is_free_position(unsigned int[:,:] occupancy_map, BoxCoordinates box):
    return is_free_position(occupancy_map, box)

cdef find_free_box(unsigned int[:,:] occupancy_map, Size size, random_state):
    cdef Size scan_size = to_size(occupancy_map.shape[0], occupancy_map.shape[1])
    cdef Position pos = to_position(0,0)
    cdef BoxCoordinates box = to_box(pos,size)
    cdef array.array positions = array.array('i', [])
    cdef chosen_position_left_index = 0
    
    # box positions are '(left,upper) so we need to go from (top-left) to (bottom-right) in occupancy map
    for left in range(scan_size.width):
        if scan_size.width <= (left + size.width):
            break
        for upper in range(scan_size.height):
            if scan_size.height <= (upper + size.height):
                break
            pos = to_position(left, upper)
            box = to_box(pos,size)
            if is_free_position(occupancy_map, box):
                positions.extend([pos.left, pos.upper])

    if 0 == len(positions):
        return None

    # positions is an array of ints extended with position left and upper
    # we want to randomly pick the index of a position left
    chosen_position_left_index = random_state.randint(0, int(len(positions)/2) - 1 ) * 2
    return to_box(
        to_position(
            positions[chosen_position_left_index],
            positions[chosen_position_left_index + 1]
        ),
        size
    )

def py_find_free_box(unsigned int[:,:] occupancy_map, Size size, random_state):
    return find_free_box(occupancy_map, size, random_state)

cdef sample_to_find_free_box(
    unsigned int[:,:] occupancy_map, 
    Size size,
    Size min_size,
    int margin,
    int maintain_aspect_ratio, # false(0)/true(non-zero),
    int step_size,
    random_state
):
    cdef int sampling_count = 0
    cdef int rotate = 0
    cdef Size new_size = size
    cdef int shrink_step_size = -1 * step_size
    cdef Transpose orientation = Transpose.NONE
    cdef BoxCoordinates reservation_box
    cdef SamplingResult result

    while True:
        sampling_count += 1
        if new_size.width < min_size.width or new_size.height < min_size.height:
            result.found_reservation = 0
            result.sampling_total = sampling_count 
            result.new_size = new_size
            return result

        if 0 != rotate:
            orientation = Transpose.ROTATE_90
            new_size = transpose_size(orientation, new_size)
        
        reservation = find_free_box(occupancy_map, adjust_size(margin, new_size, maintain_aspect_ratio), random_state)
        if reservation is not None:
            result.found_reservation = 1
            result.sampling_total = sampling_count
            result.new_size = new_size
            result.reservation_box = reservation
            result.actual_box = remove_margin(margin, reservation)
            result.new_size = new_size
            result.orientation = orientation
            return result
        
        if 0 != rotate:
            new_size = untranspose_size(orientation, new_size)
            new_size = adjust_size(shrink_step_size, new_size, maintain_aspect_ratio)
            orientation = Transpose.NONE
            rotate = 0
        else:
            rotate = 1

def py_sample_to_find_free_box(
    unsigned int[:,:] occupancy_map, 
    Size size,
    Size min_size,
    int margin,
    int maintain_aspect_ratio, # false(0)/true(non-zero),
    int step_size,
    random_state
):
    return sample_to_find_free_box(
        occupancy_map, 
        size,
        min_size,
        margin,
        maintain_aspect_ratio,
        step_size,
        random_state
    )