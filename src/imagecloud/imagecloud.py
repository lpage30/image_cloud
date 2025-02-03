from imagecloud.base_logger import BaseLogger
from PIL import Image
from random import Random
import warnings
import numpy as np

from imagecloud.position_box_size import Size
from imagecloud.imagecloud_helpers import (
    parse_to_int,
    parse_to_float,
    parse_to_size,
)
from imagecloud.weighted_image import (
    WeightedImage,
    sort_by_weight,
    resize_images_to_proportionally_fit,
    grow_size_by_step,
)
from imagecloud.integral_occupancy_map import IntegralOccupancyMap, SamplingResult
import imagecloud.imagecloud_defaults as helper
from imagecloud.layout import (
    LayoutContour,
    LayoutCanvas,
    LayoutItem,
    Layout
)

# implementation was extrapolated from wordcloud and adapted for images
 
class ImageCloud(object):
    r"""imagecloud object for generating and pasting.

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
        Background color for the imagecloud image.
    
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
            
    margin: int (default=helper.DEFAULT_MARGIN)
        The gap to allow between images
    
    mode : string (default=helper.DEFAULT_MODE)
        Transparent background will be generated when mode is "RGBA" and
        background_color is None.
    """
    def __init__(self,
                 logger: BaseLogger,
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
                 margin: int | None = None,
                 mode: str | None = None,
                 name: str | None = None
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

        self._margin = margin if margin is not None else parse_to_int(helper.DEFAULT_MARGIN)
        self._mode = mode if mode is not None else helper.DEFAULT_MODE
        self._random_state = None
        self._name = name if name is not None else 'imagecloud'
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
        
    def generate(self,
                weighted_images: list[WeightedImage],
                max_image_size: Size | None = None,
                cloud_expansion_step_size: int = 0,
    ) -> Layout:
        weighted_images = sort_by_weight(weighted_images, True)[:self._max_images]
        resize_count = 0
        imagecloud_size = self.size
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
                if 1 == resize_count:
                    self._logger.info('Expanding ImageCloud to fit {0} remaining images.'.format(len(weighted_images) - len(result.items)))
                    self._logger.push_indent('Expanding ImageCloud')
                if 0 == (resize_count - 1) % 10:
                    self._logger.info('{0}/{1} images fit. Expanding ImageCloud [{2}] ({3},{4}) -> ({5},{6}) to fit more ...'.format(
                        len(result.items),len(weighted_images), resize_count,
                        self.size[0], self.size[1],
                        imagecloud_size[0], imagecloud_size[1]
                    ))
                continue
            break

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
        self._logger.info('Maximizing ImageCloud empty-space around  {0} images'.format(total_images))
        self._logger.push_indent('maximizing-empty-space')

        for i in range(total_images - 1, -1, -1):
            item: LayoutItem = layout.items[i]
            expanded_versions = occupancy.find_expanded_box_versions(item.reservation_box)
            self._logger.push_indent('Image-{0}[{1}/{2}]'.format(item.name, total_images - i, total_images))

            if expanded_versions is None:
                new_items.append(item)
                continue
            # maximum expanded box is the possible_box with largest area
            expanded_versions.sort(key=lambda v: v.area, reverse=True)

            new_reservation_box = expanded_versions[0]
            margin = 2 * (item.reservation_box.left - item.placement_box.left)
            occupancy.reserve_box(new_reservation_box, item.reservation_no)
            new_items.append(
                LayoutItem(
                    item.original_image,
                    new_reservation_box.remove_margin(margin),
                    item.orientation,
                    new_reservation_box,
                    item.reservation_no
                )
            )
            self._logger.info('Maximized empty-space: Image [{0}/{1}] {2} from {3} -> {4}'.format(
                (total_images - i), total_images, item.name, str(item.reservation_box), str(new_reservation_box)))
            self._logger.pop_indent()
                

        new_items.reverse()
        self.layout_ = Layout(
            LayoutCanvas(
                layout.canvas.size,
                layout.canvas.mode,
                layout.canvas.background_color,
                occupancy.occupancy_map,
                layout.canvas.name + '.maximized'
            ),
            LayoutContour(
                layout.contour.mask,
                layout.contour.width,
                layout.contour.color
            ),
            new_items,
            layout.max_images,
            layout.min_image_size,
            layout.image_step,
            layout.maintain_aspect_ratio,
            layout.scale,
            layout.margin,
            layout.name + '.maximized'
            
        )
        self._logger = self._logger.copy()

        return self.layout_

    def _generate(self,
                proportional_images: list[WeightedImage],
                imagecloud_size: Size,
                random_state: Random,              
                max_image_size: Size | None
    ) -> Layout: 

        if len(proportional_images) <= 0:
            raise ValueError("We need at least 1 image to plot a imagecloud, "
                             "got %d." % len(proportional_images))
        
        occupancy = IntegralOccupancyMap(imagecloud_size)

        layout_items: list[LayoutItem] = list()

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
                sizes = [x.placement_box.size for x in layout.items]
            
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
        for index in range(total):
            weight = proportional_images[index].weight
            image = proportional_images[index].image
            name = proportional_images[index].name
            self._logger.push_indent('Image-{0}[{1}/{2}]'.format(name, index + 1, total))

            if weight == 0:
                self._logger.info('Dropping 0 weight'.format(
                    index+1, total, name
                ))
                self._logger.pop_indent()
                continue

            self._logger.info('Finding position in ImageCloud')
            
            sampling_result: SamplingResult = occupancy.sample_to_find_free_box(
                Size(image.size),
                self._min_image_size,
                self._margin,
                self._maintain_aspect_ratio,
                self._image_step,
                random_state
            )
            if sampling_result.found_reservation:
                self._logger.info('Found position: samplings({0}), orientation ({1}), resize({2}->{3})'.format(
                    sampling_result.sampling_total,
                    sampling_result.orientation.name if sampling_result.orientation is not None else None,
                    str(Size(image.size)),str(sampling_result.new_size)
                ))
                reservation_no = index + 1
                occupancy.reserve_box(sampling_result.reservation_box, reservation_no)
                layout_items.append(LayoutItem(
                    proportional_images[index],
                    sampling_result.actual_box,
                    sampling_result.orientation,
                    sampling_result.reservation_box,
                    reservation_no
                ))
            else:
                self._logger.info('Dropping image: samplings({0}). {1}'.format(
                    sampling_result.sampling_total,
                    'Image resized too small' if sampling_result.new_size < self._min_image_size else ''
                ))
                
                    
            self._logger.pop_indent()

        self.layout_ = Layout(
            LayoutCanvas(
                imagecloud_size,
                self._mode,
                self._background_color,
                occupancy.occupancy_map,
                self._name
            ),
            LayoutContour(
                self._get_boolean_mask(self._mask) * 255 if self._mask is not None else None,
                self._contour_width,
                self._contour_color
            ),
            layout_items,
            self._max_images,
            self._min_image_size,
            self._image_step,
            self._maintain_aspect_ratio,
            self._scale,
            self._margin,
            self._name + '.layout'
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
    def create(
        layout: Layout,
        logger: BaseLogger
    ):
        result = ImageCloud(
            logger,
            layout.contour.mask,
            layout.canvas.size,
            layout.canvas.background_color,
            layout.max_images,
            None,
            layout.min_image_size,
            layout.image_step,
            layout.maintain_aspect_ratio,
            layout.scale,
            layout.contour.width,
            layout.contour.color,
            layout.margin,
            layout.canvas.mode,
            layout.canvas.name
        )
        result.layout_ = layout
        return result