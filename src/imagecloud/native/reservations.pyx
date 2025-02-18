# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# distutils: language = c++
# distutils: extra_compile_args = -std=c++11
cimport cython
from libcpp.atomic cimport atomic
from cython.parallel import parallel, prange
from libc.time cimport time
cdef extern from "stdio.h":
    int snprintf(char *str, unsigned int size, const char *format, ...) noexcept nogil
from imagecloud.native.size cimport (
    Size, 
    ResizeType,
    Transpose,
    to_resize_type,
    create_size,
    size_area,
    transpose,
    adjust,
    untranspose,
    size_to_string,
    weighted_size_to_string,
    size_less_than
)
from imagecloud.native.box cimport (
    Box, 
    empty_box,
    create_box,
    is_empty,
    remove_margin,
    box_to_string,
    box_area,
    contains,
    box_equals
)
from imagecloud.native.base_logger cimport (
    LoggerLevel,
    log_debug,
    log_error,
    log_py
)
#NOTE: PIL Image shape is of form (width, height) https://pillow.readthedocs.io/en/stable/reference/Image.html

# NOTE: ND Array shape is of form: (height, width) https://numpy.org/doc/2.2/reference/generated/numpy.ndarray.shape.html
# so for ND Array (memory view) we process rows (height or y axis) followed by columns (width or x axis)
# which is opposite of Image.
# memoryview[y,x] for ND Array and Image[x,y] <eye roll>
# a 'flattened out' memory view length is the area (height*width)
# 1 index value in that flattened out view addresses row = <int>(index_value/width), col = index_value - (width * row)

cdef enum Direction:
    LEFT = 1
    UP = 2
    RIGHT = 3
    DOWN = 4
        
cdef Direction g_directions[4]
g_directions[0] = Direction.LEFT
g_directions[1] = Direction.UP
g_directions[2] = Direction.RIGHT
g_directions[3] = Direction.DOWN

cdef Reservations create_reservations(
    int num_threads,
    Size map_size,
    Box map_box,
    int buffer_length,
) noexcept nogil:
    cdef Reservations self
    self.num_threads = num_threads
    self.map_size = map_size
    self.map_box = map_box
    self.buffer_length = buffer_length
    return self

cdef const char* reservations_to_string(
    Reservations self
) noexcept nogil:
    cdef char buf[128]
    snprintf(buf, 128,
        "Reservations[Size(%d,%d), num_threads=%d]",
        self.map_size.width, self.map_size.height, self.num_threads
    )
    return buf

cdef int _is_unreserved(
    Reservations self,
    unsigned int[:,:] self_reservation_map,
    Box party_size
) noexcept nogil:
    for row in range(party_size.upper, party_size.lower):
        for col in range(party_size.left, party_size.right):
            if 0 != self_reservation_map[row, col]:
                return 0
    return 1

cdef Box _find_unreserved_opening(
    Reservations self, 
    unsigned int[:,:] self_reservation_map,
    unsigned int[:] self_position_buffer,
    Size size,
    random_object
) noexcept nogil:
    cdef Box possible_opening
    cdef int row
    cdef int col
    cdef int pos_count = 0
    cdef int rand_pos = 0
    for row in range(self.map_size.height):
        for col in range(self.map_size.width):
            possible_opening = create_box(col, row, col + size.width, row + size.height)
            if 0 == contains(self.map_box, possible_opening):
                break
            if 0 != _is_unreserved(
                self,
                self_reservation_map,
                possible_opening
            ):
                self_position_buffer[pos_count] = col # x position
                self_position_buffer[pos_count + 1] = row # y position
                pos_count += 2

    if 0 == pos_count:
        return empty_box()

    with gil:
        rand_pos = random_object.randint(0, <int>((pos_count/2) - 1)) * 2

    possible_opening.left = self_position_buffer[rand_pos]
    possible_opening.upper = self_position_buffer[rand_pos + 1]

    possible_opening.right = possible_opening.left + size.width
    possible_opening.lower = possible_opening.upper + size.height
    log_debug('found opening position[%d/%d] [x(%d) y(%d)] Size(%d,%d) right(%d), lower(%d) isunreserved?(%d)', 
        rand_pos, pos_count, possible_opening.left, possible_opening.upper, size.width, size.height, possible_opening.right, possible_opening.lower,
        _is_unreserved(self, self_reservation_map, possible_opening)
    )
    return possible_opening

cdef Box _p_find_unreserved_opening(
    Reservations self, 
    unsigned int[:,:] self_reservation_map,
    unsigned int[:] self_position_buffer,
    Size size,
    random_object
) noexcept nogil:
    global MARK
    global EMPY
    cdef atomic[int] pos_count
    cdef Size sub_map_size = create_size(self.map_size.width - size.width, self.map_size.height - size.height)
    cdef int total_positions = size_area(sub_map_size)
    cdef int p
    cdef Box possible_opening
    cdef int row
    cdef int col
    cdef int rand_pos
    pos_count.store(0)
    with nogil, parallel(num_threads=self.num_threads):
        for p in prange(total_positions):
            row = <int>(p / self.map_size.width)
            col = <int>(p - (row * self.map_size.width))
            possible_opening = create_box(col, row, col + size.width, row + size.height)
            if self.map_box.lower < possible_opening.lower:
                break
            if self.map_box.right < possible_opening.right:
                continue
            if 0 != _is_unreserved(
                self,
                self_reservation_map,
                possible_opening
            ):
                self_position_buffer[pos_count.fetch_add(1)] = p

    if 0 == pos_count.load():
        return empty_box()

    with gil:
        rand_pos = random_object.randint(0, pos_count.load() - 1)
    p = self_position_buffer[rand_pos]
    row = <int>(p / self.map_size.width)
    col = <int>(p - (row * self.map_size.width))

    possible_opening.left = col
    possible_opening.upper = row
    possible_opening.right = possible_opening.left + size.width
    possible_opening.lower = possible_opening.upper + size.height
    log_debug('found opening position[%d/%d](%d) [x(%d) y(%d)] Size(%d,%d) right(%d), lower(%d) isunreserved?(%d)', 
        rand_pos, pos_count.load(), p, possible_opening.left, possible_opening.upper, size.width, size.height, possible_opening.right, possible_opening.lower,
        _is_unreserved(self, self_reservation_map, possible_opening)
    )
    return possible_opening

cdef SampledUnreservedOpening sample_to_find_unreserved_opening(
    Reservations self,
    unsigned int[:,:] self_reservation_map,
    unsigned int[:] self_position_buffer,
    Size max_party_size,
    Size min_party_size,
    int margin,
    ResizeType resize_type,
    int step_size,
    random_object
)  noexcept nogil:

    cdef Size new_size = max_party_size
    cdef int shrink_step_size = -1 * step_size
    cdef Transpose orientation = Transpose.NO_TRANSPOSE
    cdef SampledUnreservedOpening result
    cdef Box unreserved_opening
    cdef int sampling_count = 0
    cdef int rotate = 1

    while True:
        sampling_count = sampling_count + 1
        if 1 < self.num_threads:
            unreserved_opening = _p_find_unreserved_opening(
                self,
                self_reservation_map,
                self_position_buffer,
                adjust(new_size, margin, ResizeType.NO_RESIZE_TYPE),
                random_object
            )
        else:
            unreserved_opening = _find_unreserved_opening(
                self,
                self_reservation_map,
                self_position_buffer,
                adjust(new_size, margin, ResizeType.NO_RESIZE_TYPE),
                random_object
            )

        if 0 == is_empty(unreserved_opening):
            result.found = 1
            result.sampling_total = sampling_count
            result.new_size = new_size
            result.opening_box = unreserved_opening
            result.actual_box = remove_margin(unreserved_opening, margin)
            result.orientation = orientation
            log_debug("FOUND: sample_to_find_unreserved_opening sampling[%d] size(%d, %d) orientation(%d) opening(%d,%d,%d,%d) actual(%d,%d,%d,%d)\n", 
                result.sampling_total, result.new_size.width, result.new_size.height, result.orientation,
                result.opening_box.left, result.opening_box.upper, result.opening_box.right, result.opening_box.lower,
                result.actual_box.left, result.actual_box.upper, result.actual_box.right, result.actual_box.lower
            )
            return result
        # alternate states: 0 test -> 1 rotate -> 2 test -> 3 shrink size -> back to state 0 until we find 1 or shrink too-small
        if 1 == rotate:
            orientation = Transpose.ROTATE_90
            new_size = transpose(new_size, orientation)
            rotate = 0
        else:
            new_size = untranspose(new_size, orientation)
            new_size = adjust(new_size, shrink_step_size, resize_type)
            orientation = Transpose.NO_TRANSPOSE
            if 0 != size_less_than(new_size, min_party_size):
                result.found = 0
                result.sampling_total = sampling_count
                result.new_size = new_size
                log_debug("NOT FOUND - TOO SMALL: sample_to_find_unreserved_opening sampling[%d] Size(%d, %d)\n", 
                    result.sampling_total, result.new_size.width, result.new_size.height
                )
                return result
            rotate = 1
    return result

cdef Box _find_expanded_box(
    Reservations self,
    unsigned int[:,:] self_reservation_map,
    Box box,
    int direction: int
) noexcept nogil:
    cdef Box edge = create_box(box.left, box.upper, box.right, box.lower)
    cdef Box result = create_box(box.left, box.upper, box.right, box.lower)

    if 0 == direction: # left
        edge = create_box(box.left, box.upper, box.left, box.lower)
        for col in range(edge.left - 1, -1, -1):
            edge.left = col
            if 0 == contains(self.map_box, edge):
                break
            elif 0 != _is_unreserved(self, self_reservation_map, edge):
                result.left = edge.left
                break
    elif 1 == direction: # UP
        edge = create_box(box.left, box.upper, box.right, box.upper)
        for row in range(edge.upper - 1, -1, -1):
            edge.upper = row
            if 0 == contains(self.map_box, edge):
                break
            elif 0 != _is_unreserved(self, self_reservation_map, edge):
                result.upper = edge.upper
                break
    elif 2 == direction: # right
        edge = create_box(box.right, box.upper, box.right, box.lower)
        for col in range(edge.right + 1, self.map_size.width):
            edge.right = col
            if 0 == contains(self.map_box, edge):
                break
            elif 0 != _is_unreserved(self, self_reservation_map, edge):
                result.right = edge.right
                break
    else: # Down
        edge = create_box(box.left, box.lower, box.right, box.lower)
        for row in range(edge.lower + 1, self.map_size.height):
            edge.lower = row
            if 0 == contains(self.map_box, edge):
                break
            elif 0 != _is_unreserved(self, self_reservation_map, edge):
                result.lower = edge.lower
                break
    return result

cdef Box maximize_existing_reservation(
    Reservations self, 
    unsigned int[:,:] self_reservation_map,
    Box existing_reservation
):
    cdef Box result = create_box(existing_reservation.left, existing_reservation.upper, existing_reservation.right, existing_reservation.lower)
    cdef int expansion_count = 0
    cdef int sampling = 0
    cdef int i = 0
    cdef Box expanded_box = Box(existing_reservation.left, existing_reservation.upper, existing_reservation.right, existing_reservation.lower)
    while True:
        sampling = sampling + 1
        expansion_count = 0
        for i in range(4):
            expanded_box = _find_expanded_box(self, self_reservation_map, expanded_box, i)
            if 0 == box_equals(expanded_box, result):
                result = expanded_box
                expansion_count = expansion_count + 1
        if 0 == expansion_count:
            break
    return result


def native_create_reservations(
    int num_threads,
    native_map_size,
    native_map_box,
    int buffer_length,
    unsigned int[:,:] reservation_map,
    unsigned int[:] position_buffer
):
    cdef Reservations native_reservations = create_reservations(
        num_threads,
        native_map_size,
        native_map_box,
        buffer_length,
    )
    return native_reservations

def native_sample_to_find_unreserved_opening(
    native_reservations,
    unsigned int[:,:] reservation_map,
    unsigned int[:] position_buffer,
    native_max_party_size,
    native_min_party_size,
    margin: int,
    resize_type: int,
    step_size: int,
    random_object
): # return native_sampledunreservedopening
    return sample_to_find_unreserved_opening(
        native_reservations,
        reservation_map,
        position_buffer,
        native_max_party_size,
        native_min_party_size,
        margin,
        to_resize_type(resize_type),
        step_size,
        random_object
    )

def native_maximize_existing_reservation(
    native_reservations,
    unsigned int[:,:] reservation_map,
    native_existing_reservation
): # return native_box
    return maximize_existing_reservation(native_reservations, reservation_map, native_existing_reservation)


def native_count_lost_reserved_slots(
    native_reservations,
    unsigned int[:,:] reservation_map,
    int reservation_no,
    native_reservation_box,
): # return int
    cdef Reservations reservations = native_reservations
    cdef Box reservation = native_reservation_box
    cdef lost = 0
    cdef int row = 0
    cdef int col = 0
    
    for row in range(reservation.upper, reservation.lower):
        for col in range(reservation.left, reservation.right):
            if reservation_map[row, col] != reservation_no:
                lost += 1
    return lost

