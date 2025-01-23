from collections.abc import Callable
from PIL import Image, ImageFilter
import warnings
from random import Random
import numpy as np
import imagecloud.common.string_parsers as parsers
import imagecloud.imagecloud_defaults as helper
import imagecloud.common.query_integral_image as integral

WeightedImageType = tuple[float, Image.Image]

def create_weighted_image(weight: float, image: Image.Image) -> WeightedImageType:
    return (weight, image)

def get_weight(weighted_image: WeightedImageType) -> float:
    return weighted_image[0]

def get_image(weighted_image: WeightedImageType) -> Image.Image:
    return weighted_image[1]

def sort_by_weight(
    weighted_images: list[WeightedImageType],
    reverse: bool
) -> list[WeightedImageType]:
    return sorted(weighted_images, key=lambda i: get_weight(i), reverse=reverse)

def resize_images(
    weighted_images: list[WeightedImageType],
    new_size: tuple[int, int],
    reportProgress: Callable[[str], None] | None = None
) -> list[WeightedImageType]:
    result: list[WeightedImageType] = list()
    total = len(weighted_images)
    for index in range(total):
        weighted_image = weighted_images[index]
        if get_image(weighted_image).size[0] == new_size[0] and get_image(weighted_image).size[1] == new_size[1]:
            result.append(weighted_image)
            continue
        if reportProgress:
            reportProgress('Image[{0}/{1}] resize ({2},{3}) -> ({4},{5})'.format(
                index+1,total,
                get_image(weighted_image).size[0], get_image(weighted_image).size[1],
                new_size[0], new_size[1]
            ))
        result.append(create_weighted_image(
            get_weight(weighted_image),
            get_image(weighted_image).resize(new_size)
        ))
    return result

        
    
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
        width and height of canvas

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

    image_step : (width, height) (default=helper.DEFAULT_STEP_SIZE)
        Step size for the image. image_step[0] | image_step[1] > 1 might speed up computation but
        give a worse fit.
        
    scale : float (default=helper.DEFAULT_SCALE)
        Scaling between computation and drawing. For large word-cloud images,
        using scale instead of larger canvas size is significantly faster, but
        might lead to a coarser fit for the words.

    contour_width: float (default=helper.DEFAULT_CONTOUR_WIDTH)
        If mask is not None and contour_width > 0, draw the mask contour.
    
    contour_color: color value (default=helper.DEFAULT_CONTOUR_COLOR)
        Mask contour color.
    
    repeat : bool, default=helper.DEFAULT_REPEAT
        Whether to repeat images until max_images or min_image_size
        is reached.

    relative_scaling : float (default=None)
        Importance of relative word frequencies for font-size.  With
        relative_scaling=0, only word-ranks are considered.  With
        relative_scaling=1, a word that is twice as frequent will have twice
        the size.  If you want to consider the word frequencies and not only
        their rank, relative_scaling around .5 often looks good.
        If 'auto' it will be set to 0.5 unless repeat is true, in which
        case it will be set to 0.
    
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
                 image_step: tuple[int, int] | None = None,
                 scale: float | None = None,
                 contour_width: float | None = None,
                 contour_color: str | None = None,
                 repeat: bool | None = None,
                 relative_scaling: float | None = None,
                 prefer_horizontal: float | None = None,
                 margin: int | None = None,
                 mode: str | None = None
    ) -> None:
        self._mask = np.array(mask) if mask != None else None
        self._size = size if size != None else parsers.parse_to_tuple(helper.DEFAULT_CLOUD_SIZE)
        self._background_color = background_color if background_color != None else helper.DEFAULT_BACKGROUND_COLOR
        self._max_images = max_images if max_images != None else parsers.parse_to_int(helper.DEFAULT_MAX_IMAGES)
        self._max_image_size = max_image_size
        self._min_image_size = min_image_size if min_image_size != None else helper.parse_to_tuple(helper.DEFAULT_MIN_IMAGE_SIZE)
        self._image_step = image_step if image_step != None else parsers.parse_to_tuple(helper.DEFAULT_STEP_SIZE)
        self._scale = scale if scale != None else parsers.parse_to_float(helper.DEFAULT_SCALE)
        self._contour_width = contour_width if contour_width != None else parsers.parse_to_int(helper.DEFAULT_CONTOUR_WIDTH)
        self._contour_color = contour_color if contour_color != None else helper.DEFAULT_CONTOUR_COLOR
        self._repeat = repeat if repeat != None else helper.DEFAULT_REPEAT

        if relative_scaling == None:
            if self._repeat:
                relative_scaling = 0
            else:
                relative_scaling = .5

        if relative_scaling < 0 or relative_scaling > 1:
            raise ValueError("relative_scaling needs to be "
                             "between 0 and 1, got %f." % relative_scaling)
        self._relative_scaling = relative_scaling
        self._prefer_horizontal = prefer_horizontal if prefer_horizontal != None else parsers.parse_to_float(helper.DEFAULT_PREFER_HORIZONTAL)
        self._margin = margin if margin != None else parsers.parse_to_int(helper.DEFAULT_MARGIN)
        self._mode = mode if mode != None else helper.DEFAULT_MODE
        self._random_state = None

    def generate(self,
                weighted_images: list[WeightedImageType],
                max_image_size: tuple[int, int] | None = None,
                reportProgress: Callable[[str], None] | None = None
    ) -> None: 
        if len(weighted_images) <= 0:
            raise ValueError("We need at least 1 image to plot a image cloud, "
                             "got %d." % len(weighted_images))
 
        if self._mask is not None:
            boolean_mask = self._get_boolean_mask(self._mask)
            width = self._mask.shape[1]
            height = self._mask.shape[0]
        else:
            boolean_mask = None
            height, width = self._size[1], self._size[0]

        weighted_images = resize_images(
            sort_by_weight(weighted_images, True)[:self._max_images],
            (width, height),
            reportProgress
        )
        max_weight = get_weight(weighted_images[0])
        percent_images = [create_weighted_image(get_weight(weighted_image) / max_weight, get_image(weighted_image))
                       for weighted_image in weighted_images]
        
        occupancy = IntegralOccupancyMap(height, width, boolean_mask)

        if self._random_state is not None:
            random_state = self._random_state
        else:
            random_state = Random()

        # create cloud image
        cloud_image = Image.new("L", (width, height))
        cloud_image_array = np.asarray(cloud_image)
        image_sizes, positions, orientations = [], [], []

        last_percent = 1.

        if max_image_size is None:
            # if not provided use default max_size
            max_image_size = self._max_image_size

        if max_image_size is None:
            # figure out a good image_size by trying the 1st two inages
            if len(percent_images) == 1:
                # we only have one word. We make it big!
                image_size = self._size
            else:
                self.generate(
                    percent_images[:2],
                    self._size,
                    reportProgress
                )
                # find image sizes
                sizes = [x[1] for x in self.layout_]
                try:
                    image_size = (
                        int(2 * sizes[0][0] * sizes[1][0] / (sizes[0][0] + sizes[1][0])),
                        int(2 * sizes[0][1] * sizes[1][1] / (sizes[0][1] + sizes[1][1]))
                    )
                # quick fix for if self.layout_ contains less than 2 values
                # on very small images it can be empty
                except IndexError:
                    try:
                        image_size = sizes[0]
                    except IndexError:
                        raise ValueError(
                            "Couldn't find space to paste. Either the Canvas size"
                            " is too small or too much of the image is masked "
                            "out.")
        else:
            image_size = max_image_size

        if self._repeat and len(percent_images) < self._max_images:
            # pad  with repeating images.
            times_extend = int(np.ceil(self._max_images / len(percent_images))) - 1
            # get smallest frequency
            percent_images_org = list(percent_images)
            downweight = get_weight(percent_images[-1])
            for i in range(times_extend):
                percent_images.extend([create_weighted_image(get_weight(percent_image) * downweight ** (i + 1), get_image(percent_image))
                                    for percent_image in percent_images_org])

        # find best location for each image
        total = len(percent_images)
        for index in range(total):
            percent = get_weight(percent_images[index])
            image = get_image(percent_images[index])
            if reportProgress:
                reportProgress('generating imagecloud: {0}/{1}...'.format(index+1, total))
            if percent == 0:
                continue
            # select the font size
            rs = self._relative_scaling
            if rs != 0:
                image_size = (
                                int(round((rs * (percent / float(last_percent))
                                       + (1 - rs)) * image_size[0])),
                                int(round((rs * (percent / float(last_percent))
                                       + (1 - rs)) * image_size[1]))
                            )
            if random_state.random() < self._prefer_horizontal:
                orientation = None
            else:
                orientation = Image.ROTATE_90
            tried_other_orientation = False
            sampling_count = 0
            
            while True:
                sampling_count += 1
                if reportProgress and 0 == sampling_count % 10:
                    reportProgress('image[{0}/{1}] sampling {2}...'.format(index+1, total, sampling_count))
                    
                if image_size[0] < self._min_image_size[0] or image_size[1] < self._min_image_size[1]:
                    # image-size went too small
                    break
                
                # try to find a position
                new_image = image.resize(image_size)
                # transpose image optionally
                if orientation != None:
                    new_image = new_image.transpose(orientation)
                
                # get size of resulting image
                # find possible places using integral image:
                result = occupancy.sample_position(new_image.size[1] + self._margin,
                                                   new_image.size[0] + self._margin,
                                                   random_state)
                if result is not None:
                    # Found a place
                    break
                # if we didn't find a place, make image smaller
                # but first try to rotate!
                if not tried_other_orientation and self._prefer_horizontal < 1:
                    orientation = (Image.ROTATE_90 if orientation is None else
                                   Image.ROTATE_90)
                    tried_other_orientation = True
                else:
                    image_size = (
                        image_size[0] - self._image_step[0],
                        image_size[1] - self._image_step[1]
                    )
                    orientation = None

            if image_size[0] < self._min_image_size[0] or image_size[1] < self._min_image_size[1]:
                # we were unable to draw any more
                break

            x, y = np.array(result) + self._margin // 2
            # actually paste image
            cloud_image.paste(new_image, (x, y))
            positions.append((x, y))
            orientations.append(orientation)
            image_sizes.append(image_size)
            
            # recompute integral image
            if self._mask is None:
                cloud_image_array = np.asarray(cloud_image)
            else:
                cloud_image_array = np.asarray(cloud_image) + boolean_mask
            # recompute bottom right
            # the order of the cumsum's is important for speed ?!
            occupancy.update(cloud_image_array, x, y)
            last_percent = percent

        self.layout_ = list(zip(
            percent_images,
            image_sizes,
            positions,
            orientations
        ))
    

    def _check_generated(self) -> None:
        """Check if ``layout_`` was computed, otherwise raise error."""
        if not hasattr(self, "layout_"):
            raise ValueError("ImageCloud has not been calculated, call generate"
                             " first.")

    def to_image(
        self,
        reportProgress: Callable[[str], None] | None = None
    ) -> Image.Image:
        self._check_generated()
        if self._mask is not None:
            width = self._mask.shape[1]
            height = self._mask.shape[0]
        else:
            height, width = self._size[1], self._size[0]

        cloud_image = Image.new(
            self._mode, (
                int(width * self._scale),
                int(height * self._scale)
            ),
            self._background_color
        )
        """
        layout_ format: list[
            tuple[
                WeightedImageType,
                image_size,
                position,
                orientation
            ]
        ]
        """
        total = len(self.layout_)
        for index in range(total):
            percent_image, size, position, orientation = self.layout_[index]
            image = get_image(percent_image)

            if reportProgress:
                reportProgress('scaling/pasting image {0}/{1} into collage'.format(index+1, total))
            
            new_image = image.resize((
                round(size[0] * self._scale),
                round(size[1] * self._scale)
            ))
            if orientation != None:
                new_image = new_image.transpose(orientation)

            pos = (round(position[1] * self._scale),
                   round(position[0] * self._scale))
            cloud_image.paste(new_image, pos)
        return self._draw_contour(img=cloud_image)

    def to_array(self,
        reportProgress: Callable[[str], None] | None = None
    ) -> np.ndarray:
        """Convert to numpy array.

        Returns
        -------
        image : nd-array size (width, height, 3)
            Word cloud image as numpy matrix.
        """
        return np.array(self.to_image(reportProgress=reportProgress))
        
        
    def _draw_contour(self, img) -> Image.Image:
        """Draw mask contour on a pillow image."""
        if self._mask is None or self._contour_width == 0:
            return img

        mask = self._get_boolean_mask(self._mask) * 255
        contour = Image.fromarray(mask.astype(np.uint8))
        contour = contour.resize(img.size)
        contour = contour.filter(ImageFilter.FIND_EDGES)
        contour = np.array(contour)

        # make sure borders are not drawn before changing width
        contour[[0, -1], :] = 0
        contour[:, [0, -1]] = 0

        # use gaussian to change width, divide by 10 to give more resolution
        radius = self._contour_width / 10
        contour = Image.fromarray(contour)
        contour = contour.filter(ImageFilter.GaussianBlur(radius=radius))
        contour = np.array(contour) > 0
        contour = np.dstack((contour, contour, contour))

        # color the contour
        ret = np.array(img) * np.invert(contour)
        if self.contour_color != 'black':
            color = Image.new(img.mode, img.size, self.contour_color)
            ret += np.array(color) * contour

        return Image.fromarray(ret)
    
    def _get_boolean_mask(self, mask) -> bool | np.ndarray:
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
        
        return integral.query_integral_image(self.integral, size_x, size_y,
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
