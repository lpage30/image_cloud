import numpy as np
from query_integral_image import query_integral_image # type: ignore

# copied from https://github.com/amueller/word_cloud/blob/main/wordcloud/wordcloud.py

class IntegralOccupancyMap(object):
    def __init__(self, height, width, mask):
        self.height = height
        self.width = width
        if mask is not None:
            # the order of the cumsum's is important for speed ?!
            self.integral = np.cumsum(np.cumsum(255 * mask, axis=1),
                                      axis=0).astype(np.uint32)
        else:
            self.integral = np.zeros((height, width), dtype=np.uint32)

    def sample_position(self, size_x, size_y, random_state):
        
        return query_integral_image(self.integral, size_x, size_y,
                                    random_state)

    def update(self, img_array, pos_x, pos_y):
        partial_integral = np.cumsum(np.cumsum(img_array[pos_x:, pos_y:],
                                               axis=1), axis=0)
        # paste recomputed part into old image
        # if x or y is zero it is a bit annoying
        if pos_x > 0:
            if pos_y > 0:
                partial_integral += (self.integral[pos_x - 1, pos_y:]
                                     - self.integral[pos_x - 1, pos_y - 1])
            else:
                partial_integral += self.integral[pos_x - 1, pos_y:]
        if pos_y > 0:
            partial_integral += self.integral[pos_x:, pos_y - 1][:, np.newaxis]

        self.integral[pos_x:, pos_y:] = partial_integral
