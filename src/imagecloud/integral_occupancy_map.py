import numpy as np
from imagecloud.position_box_size import (
    Size,
    Position,
    BoxCoordinates
)
import imagecloud.native_integral_occupancy_functions as native


OccupancyMapDataType = np.uint32
OccupancyMapType = np.ndarray[OccupancyMapDataType, OccupancyMapDataType]
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
        native.reserve_position(self._occupancy_map, box.native, reservation_no)
    
    def expand_occupancy(self, box: BoxCoordinates) -> BoxCoordinates:
        result = native.expand_occupancy(self._occupancy_map, box.native)
        return BoxCoordinates.from_native(result)
    
    @staticmethod
    def create_occupancy_map(map_size: Size, reservations: list[BoxCoordinates]) -> OccupancyMapType:
        integral = IntegralOccupancyMap(map_size)
        for i in range(len(reservations)):
            integral.reserve(reservations[i], i + 1)
        return integral.occupancy_map
    
