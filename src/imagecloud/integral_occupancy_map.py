import numpy as np
from imagecloud.weighted_image import BoxCoordinates
from imagecloud.native_integral_occupancy_functions import (
    find_free_position,
    reserve_position
)


OccupancyMapDataType = np.uint32
OccupancyMapType = np.ndarray[OccupancyMapDataType, OccupancyMapDataType]
# extrapolated from https://github.com/amueller/word_cloud/blob/main/wordcloud/wordcloud.py
class IntegralOccupancyMap(object):
    def __init__(self, map_size: tuple[int, int]):
        self.map_size = map_size
        # integral is our 'target' for placement of images
        self.occupancy_map: OccupancyMapType  = np.zeros(map_size, dtype=OccupancyMapDataType)

    def find_position(self, size: tuple[int, int], random_state) -> None | tuple[int, int]:
        return find_free_position(self.occupancy_map, size, random_state)

    def reserve(self, pos: tuple[int, int], size: tuple[int, int], reservation_no: int) -> None:
        if reservation_no == 0:
            raise ValueError('reservation_number cannot be zero')
        reserve_position(self.occupancy_map, pos, size, reservation_no)
    
    @staticmethod
    def create_occupancy_map(map_size: tuple[int, tuple], reservations: list[tuple[tuple[int, int], tuple[int, int]]]) -> OccupancyMapType:
        integral = IntegralOccupancyMap(map_size)
        for i in range(len(reservations)):
            integral.reserve(reservations[i][0], reservations[i][1], i + 1)
        return integral.occupancy_map
        