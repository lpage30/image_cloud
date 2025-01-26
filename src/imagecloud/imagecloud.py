from imagecloud.console_logger import ConsoleLogger
from PIL import Image
from random import Random
import warnings
import numpy as np
from imagecloud.imagecloud_helpers import (
    parse_to_int,
    parse_to_float,
    parse_to_tuple,
)
from imagecloud.weighted_image import (
    NamedImage,
    WeightedImage,
    sort_by_weight,
    resize_images_to_proportionally_fit,
    shrink_size_by_step,
    transpose_size,
    remove_transpose_size,
)
from imagecloud.integral_occupancy_map import IntegralOccupancyMap
import imagecloud.imagecloud_defaults as helper
from imagecloud.layout import (
    LayoutContour,
    LayoutCanvas,
    LayoutItem,
    Layout
)

# implementation was extrapolated from wordcloud and adapted for images
 
class ImageCloud(object):
    r"""Image cloud object for generating and pasting.

    Parameters
    ----------
    mask : Image or None (default=None)
        If not None, gives a binary mask on where to draw words. If mask is not
        None, width and height will be ignored and the shape of mask will be
        used instead. All white (#FF or #FFFFFF) entries will be considerd
        "masked out" while other entries will be free to draw on. [This
        changed in the most recent version!]

    size: (width, height) see helper.DEFAULT_CLOUD_SIZE
        width and height of imagecloud

    background_color : color value (default=helper.DEFAULT_BACKGROUND_COLOR)
        Background color for the image cloud image.
    
    max_images : number (default=helper.DEFAULT_MAX_IMAGES)
        The maximum number of images.

    max_image_size : (width, height) or None (default=None)
        Maximum image size for the largest image. If None, height of the image is
        used.

    min_image_size : (width, height) (default=helper.DEFAULT_MIN_IMAGE_SIZE)
        Smallest image size to use. Will stop when there is no more room in this
        size.

    image_step : int (default=helper.DEFAULT_STEP_SIZE)
        Step size for the image. image_step > 1 might speed up computation but
        give a worse fit.
    
    maintain_aspect_ratio: bool (default=helper.DEFAULT_MAINTAIN_ASPECT_RATIO)
    
    scale : float (default=helper.DEFAULT_SCALE)
        Scaling between computation and drawing. For large word-cloud images,
        using scale instead of larger imagecloud size is significantly faster, but
        might lead to a coarser fit for the words.

    contour_width: float (default=helper.DEFAULT_CONTOUR_WIDTH)
        If mask is not None and contour_width > 0, draw the mask contour.
    
    contour_color: color value (default=helper.DEFAULT_CONTOUR_COLOR)
        Mask contour color.
    
    repeat : bool, default=helper.DEFAULT_REPEAT
        Whether to repeat images until max_images or min_image_size
        is reached.
    
    prefer_horizontal : float (default=helper.DEFAULT_PREFER_HORIZONTAL)
        The ratio of times to try horizontal fitting as opposed to vertical.
        If prefer_horizontal < 1, the algorithm will try rotating the word
        if it doesn't fit. (There is currently no built-in way to get only
        vertical words.)
        
    margin: int (default=helper.DEFAULT_MARGIN)
        The gap to allow between images
    
    mode : string (default=helper.DEFAULT_MODE)
        Transparent background will be generated when mode is "RGBA" and
        background_color is None.
    """
    def __init__(self, 
                 mask: Image.Image | None = None,
                 size: tuple[int, int] | None = None,
                 background_color: str | None = None,
                 max_images: int | None = None,
                 max_image_size: tuple[int, int] | None = None,
                 min_image_size: tuple[int, int] | None = None,
                 image_step: int | None = None,
                 maintain_aspect_ratio: bool | None = None,
                 scale: float | None = None,
                 contour_width: float | None = None,
                 contour_color: str | None = None,
                 repeat: bool | None = None,
                 prefer_horizontal: float | None = None,
                 margin: int | None = None,
                 mode: str | None = None,
                 logger: ConsoleLogger | None = None
    ) -> None:
        self._mask = np.array(mask) if mask != None else None
        self._size = size if size != None else parse_to_tuple(helper.DEFAULT_CLOUD_SIZE)
        self._background_color = background_color if background_color != None else helper.DEFAULT_BACKGROUND_COLOR
        self._max_images = max_images if max_images != None else parse_to_int(helper.DEFAULT_MAX_IMAGES)
        self._max_image_size = max_image_size
        self._min_image_size = min_image_size if min_image_size != None else helper.parse_to_tuple(helper.DEFAULT_MIN_IMAGE_SIZE)
        self._image_step = image_step if image_step != None else parse_to_int(helper.DEFAULT_STEP_SIZE)
        self._maintain_aspect_ratio = maintain_aspect_ratio if maintain_aspect_ratio != None else helper.DEFAULT_MAINTAIN_ASPECT_RATIO
        self._scale = scale if scale != None else parse_to_float(helper.DEFAULT_SCALE)
        self._contour_width = contour_width if contour_width != None else parse_to_int(helper.DEFAULT_CONTOUR_WIDTH)
        self._contour_color = contour_color if contour_color != None else helper.DEFAULT_CONTOUR_COLOR
        self._repeat = repeat if repeat != None else helper.DEFAULT_REPEAT
        self._logger = logger

        self._prefer_horizontal = prefer_horizontal if prefer_horizontal != None else parse_to_float(helper.DEFAULT_PREFER_HORIZONTAL)
        self._margin = margin if margin != None else parse_to_int(helper.DEFAULT_MARGIN)
        self._mode = mode if mode != None else helper.DEFAULT_MODE
        self._random_state = None
        self.layout_: Layout | None = None
        
    def generate(self,
                weighted_images: list[WeightedImage],
                max_image_size: tuple[int, int] | None = None
    ) -> Layout: 
        if self._mask is not None:
            boolean_mask = self._get_boolean_mask(self._mask)
            imagecloud_size = (
                self._mask.shape[0],
                self._mask.shape[1]
            )
        else:
            boolean_mask = None
            imagecloud_size = self._size

        weighted_images = sort_by_weight(weighted_images, True)[:self._max_images]
        weighted_images = resize_images_to_proportionally_fit(
            weighted_images,
            imagecloud_size,
            self._maintain_aspect_ratio,
            self._image_step,
            self._logger
        )
        
        return self._generate(
            weighted_images,
            imagecloud_size,
            self._random_state if self._random_state != None else Random(),
            max_image_size
        )

    def _generate(self,
                proportional_images: list[WeightedImage],
                imagecloud_size: tuple[int, int],
                random_state: Random,              
                max_image_size: tuple[int, int] | None
    ) -> Layout: 

        if len(proportional_images) <= 0:
            raise ValueError("We need at least 1 image to plot a image cloud, "
                             "got %d." % len(proportional_images))
        
        occupancy = IntegralOccupancyMap(imagecloud_size)

        images: list[NamedImage] = []
        image_sizes: list[tuple[int,int]] = []
        positions: list[tuple[int, int]] = []
        orientations: list[Image.Transpose | None] = []

        if max_image_size is None:
            # if not provided use default max_size
            max_image_size = self._max_image_size

        if max_image_size is None:
            sizes: list[tuple[int, int]] = []
            # figure out a good image_size by trying the 1st two inages
            if len(proportional_images) == 1:
                # we only have one word. We make it big!
                sizes = [self._size]
            else:
                layout = self._generate(
                    proportional_images[:2],
                    imagecloud_size,
                    random_state,
                    self._size
                )
                # find image sizes
                sizes = [x.size for x in layout.items]
            
            if 0 == len(sizes):
                raise ValueError(
                    "Couldn't find space to paste. Either the imagecloud size"
                    " is too small or too much of the image is masked "
                    "out.")
            if 1 < len(sizes):
                max_image_size = (
                    int(2 * sizes[0][0] * sizes[1][0] / (sizes[0][0] + sizes[1][0])),
                    int(2 * sizes[0][1] * sizes[1][1] / (sizes[0][1] + sizes[1][1]))
                )
            else:
                max_image_size = sizes[0]

        if self._repeat and len(proportional_images) < self._max_images:
            # pad  with repeating images.
            times_extend = int(np.ceil(self._max_images / len(proportional_images))) - 1
            # get smallest proportion
            proportional_images_org = list(proportional_images)
            smallest_proportion = proportional_images[-1].weight
            for i in range(times_extend):
                proportional_images.extend([
                    WeightedImage(
                        weighted_image.weight * smallest_proportion ** (i + 1),
                        weighted_image.image,
                        weighted_image.name
                    ) for weighted_image in proportional_images_org
                ])

        # find best location for each image
        total = len(proportional_images)
        orientation: None | Image.Transpose = None
        for index in range(total):
            weight = proportional_images[index].weight
            image = proportional_images[index].image
            name = proportional_images[index].name
            if weight == 0:
                if self._logger:
                    self._logger.warning('Dropping Image[{0}/{1}] {2}. 0 weight'.format(
                        index+1, total, name
                    ))
                continue

            if self._logger:
                self._logger.info('generating imagecloud: Image[{0}/{1}] {2}...'.format(index+1, total, name))

            if random_state.random() < self._prefer_horizontal:
                orientation = None
            else:
                orientation = Image.Transpose.ROTATE_90
            tried_other_orientation = False
            sampling_count = 0
            prior_image_size = image.size
            new_image_size = image.size
            while True:
                sampling_count += 1
                if self._logger and 0 == sampling_count % 10:
                    self._logger.debug('Image[{0}/{1}] {2} sampling {3}...'.format(index+1, total, name, sampling_count))
                    
                if new_image_size[0] < self._min_image_size[0] or new_image_size[1] < self._min_image_size[1]:
                    # image-size went too small
                    break

                # change size/orientation if sampling_count > 1
                if new_image_size != prior_image_size and self._logger:
                        self._logger.debug('Image[{0}/{1}] {2} sampling {3} resize ({4},{5}) -> ({6},{7})'.format(
                            index+1, total, sampling_count, name,
                            image.size[0], image.size[1],
                            new_image_size[0], new_image_size[1]
                        ))
                
                # transpose image optionally
                if orientation != None:
                    if self._logger:
                        self._logger.debug('Image[{0}/{1}] {2} sampling {3} transpose {4}'.format(
                            index+1, total, name, sampling_count, orientation.name
                        ))
                    new_image_size = transpose_size(new_image_size, orientation)

                # find a free position to occupy                
                paste_position = occupancy.find_position(
                    (
                        new_image_size[0] + self._margin,
                        new_image_size[1] + self._margin
                    ),
                    random_state
                )
                if paste_position is not None:
                    # Found a place
                    break

                # if we didn't find a place, make image smaller
                # but first try to rotate!
                if not tried_other_orientation and self._prefer_horizontal < 1:
                    orientation = (Image.Transpose.ROTATE_90 if orientation is None else
                                   Image.Transpose.ROTATE_90)
                    tried_other_orientation = True
                else:
                    if orientation != None:
                        new_image_size = remove_transpose_size(new_image_size, orientation)
                        orientation = None
                    prior_image_size = new_image_size
                    new_image_size = shrink_size_by_step(new_image_size, self._image_step, self._maintain_aspect_ratio)
                    

            if new_image_size[0] < self._min_image_size[0] or new_image_size[1] < self._min_image_size[1]:
                if self._logger:
                    self._logger.warning('Dropping Image[{0}/{1}] {2} after {3} samplings. resized too small'.format(
                        index+1, total, name, sampling_count
                    ))
                break

            paste_position = (
                paste_position[0] + self._margin //2,
                paste_position[1] + self._margin //2
            )

            images.append(proportional_images[index])
            image_sizes.append(new_image_size)
            positions.append(paste_position)
            orientations.append(orientation)
            
            occupancy.reserve(paste_position, new_image_size, index + 1)

        items: list[LayoutItem] = list()
        for i in range(len(images)):
            items.append(
                LayoutItem(
                    images[i],
                    image_sizes[i],
                    positions[i],
                    orientations[i]
                )
            )
        self.layout_ = Layout(
            LayoutCanvas(
                imagecloud_size,
                self._mode,
                self._background_color,
                occupancy.occupancy_map
            ),
            items,
            LayoutContour(
                self._get_boolean_mask(self._mask) * 255 if self._mask != None else None,
                self._contour_width,
                self._contour_color
            )
        )
        return self.layout_

    def _check_generated(self) -> None:
        """Check if ``layout_`` was computed, otherwise raise error."""
        if not hasattr(self, "layout_"):
            raise ValueError("ImageCloud has not been calculated, call generate"
                             " first.")

    def to_image(
        self
    ) -> Image.Image:
        self._check_generated()
        return self.layout_.to_image(
            self._scale,
            self._logger
        ).image


    def to_array(self) -> np.ndarray:
        """Convert to numpy array.

        Returns
        -------
        image : nd-array size (width, height, 3)
            Word cloud image as numpy matrix.
        """
        return np.array(self.to_image())
        
    
    def _get_boolean_mask(self, mask: np.ndarray) -> bool | np.ndarray:
        """Cast to two dimensional boolean mask."""
        if mask.dtype.kind == 'f':
            warnings.warn("mask image should be unsigned byte between 0"
                          " and 255. Got a float array")
        if mask.ndim == 2:
            boolean_mask = mask == 255
        elif mask.ndim == 3:
            # if all channels are white, mask out
            boolean_mask = np.all(mask[:, :, :3] == 255, axis=-1)
        else:
            raise ValueError("Got mask of invalid shape: %s" % str(mask.shape))
        return boolean_mask
