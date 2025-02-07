import numpy as np
from enum import IntEnum
from imagecloud.position_box_size import (
    Point,
    ResizeType,
    Size,
    BoxCoordinates
)
from PIL import Image
import imagecloud.native.unreserved_box as native
import imagecloud.native.parallel.p_unreserved_box as native_parallel


ReservationMapDataType = np.uint32
ReservationMapType = np.ndarray[ReservationMapDataType, ReservationMapDataType]
class Direction(IntEnum):
    UP = 1
    LEFT = 2
    DOWN = 3
    RIGHT = 4

class SampledUnreservedBoxResult(object):
    
    def __init__(
        self, 
        found: bool,
        sampling_total: int,
        new_size: Size,
        unreserved_box: BoxCoordinates | None = None,
        actual_box: BoxCoordinates | None = None,
        orientation: Image.Transpose | None = None,
        parallelism: int | None = None
    ):
        self.found = found
        self.sampling_total = sampling_total
        self.new_size = new_size
        self.unreserved_box = unreserved_box
        self.actual_box = actual_box
        self.orientation = orientation
        self.parallelism = parallelism if parallelism is not None else 1
    
    @staticmethod
    def from_native(native_sampledunreservedboxresult):
        if 0 != native_sampledunreservedboxresult['found']:
            return  SampledUnreservedBoxResult(
                True,
                native_sampledunreservedboxresult['sampling_total'],
                Size.from_native(native_sampledunreservedboxresult['new_size']),
                BoxCoordinates.from_native(native_sampledunreservedboxresult['unreserved_box']),
                BoxCoordinates.from_native(native_sampledunreservedboxresult['actual_box']),
                Image.Transpose(native_sampledunreservedboxresult['orientation']) if 0 <= native_sampledunreservedboxresult['orientation'] else None
            )
        else:
            return  SampledUnreservedBoxResult(
                False,
                native_sampledunreservedboxresult['sampling_total'],
                Size.from_native(native_sampledunreservedboxresult['new_size']),
            )


# extrapolated from https://github.com/amueller/word_cloud/blob/main/wordcloud/wordcloud.py
class Reservations(object):
    def __init__(self,
                 map_size: Size = Size((0,0)),
                 parallelism: int = 1
        ):
        self._map_size = map_size
        # integral is our 'target' for placement of images
        self._reservation_map: ReservationMapType  = np.zeros(map_size.tuple, dtype=ReservationMapDataType)
        self._position_scratch_buffer: ReservationMapType = np.zeros(map_size.width * map_size.height, dtype=ReservationMapDataType),
        self._parallelism: int = parallelism
    
    @property
    def map_size(self) -> Size:
        return self._map_size
    
    @property
    def reservation_map(self) -> ReservationMapType:
        return self._reservation_map

    @reservation_map.setter
    def reservation_map(self, map: ReservationMapType) -> None:
        self._map_size = Size((map.shape[0], map.shape[1]))
        self._reservation_map = map

    def sample_to_find_unreserved_box(
        self, 
        size: Size,
        min_size: Size,
        margin: int,
        resize_type: ResizeType,
        step_size: int,
        random_state
    ) -> SampledUnreservedBoxResult:

        if 1 < self._parallelism:
            result = native_parallel.py_p_sample_to_find_unreserved_box(
                self._reservation_map,
                Size.to_native(size),
                Size.to_native(min_size),
                margin,
                resize_type.value,
                step_size,
                0
            )
        else:
            result = native.py_sample_to_find_unreserved_box(
                self._reservation_map,
                self._position_scratch_buffer,
                Size.to_native(size),
                Size.to_native(min_size),
                margin,
                resize_type.value,
                step_size,
                random_state,
            )
        return SampledUnreservedBoxResult.from_native(result)
    
    def reserve_box(self, box: BoxCoordinates, reservation_no: int) -> None:
        if reservation_no == 0:
            raise ValueError('reservation_number cannot be zero')
        for x in range(box.left, box.right):
            for y in range(box.upper, box.lower):
                self.reservation_map[x, y] = reservation_no
    
    def find_expanded_box_versions(self, box: BoxCoordinates) -> list[BoxCoordinates] | None:
        possible_boxset: set[BoxCoordinates] = set()
        max_directions = max(Direction)
        for i in range(max_directions):
            possibles: list[BoxCoordinates] = list()
            possibles.append(box)
            for j in range(max_directions):
                # do directions in every ordering
                direction = Direction(
                    ((i + j) % max_directions) + 1
                )
                possibles.extend(self._find_expanded_boxes(direction, possibles))
            possible_boxset.update(possibles)

        possible_boxset.remove(box)
        possible_boxes = list(possible_boxset)
        
        return possible_boxes if 0 < len(possible_boxes) else None
        
        
    @staticmethod
    def create_reservation_map(map_size: Size, reservations: list[BoxCoordinates]) -> ReservationMapType:
        integral = Reservations(map_size)
        for i in range(len(reservations)):
            integral.reserve_box(reservations[i], i + 1)
        return integral.reservation_map

    def _find_expanded_boxes(self, direction: Direction, boxes: list[BoxCoordinates]) -> list[BoxCoordinates]:
        result: list[BoxCoordinates] = list()
        match direction:
            case Direction.UP:
                find_expanded_box = self._find_upper_expanded_box
            case Direction.LEFT:
                find_expanded_box = self._find_left_expanded_box
            case Direction.DOWN:
                find_expanded_box = self._find_lower_expanded_box
            case Direction.RIGHT:
                find_expanded_box = self._find_right_expanded_box
           
        for box in boxes:
            new_box = find_expanded_box(box)
            if new_box is not None:
                result.append(new_box)
        return result

    def _find_upper_expanded_box(self, box: BoxCoordinates) -> BoxCoordinates | None:
        box_edge: Point = Point((box.lower_right.x, box.upper_left.y))
        result: BoxCoordinates | None = None
        for y in range(box.upper - 1, -1, -1): # expand up
            new_edge = Point((box.upper_left.x, y))
            if self._is_unreserved_position(BoxCoordinates.from_points(new_edge, box_edge)):
                result = BoxCoordinates.from_points(new_edge, box.lower_right)
            else:
                return result
        
        return result

    def _find_left_expanded_box(self, box: BoxCoordinates) -> BoxCoordinates | None:
        box_edge: Point = Point((box.upper_left.x, box.lower_right.y))
        result: BoxCoordinates | None = None
        for x in range(box.left - 1, -1, -1): # expand left
            new_edge = Point((x, box.upper_left.y))
            if self._is_unreserved_position(BoxCoordinates.from_points(new_edge,box_edge)):
                result = BoxCoordinates.from_points(new_edge, box.lower_right)
            else:
                return result
        
        return result

    def _find_lower_expanded_box(self, box: BoxCoordinates) -> BoxCoordinates | None:
        box_edge: Point = Point((box.upper_left.x, box.lower_right.y))
        result: BoxCoordinates | None = None
        for y in range(box.lower + 1, self.map_size.height): # expand down
            new_edge = Point((box.lower_right.x, y))
            if self._is_unreserved_position(BoxCoordinates.from_points(box_edge, new_edge)):
                result = BoxCoordinates.from_points(box.upper_left, new_edge)
            else:
                return result
        
        return result


    def _find_right_expanded_box(self, box: BoxCoordinates) -> BoxCoordinates | None:
        box_edge: Point = Point((box.lower_right.x, box.upper_left.y))
        result: BoxCoordinates | None = None
        for x in range(box.right + 1, self.map_size.width): # expand right
            new_edge = Point((x, box.lower_right.y))
            if self._is_unreserved_position(BoxCoordinates.from_points(box_edge, new_edge)):
                result = BoxCoordinates.from_points(box.upper_left, new_edge)
            else:
                return result
        
        return result

    def _is_unreserved_position(self, box: BoxCoordinates) -> bool:
        if 1 < self._parallelism:
            result = native_parallel.py_p_is_unreserved_position(
                self.reservation_map,
                BoxCoordinates.to_native(box),
                0
            )
        else:
            result = native.py_is_unreserved_position(
                self.reservation_map,
                BoxCoordinates.to_native(box)
            )
        return result

