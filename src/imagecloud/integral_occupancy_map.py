import numpy as np

# extrapolated from https://github.com/amueller/word_cloud/blob/main/wordcloud/wordcloud.py
class IntegralOccupancyMap(object):
    def __init__(self, map_size: tuple[int, int], mask):
        self.map_size = map_size
        # integral is our 'target' for placement of images
        if mask is not None:
            # the order of the cumsum's is important for speed ?!
            self.occupancy_map = np.cumsum(np.cumsum(255 * mask, axis=1),
                                      axis=0, dtype=np.uint8)
        else:
            self.occupancy_map  = np.zeros(map_size, dtype=np.uint8)

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

    def reserve(self, pos: tuple[int, int], size: tuple[int, int]) -> None:
        self.occupancy_map[pos[0]:(pos[0] + size[0]), pos[1]:(pos[1] + size[1])] = 1
        