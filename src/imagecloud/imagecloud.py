from imagecloud.base_logger import BaseLogger
from PIL import Image
from random import Random
import warnings
import numpy as np
from imagecloud.size import (Size, ResizeType)
from imagecloud.parsers import (parse_to_float, parse_to_int)
from imagecloud.reservations import (Reservations, SampledUnreservedOpening)
from imagecloud.image_wrappers import (WeightedImage, sort_by_weight, resize_images_to_proportionally_fit)
from imagecloud.time_measure import TimeMeasure
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
    
    resize_type: ResizeType (default=helper.DEFAULT_RESIZE_TYPE)
    
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
                 resize_type: ResizeType | None = None,
                 scale: float | None = None,
                 contour_width: float | None = None,
                 contour_color: str | None = None,
                 margin: int | None = None,
                 mode: str | None = None,
                 name: str | None = None,
                 total_threads: int | None = None
    ) -> None:
        self._mask: np.ndarray | None = np.array(mask) if mask is not None else None
        self._size = size if size is not None else Size.parse(helper.DEFAULT_CLOUD_SIZE)
        self._background_color = background_color if background_color is not None else helper.DEFAULT_BACKGROUND_COLOR
        self._max_images = max_images if max_images is not None else parse_to_int(helper.DEFAULT_MAX_IMAGES)
        self._max_image_size = max_image_size
        self._min_image_size = min_image_size if min_image_size is not None else Size.parse(helper.DEFAULT_MIN_IMAGE_SIZE)
        self._image_step = image_step if image_step is not None else parse_to_int(helper.DEFAULT_STEP_SIZE)
        self._resize_type = resize_type if resize_type is not None else helper.DEFAULT_RESIZE_TYPE
        self._scale = scale if scale is not None else parse_to_float(helper.DEFAULT_SCALE)
        self._contour_width = contour_width if contour_width is not None else parse_to_int(helper.DEFAULT_CONTOUR_WIDTH)
        self._contour_color = contour_color if contour_color is not None else helper.DEFAULT_CONTOUR_COLOR
        self._logger = logger
        self._logger.reset_context()

        self._margin = margin if margin is not None else parse_to_int(helper.DEFAULT_MARGIN)
        self._mode = mode if mode is not None else helper.DEFAULT_MODE
        self._random_state = None
        self._name = name if name is not None else 'imagecloud'
        self._total_threads = total_threads if total_threads is not None else parse_to_int(helper.DEFAULT_TOTAL_THREADS)
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
    def resize_type(self) -> ResizeType:
        return self._resize_type

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
            self.resize_type,
            self.image_step,
            self._margin
        )
        measure = TimeMeasure()
        measure.start()
        while True:
            self._logger.push_indent('creating-imagecloud')
            if self.mask is not None:
                imagecloud_size = Size(
                    self.mask.shape[0],
                    self.mask.shape[1]
                )
            
            result = self._generate(
                proportional_images,
                imagecloud_size,
                self._random_state if self._random_state is not None else Random(),
                max_image_size
            )
            self._logger.pop_indent()
            if 0 < resize_count:
                self._logger.pop_indent()
            if 0 < cloud_expansion_step_size and len(result.items) != len(weighted_images):
                resize_count += 1
                if 1 == resize_count:                    
                    if self.mask is not None:
                        raise ValueError('Cannot expand_cloud_to_fit_all when mask is provided.')  

                new_imagecloud_size = imagecloud_size.adjust(
                    cloud_expansion_step_size, 
                    self.resize_type
                )
                self._logger.info('Expanded ImageCloud ({0} -> {1}) for dropped images ({2}/{3})'.format(
                    imagecloud_size.size_to_string(),
                    new_imagecloud_size.size_to_string(),
                    (len(weighted_images) - len(result.items)),
                    len(weighted_images)
                ))
                imagecloud_size = new_imagecloud_size
                
                self._logger.push_indent('expanded-imagecloud-{0}'.format(resize_count))
                continue
            break

        measure.stop()
        self._logger.pop_indent()
        self._logger.info('Generated: {0}/{1} images ({2})'.format(
            len(result.items),
            len(proportional_images),
            measure.latency_str()
        ))
        self._logger.reset_context()

        return result
    
    
    def maximize_empty_space(self, layout: Layout | None = None) -> Layout:
        if layout is None:
            self._check_generated()
            layout = self.layout_
        self.layout_ = layout
        reservations = Reservations.create_reservations(layout.canvas.reservation_map)
        new_items: list[LayoutItem] = list()
        
        total_images = len(layout.items)
        self._logger.info('Maximizing ImageCloud empty-space around  {0} images'.format(total_images))
        self._logger.push_indent('maximizing-empty-space')
        measure = TimeMeasure()
        measure.start()
        maximized_count = 0

        for i in range(total_images - 1, -1, -1):
            item: LayoutItem = layout.items[i]
            image_measure = TimeMeasure()
            image_measure.start()
            self._logger.push_indent('image-{0}[{1}/{2}]'.format(item.name, total_images - i, total_images))
            new_reservation_box = reservations.maximize_existing_reservation(item.reservation_box)
            image_measure.stop()
            if item.reservation_box.equals(new_reservation_box):
                new_items.append(item)
                continue
            margin = 2 * (item.reservation_box.left - item.placement_box.left)
            reservations.reserve_opening(item.original_image.name, item.reservation_no, new_reservation_box)
            new_items.append(
                LayoutItem(
                    item.original_image,
                    new_reservation_box.remove_margin(margin),
                    item.orientation,
                    new_reservation_box,
                    item.reservation_no,
                    image_measure.latency_str()
                )
            )
            maximized_count += 1
            self._logger.info('resized {0} -> {1}. ({2})'.format(
                item.reservation_box.box_to_string(),
                new_reservation_box.box_to_string(),
                image_measure.latency_str(),
            ))
            self._logger.pop_indent()

        measure.stop()
        self._logger.pop_indent()
        self._logger.info('Maximized {0}/{1} images ({2})'.format(
            maximized_count,
            len(new_items),
            measure.latency_str()
        ))    

        new_items.reverse()
        self.layout_ = Layout(
            LayoutCanvas(
                layout.canvas.size,
                layout.canvas.mode,
                layout.canvas.background_color,
                reservations.reservation_map,
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
            layout.resize_type,
            layout.scale,
            layout.margin,
            layout.name + '.maximized',
            self._total_threads,
            measure.latency_str()
        )
        self._logger.reset_context()

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
        
        reservations = Reservations(self._logger, imagecloud_size, self._total_threads)

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
                max_image_size = Size(
                    int(2 * sizes[0].width * sizes[1].width / (sizes[0].width + sizes[1].width)),
                    int(2 * sizes[0].height * sizes[1].height / (sizes[0].height + sizes[1].height))
                )
            else:
                max_image_size = sizes[0]

        generation_measure = TimeMeasure()
        # find best location for each image
        total = len(proportional_images)
        generation_measure.start()
        for index in range(total):
            weight = proportional_images[index].weight
            image = proportional_images[index].image
            name = proportional_images[index].name
            measure = TimeMeasure()
            measure.start()
            self._logger.push_indent('image-{0}[{1}/{2}]'.format(name, index + 1, total))

            if weight == 0:
                self._logger.info('Dropping 0 weight'.format(
                    index+1, total, name
                ))
                self._logger.pop_indent()
                continue

            self._logger.info('Finding position in ImageCloud')
            
            sampled_result: SampledUnreservedOpening = reservations.sample_to_find_unreserved_opening(
                Size(image.width, image.height),
                self._min_image_size,
                self._margin,
                self._resize_type,
                self._image_step
            )
            measure.stop()
            if sampled_result.found:
                self._logger.info('Found position: samplings({0}), orientation ({1}), resize({2}->{3}) ({4})'.format(
                    sampled_result.sampling_total,
                    sampled_result.orientation.name if sampled_result.orientation is not None else None,
                    Size(image.width, image.height).size_to_string(),
                    sampled_result.new_size.size_to_string(),
                    measure.latency_str()
                ))
                reservation_no = index + 1
                reservations.reserve_opening(name, reservation_no, sampled_result.opening_box)
                layout_items.append(LayoutItem(
                    proportional_images[index],
                    sampled_result.actual_box,
                    sampled_result.orientation,
                    sampled_result.opening_box,
                    reservation_no,
                    measure.latency_str()
                ))
            else:
                self._logger.info('Dropping image: samplings({0}). {1} resize({2} -> {3}) ({4})'.format(
                    sampled_result.sampling_total,
                    'Image resized too small' if sampled_result.new_size.is_less_than(self._min_image_size) else '',
                    Size(image.width, image.height).size_to_string(),
                    sampled_result.new_size.size_to_string(),
                    measure.latency_str()
                ))
                
                    
            self._logger.pop_indent()

        generation_measure.stop()
        self.layout_ = Layout(
            LayoutCanvas(
                imagecloud_size,
                self._mode,
                self._background_color,
                reservations.reservation_map,
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
            self._resize_type,
            self._scale,
            self._margin,
            self._name + '.layout',
            self._total_threads,
            generation_measure.latency_str()
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
            raise ValueError("Got mask of invalid shape: %s" % f'mask({mask.shape[0]},{mask.shape[1]},{mask.shape[2]})')
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
            layout.resize_type,
            layout.scale,
            layout.contour.width,
            layout.contour.color,
            layout.margin,
            layout.canvas.mode,
            layout.canvas.name
        )
        result.layout_ = layout
        return result