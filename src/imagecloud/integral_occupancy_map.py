import numpy as np

OccupancyMapDataType = np.uint32
OccupancyMapType = np.ndarray[OccupancyMapDataType, OccupancyMapDataType]
# extrapolated from https://github.com/amueller/word_cloud/blob/main/wordcloud/wordcloud.py
class IntegralOccupancyMap(object):
    def __init__(self, map_size: tuple[int, int]):
        self.map_size = map_size
        # integral is our 'target' for placement of images
        self.occupancy_map: OccupancyMapType  = np.zeros(map_size, dtype=OccupancyMapDataType)

    def find_position(self, size: tuple[int, int], random_state) -> None | tuple[int, int]:
        
        scan_width = self.occupancy_map.shape[0]
        scan_height = self.occupancy_map.shape[1]
        positions: list[tuple[int, int]] = list()
    
        # not efficient; for now
        for x in range(scan_width):
            for y in range(scan_height):
                possible = self.occupancy_map[x:(x + size[0]), y:(y + size[1])]
                if 0 == np.sum(possible):
                    positions.append((x,y))

        total_positions = len(positions)
        return None if 0 == total_positions else positions[random_state.randint(0, total_positions - 1)]

    def reserve(self, pos: tuple[int, int], size: tuple[int, int], reservation_no: int) -> None:
        if reservation_no == 0:
            raise ValueError('reservation_number cannot be zero')
        self.occupancy_map[pos[0]:(pos[0] + size[0]), pos[1]:(pos[1] + size[1])] = reservation_no
    
    @staticmethod
    def create_occupancy_map(map_size: tuple[int, tuple], reservations: list[tuple[tuple[int, int], tuple[int, int]]]) -> OccupancyMapType:
        integral = IntegralOccupancyMap(map_size)
        for i in range(len(reservations)):
            integral.reserve(reservations[i][0], reservations[i][1], i + 1)
        return integral.occupancy_map
        