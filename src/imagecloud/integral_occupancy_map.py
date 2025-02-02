import numpy as np
from enum import IntEnum
from imagecloud.position_box_size import (
    Point,
    Size,
    BoxCoordinates
)
from PIL import Image
import imagecloud.native_integral_occupancy_functions as native


OccupancyMapDataType = np.uint32
OccupancyMapType = np.ndarray[OccupancyMapDataType, OccupancyMapDataType]
class Direction(IntEnum):
    UP = 1
    LEFT = 2
    DOWN = 3
    RIGHT = 4

class SamplingResult(object):
    
    def __init__(
        self, 
        found_reservation: bool,
        sampling_total: int,
        new_size: Size,
        reservation_box: BoxCoordinates | None = None,
        actual_box: BoxCoordinates | None = None,
        orientation: Image.Transpose | None = None
    ):
        self.found_reservation = found_reservation
        self.sampling_total = sampling_total
        self.new_size = new_size
        self.reservation_box = reservation_box
        self.actual_box = actual_box
        self.orientation = orientation
    
    @staticmethod
    def from_native(native_samplingresult):
        if 0 != native_samplingresult['found_reservation']:
            return  SamplingResult(
                True,
                native_samplingresult['sampling_total'],
                Size.from_native(native_samplingresult['new_size']),
                BoxCoordinates.from_native(native_samplingresult['reservation_box']),
                BoxCoordinates.from_native(native_samplingresult['actual_box']),
                Image.Transpose(native_samplingresult['orientation']) if 0 <= native_samplingresult['orientation'] else None
            )
        else:
            return  SamplingResult(
                True,
                native_samplingresult['sampling_total'],
                Size.from_native(native_samplingresult['new_size']),
            )


# extrapolated from https://github.com/amueller/word_cloud/blob/main/wordcloud/wordcloud.py
class IntegralOccupancyMap(object):
    def __init__(self, map_size: Size = Size((0,0))):
        self._map_size = map_size
        # integral is our 'target' for placement of images
        self._occupancy_map: OccupancyMapType  = np.zeros(map_size.tuple, dtype=OccupancyMapDataType)
    
    @property
    def map_size(self) -> Size:
        return self._map_size
    
    @property
    def occupancy_map(self) -> OccupancyMapType:
        return self._occupancy_map

    @occupancy_map.setter
    def occupancy_map(self, map: OccupancyMapType) -> None:
        self._map_size = Size((map.shape[0], map.shape[1]))
        self._occupancy_map = map

    def find_free_box(self, size: Size, random_state) -> BoxCoordinates | None:
        result = native.py_find_free_box(self._occupancy_map, Size.to_native(size), random_state)
        return BoxCoordinates.from_native(result) if result is not None else result

    def sample_to_find_free_box(
        self, 
        size: Size,
        min_size: Size,
        margin: int,
        maintain_aspect_ratio: bool,
        step_size: int,
        prefer_horizontal: float,
        random_state
    ) -> SamplingResult:
     
        return SamplingResult.from_native(
            native.py_sample_to_find_free_box(
                self._occupancy_map,
                Size.to_native(size),
                Size.to_native(min_size),
                margin,
                1 if maintain_aspect_ratio else 0,
                step_size,
                prefer_horizontal,
                random_state,
            )
        )
    
    def reserve_box(self, box: BoxCoordinates, reservation_no: int) -> None:
        if reservation_no == 0:
            raise ValueError('reservation_number cannot be zero')
        for x in range(box.left, box.right):
            for y in range(box.upper, box.lower):
                self.occupancy_map[x, y] = reservation_no
    
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
    def create_occupancy_map(map_size: Size, reservations: list[BoxCoordinates]) -> OccupancyMapType:
        integral = IntegralOccupancyMap(map_size)
        for i in range(len(reservations)):
            integral.reserve_box(reservations[i], i + 1)
        return integral.occupancy_map

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
            if self._is_free_position(BoxCoordinates.from_points(new_edge, box_edge)):
                result = BoxCoordinates.from_points(new_edge, box.lower_right)
            else:
                return result
        
        return result

    def _find_left_expanded_box(self, box: BoxCoordinates) -> BoxCoordinates | None:
        box_edge: Point = Point((box.upper_left.x, box.lower_right.y))
        result: BoxCoordinates | None = None
        for x in range(box.left - 1, -1, -1): # expand left
            new_edge = Point((x, box.upper_left.y))
            if self._is_free_position(BoxCoordinates.from_points(new_edge,box_edge)):
                result = BoxCoordinates.from_points(new_edge, box.lower_right)
            else:
                return result
        
        return result

    def _find_lower_expanded_box(self, box: BoxCoordinates) -> BoxCoordinates | None:
        box_edge: Point = Point((box.upper_left.x, box.lower_right.y))
        result: BoxCoordinates | None = None
        for y in range(box.lower + 1, self.map_size.height): # expand down
            new_edge = Point((box.lower_right.x, y))
            if self._is_free_position(BoxCoordinates.from_points(box_edge, new_edge)):
                result = BoxCoordinates.from_points(box.upper_left, new_edge)
            else:
                return result
        
        return result


    def _find_right_expanded_box(self, box: BoxCoordinates) -> BoxCoordinates | None:
        box_edge: Point = Point((box.lower_right.x, box.upper_left.y))
        result: BoxCoordinates | None = None
        for x in range(box.right + 1, self.map_size.width): # expand right
            new_edge = Point((x, box.lower_right.y))
            if self._is_free_position(BoxCoordinates.from_points(box_edge, new_edge)):
                result = BoxCoordinates.from_points(box.upper_left, new_edge)
            else:
                return result
        
        return result

    def _is_free_position(self, box: BoxCoordinates) -> bool:
        return native.py_is_free_position(self.occupancy_map, BoxCoordinates.to_native(box))
