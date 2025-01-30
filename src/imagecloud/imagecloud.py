from imagecloud.console_logger import ConsoleLogger
from PIL import Image
from random import Random
import warnings
import numpy as np

from imagecloud.position_box_size import (
    Size,
    Position,
    BoxCoordinates
)
from imagecloud.imagecloud_helpers import (
    parse_to_int,
    parse_to_float,
    parse_to_size,
)
from imagecloud.weighted_image import (
    NamedImage,
    WeightedImage,
    sort_by_weight,
    resize_images_to_proportionally_fit,
    grow_size_by_step,
    shrink_size_by_step,
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
                 size: Size | None = None,
                 background_color: str | None = None,
                 max_images: int | None = None,
                 max_image_size: Size | None = None,
                 min_image_size: Size | None = None,
                 image_step: int | None = None,
                 maintain_aspect_ratio: bool | None = None,
                 scale: float | None = None,
                 contour_width: float | None = None,
                 contour_color: str | None = None,
                 prefer_horizontal: float | None = None,
                 margin: int | None = None,
                 mode: str | None = None,
                 logger: ConsoleLogger | None = None
    ) -> None:
        self._mask: np.ndarray | None = np.array(mask) if mask is not None else None
        self._size = size if size is not None else parse_to_size(helper.DEFAULT_CLOUD_SIZE)
        self._background_color = background_color if background_color is not None else helper.DEFAULT_BACKGROUND_COLOR
        self._max_images = max_images if max_images is not None else parse_to_int(helper.DEFAULT_MAX_IMAGES)
        self._max_image_size = max_image_size
        self._min_image_size = min_image_size if min_image_size is not None else parse_to_size(helper.DEFAULT_MIN_IMAGE_SIZE)
        self._image_step = image_step if image_step is not None else parse_to_int(helper.DEFAULT_STEP_SIZE)
        self._maintain_aspect_ratio = maintain_aspect_ratio if maintain_aspect_ratio is not None else helper.DEFAULT_MAINTAIN_ASPECT_RATIO
        self._scale = scale if scale is not None else parse_to_float(helper.DEFAULT_SCALE)
        self._contour_width = contour_width if contour_width is not None else parse_to_int(helper.DEFAULT_CONTOUR_WIDTH)
        self._contour_color = contour_color if contour_color is not None else helper.DEFAULT_CONTOUR_COLOR
        self._logger = logger

        self._prefer_horizontal = prefer_horizontal if prefer_horizontal is not None else parse_to_float(helper.DEFAULT_PREFER_HORIZONTAL)
        self._margin = margin if margin is not None else parse_to_int(helper.DEFAULT_MARGIN)
        self._mode = mode if mode is not None else helper.DEFAULT_MODE
        self._random_state = None
        self.layout_: Layout | None = None

    @property
    def mask(self) -> np.ndarray | None:
        return self._mask
    
    @mask.setter
    def mask(self, v: np.ndarray | None) -> None:
        self._mask = v

    @property
    def size(self) -> Size:
        return self._size
    
    @size.setter
    def size(self, v: Size) -> None:
        self._size = v
        if self._mask is not None:
            self._mask = None
            
    @property
    def image_step(self) -> int:
        return self._image_step

    @property
    def maintain_aspect_ratio(self) -> bool:
        return self._maintain_aspect_ratio

    @property
    def layout(self) -> Layout | None:
        return self.layout_
    
    @layout.setter
    def layout(self, v: Layout) -> None:
        self.layout_ = v
    
    def generate(self,
                weighted_images: list[WeightedImage],
                max_image_size: Size | None = None,
                cloud_expansion_step_size: int = 0,
    ) -> Layout:
        weighted_images = sort_by_weight(weighted_images, True)[:self._max_images]
        resize_count = 0
        imagecloud_size = self.size
        if self._logger:
            self._logger.info('Generating ImageCloud from {0} images'.format(len(weighted_images)))
            self._logger.push_indent('generating')

        proportional_images = resize_images_to_proportionally_fit(
            weighted_images,
            imagecloud_size,
            self.maintain_aspect_ratio,
            self.image_step,
            self._margin,
            self._logger
        )

        while True:
            if self.mask is not None:
                imagecloud_size = Size((
                    self.mask.shape[0],
                    self.mask.shape[1]
                ))
            
            result = self._generate(
                proportional_images,
                imagecloud_size,
                self._random_state if self._random_state is not None else Random(),
                max_image_size
            )
            if 0 < cloud_expansion_step_size and len(result.items) != len(weighted_images):
                resize_count += 1
                if self.mask is not None:
                    raise ValueError('Cannot expand_cloud_to_fit_all when mask is provided.')
                imagecloud_size = grow_size_by_step(
                    imagecloud_size, 
                    cloud_expansion_step_size, 
                    self.maintain_aspect_ratio
                )
                if self._logger:
                    self._logger.stop_buffering(False)
                    if 1 < resize_count:
                        self._logger.pop_indent()
                    if 0 == (resize_count - 1) % 10:
                        self._logger.info('{0}/{1} images fit. Expanding ImageCloud [{2}] ({3},{4}) -> ({5},{6}) to fit more ...'.format(
                            len(result.items),len(weighted_images), resize_count,
                            self.size[0], self.size[1],
                            imagecloud_size[0], imagecloud_size[1]
                        ))
                    self._logger.push_indent('resize-{0}-{1}-more-images'.format(resize_count, len(weighted_images) - len(result.items)))
                    self._logger.start_buffering()
                continue
            break
        if self._logger:
            self._logger.stop_buffering(True)
            self._logger = self._logger.copy()

        return result
    
    
    def maximize_empty_space(self, layout: Layout | None = None) -> Layout:
        if layout is None:
            self._check_generated()
            layout = self.layout_
        self.layout_ = layout
        occupancy = IntegralOccupancyMap()
        occupancy.occupancy_map = layout.canvas.occupancy_map
        new_items: list[LayoutItem] = list()
        total_images = len(layout.items)
        for i in range(total_images - 1, 0, -1):
            item: LayoutItem = layout.items[i]
            new_reservation = occupancy.expand_occupancy(item.reservation_box())
            occupancy.reserve(new_reservation, item.reservation_no)
            new_items.append(
                LayoutItem(
                    item.original_image,
                    new_reservation.size,
                    new_reservation.position,
                    item.orientation,
                    item.reservation_no
                )
            )
            if not(item.reservation_box().equal(new_reservation)) and self._logger:
                self._logger.info('Maximized empty-space: Image [{0}/{1}] {2} from {3} -> {4}}'.format((total_images - i), total_images, item.name, str(item.reservation_box()), str(new_reservation)))
                

        new_items.reverse()
        self.layout_ = Layout(
            LayoutCanvas(
                layout.canvas.size,
                layout.canvas.mode,
                self.background_color,
                occupancy.occupancy_map
            ),
            LayoutContour(
                layout.contour.mask,
                layout.contour.width,
                layout.contour.color
            ),
            new_items
        )
        return self.layout_

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

    def _generate(self,
                proportional_images: list[WeightedImage],
                imagecloud_size: Size,
                random_state: Random,              
                max_image_size: Size | None
    ) -> Layout: 

        if len(proportional_images) <= 0:
            raise ValueError("We need at least 1 image to plot a image cloud, "
                             "got %d." % len(proportional_images))
        
        occupancy = IntegralOccupancyMap(imagecloud_size)

        images: list[NamedImage] = []
        image_sizes: list[Size] = []
        positions: list[Position] = []
        orientations: list[Image.Transpose | None] = []

        if max_image_size is None:
            # if not provided use default max_size
            max_image_size = self._max_image_size

        if max_image_size is None:
            sizes: list[Size] = []
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
                max_image_size = Size((
                    int(2 * sizes[0].width * sizes[1].width / (sizes[0].width + sizes[1].width)),
                    int(2 * sizes[0].height * sizes[1].height / (sizes[0].height + sizes[1].height))
                ))
            else:
                max_image_size = sizes[0]

        # find best location for each image
        total = len(proportional_images)
        orientation: None | Image.Transpose = None
        for index in range(total):
            weight = proportional_images[index].weight
            image = proportional_images[index].image
            name = proportional_images[index].name
            if self._logger:
                if 0 < index:
                    self._logger.pop_indent()
                self._logger.push_indent('Image-{0}[{1}/{2}]'.format(name, index + 1, total))
            if weight == 0:
                if self._logger:
                    self._logger.info('Dropping 0 weight'.format(
                        index+1, total, name
                    ))
                continue

            if self._logger:
                self._logger.info('finding position in ImageCloud')
            
            sampling_count = 0
            new_image_size = Size(image.size)
            rotate = (self._prefer_horizontal <= random_state.random())
            # sampling we try image 2 ways until we get a position
            # sampling 1:
            #   - randomly choose to rotate or not
            #   - use image's initial size
            #   - search for position
            #   - if found then no more sampling
            #   - otherwise do next sampling:
            #        - do sampling i if we didn't rotate
            #        - do sampling i + 1 if we did rotate
            # sampling i: 
            #   - rotate image - no resize
            #   - search for position
            #   - if found then no more sampling
            #   - otherwise do sampling i + 1
            # sampling i + 1:
            #   - unrotate image (sampling i had us rotate the size)
            #   - shrink size by configured step
            #   - if new image size is too small then no more sampling
            #   - search for position
            #   - if found then no more sampling
            #   - otherwise do sampling i (lets try rotating and searching)

            while True:
                sampling_count += 1
                if self._logger:
                    if 1 < sampling_count:
                        self._logger.pop_indent()
                    if 0 == sampling_count % 10:
                        self._logger.debug('sampling {0}...'.format(sampling_count))
                    self._logger.push_indent('Sampling {0}'.format(sampling_count))
                if new_image_size < self._min_image_size:
                    # image-size went too small
                    break

                if rotate:
                    orientation = Image.Transpose.ROTATE_90
                    if self._logger:
                        self._logger.debug('transpose {0}'.format(orientation.name))
                    new_image_size = new_image_size.transpose(orientation)
                elif 1 < sampling_count and self._logger:
                    self._logger.debug('resizing ({0},{1}) -> {2}'.format(
                        image.size[0], image.size[1],
                        str(new_image_size)
                    ))
                
                # find a free position to occupy                
                paste_position = occupancy.find_position(
                    new_image_size.adjust(self._margin, False),
                    random_state
                )
                if paste_position is not None:
                    # Found a place
                    break
                if rotate: # try resizing before rotating again
                    new_image_size = new_image_size.untranspose(orientation)
                    new_image_size = shrink_size_by_step(new_image_size, self.image_step, self.maintain_aspect_ratio)
                    rotate = False
                    orientation = None
                else: # try rotating before resizing
                    rotate = True
                    
            if self._logger:
                self._logger.pop_indent()

            if new_image_size < self._min_image_size:
                if self._logger:
                    self._logger.info('Dropping Image. resized too small')
                break
            paste_position = paste_position.adjust(self._margin //2)

            images.append(proportional_images[index])
            image_sizes.append(new_image_size)
            positions.append(paste_position)
            orientations.append(orientation)
            
            occupancy.reserve(BoxCoordinates(paste_position, new_image_size), index + 1)

        if self._logger:
            self._logger.pop_indent()
        items: list[LayoutItem] = list()
        for i in range(len(images)):
            items.append(
                LayoutItem(
                    images[i],
                    image_sizes[i],
                    positions[i],
                    orientations[i],
                    i + 1
                )
            )
        self.layout_ = Layout(
            LayoutCanvas(
                imagecloud_size,
                self._mode,
                self._background_color,
                occupancy.occupancy_map
            ),
            LayoutContour(
                self._get_boolean_mask(self._mask) * 255 if self._mask is not None else None,
                self._contour_width,
                self._contour_color
            ),
            items
        )
        return self.layout_

    def _check_generated(self) -> None:
        """Check if ``layout_`` was computed, otherwise raise error."""
        if not hasattr(self, "layout_"):
            raise ValueError("ImageCloud has not been calculated, call generate"
                             " first.")
    
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

    @staticmethod
    def wrap_layout(
        layout: Layout,
        logger: ConsoleLogger | None = None
    ):
        result = ImageCloud(
            layout.contour.mask,
            layout.canvas.size,
            layout.canvas.background_color,
            None,
            None,
            None,
            None,
            None,
            None,
            layout.contour.width,
            layout.contour.color,
            None,
            None,
            layout.canvas.mode,
            logger
        )
        result.layout = layout
        return result