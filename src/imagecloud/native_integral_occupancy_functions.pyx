# cython: boundscheck=False
# cython: wraparound=False
import array
import numpy as np

# copied from https://github.com/amueller/word_cloud/blob/main/wordcloud/query_integral_image.pyx
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
    r.lower = upper - height
    return r

def is_box_too_big(unsigned int[:,:] occupancy_map, BoxCoordinates box):
    return occupancy_map.shape[0] <= box.right or box.lower < 0

def is_free_position(unsigned int[:,:] occupancy_map, BoxCoordinates box):
    cdef total = 0
    for x in range(box.left, box.right):
        for y in range(box.lower, box.upper):
          total += occupancy_map[x, y]
          if 0 < total:
            return False
    return True


def find_free_position(unsigned int[:,:] occupancy_map, int[:] size, random_state):

    cdef int scan_width = occupancy_map.shape[0]
    cdef int scan_height = occupancy_map.shape[1]
    cdef BoxCoordinates box = to_box(0,1,2,3)
    cdef int position_count = 0
    cdef int chosen_position = 0
    cdef bint box_too_big = False

    # box positions are '(left,upper) so we need to go from (top-left) to (bottom-right) in occupancy map
    for left in range(scan_width):
        box_too_big = False
        for upper in range(scan_height, 0, -1):
            box = to_box(left, upper, size[0], size[1])
            box_too_big = is_box_too_big(occupancy_map, box)
            if box_too_big:
                break
            if is_free_position(occupancy_map, box):
                position_count += 1
        if box_too_big:
            break

    if 0 == position_count:
        return None

    chosen_position = random_state.randint(1, position_count)
    position_count = 0
    for left in range(scan_width):
        for upper in range(scan_height, 0, -1):
            box = to_box(left, upper, size[0], size[1])
            if is_free_position(occupancy_map, box):
                position_count += 1
                if chosen_position == position_count:
                    return left, upper

def reserve_position(unsigned int[:,:] occupancy_map, int[:] position, int[:] size, int reservation_no):
    cdef BoxCoordinates box = to_box(position[0], position[1], size[0], size[1])

    for x in range(box.left, box.right):
        for y in range(box.lower, box.upper):
            occupancy_map[x, y] = reservation_no
