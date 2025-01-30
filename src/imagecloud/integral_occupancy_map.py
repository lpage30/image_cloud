import numpy as np
from enum import IntEnum
from imagecloud.position_box_size import (
    Size,
    Point,
    Position,
    BoxCoordinates
)
import imagecloud.native_integral_occupancy_functions as native


OccupancyMapDataType = np.uint32
OccupancyMapType = np.ndarray[OccupancyMapDataType, OccupancyMapDataType]
class Direction(IntEnum):
    UP = 1
    LEFT = 2
    DOWN = 3
    RIGHT = 4

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

    def find_position(self, size: Size, random_state) -> None | Position:
        result = native.find_free_position(self._occupancy_map, size.native, random_state)
        return Position.from_native(result) if result is not None else result

    def reserve(self, box: BoxCoordinates, reservation_no: int) -> None:
        if reservation_no == 0:
            raise ValueError('reservation_number cannot be zero')
        for x in range(box.left, box.right):
            for y in range(box.upper, box.lower):
                self.occupancy_map[x, y] = reservation_no
        
    def find_maximum_expanded_box(self, box: BoxCoordinates) -> BoxCoordinates | None:
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
        # maximum expanded box is the possible_box with largest area
        possible_boxes.sort(key=lambda v: v.area, reverse=True)
        
        return possible_boxes[0] if 0 < len(possible_boxes) else None
        
        
    @staticmethod
    def create_occupancy_map(map_size: Size, reservations: list[BoxCoordinates]) -> OccupancyMapType:
        integral = IntegralOccupancyMap(map_size)
        for i in range(len(reservations)):
            integral.reserve(reservations[i], i + 1)
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
        return native.is_free_position(self.occupancy_map, box.native)
