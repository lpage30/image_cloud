# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
from cpython cimport array 

cdef struct BoxCoordinates:
    int left
    int upper
    int right
    int lower

cdef struct Size:
    int width
    int height

cdef struct Position:
    int left
    int upper


def is_size_too_wide(unsigned int[:,:] occupancy_map, int position_x, int width):
    return occupancy_map.shape[0] <= (position_x + width)

def is_size_too_tall(unsigned int[:,:] occupancy_map, int position_y, int height):
    return occupancy_map.shape[1] <= (position_y + height)



def to_box(Position position, Size size):
    cdef BoxCoordinates r
    r.left = position.left
    r.upper = position.upper
    r.right = position.left + size.width
    r.lower = position.upper + size.height
    return r

def to_position(int left, int upper):
    cdef Position r
    r.left = left
    r.upper = upper
    return r

def to_size(int width, int height):
    cdef Size r
    r.width = width
    r.height = height
    return r

def is_free_position(unsigned int[:,:] occupancy_map, BoxCoordinates box):
    for x in range(box.left, box.right):
        for y in range(box.upper, box.lower):
          if occupancy_map[x, y] != 0:
            return False
    return True

def find_free_box(unsigned int[:,:] occupancy_map, Size size, random_state):
    cdef Size scan_size = to_size(occupancy_map.shape[0], occupancy_map.shape[1])
    cdef Position pos = to_position(0,0)
    cdef BoxCoordinates box = to_box(pos,size)
    cdef array.array positions = array.array('i', [])
    cdef chosen_position_left_index = 0
    
    # box positions are '(left,upper) so we need to go from (top-left) to (bottom-right) in occupancy map
    for left in range(scan_size.width):
        if is_size_too_wide(occupancy_map, left, size.width):
            break
        for upper in range(scan_size.height):
            if is_size_too_tall(occupancy_map, upper, size.height):
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
    