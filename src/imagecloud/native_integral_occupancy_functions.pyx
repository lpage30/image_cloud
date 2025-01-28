# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
from cpython cimport array 

cdef struct BoxCoordinates:
    int left
    int upper
    int right
    int lower

def to_box(int left, int upper, int width, int height):
    cdef BoxCoordinates r
    r.left = left
    r.upper = upper
    r.right = left + width
    r.lower = upper + height
    return r

def is_size_too_wide(unsigned int[:,:] occupancy_map, int position_x, int width):
    return occupancy_map.shape[0] <= (position_x + width)

def is_size_too_tall(unsigned int[:,:] occupancy_map, int position_y, int height):
    return occupancy_map.shape[1] <= (position_y + height)

def is_free_position(unsigned int[:,:] occupancy_map, BoxCoordinates box):
    cdef total = 0
    for x in range(box.left, box.right):
        for y in range(box.upper, box.lower):
          if occupancy_map[x, y] != 0:
            return False
    return True


def find_free_position(unsigned int[:,:] occupancy_map, int size_width, int size_height, random_state):

    cdef int scan_width = occupancy_map.shape[0]
    cdef int scan_height = occupancy_map.shape[1]
    cdef BoxCoordinates box = to_box(0,1,2,3)
    cdef array.array positions = array.array('i', [])
    cdef int chosen_position = 0
    
    # box positions are '(left,upper) so we need to go from (top-left) to (bottom-right) in occupancy map
    for left in range(scan_width):
        if is_size_too_wide(occupancy_map, left, size_width):
            break
        for upper in range(scan_height):
            if is_size_too_tall(occupancy_map, upper, size_height):
                break
            if is_free_position(occupancy_map, to_box(left, upper, size_width, size_height)):
                positions.extend([left, upper])

    if 0 == len(positions):
        return None

    chosen_position = random_state.randint(0, int(len(positions)/2) - 1 ) * 2
    return positions[chosen_position], positions[chosen_position + 1]

def reserve_position(unsigned int[:,:] occupancy_map, int position_x, int position_y, int size_width, int size_height, int reservation_no):
    cdef BoxCoordinates box = to_box(position_x, position_y, size_width, size_height)

    for x in range(box.left, box.right):
        for y in range(box.upper, box.lower):
            occupancy_map[x, y] = reservation_no
