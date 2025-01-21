from collections.abc import Callable
from PIL import Image, ImageFilter
import warnings
from random import Random
import numpy as np
from .query_integral_image import query_integral_image

MASK_HELP = '''Image file
        If not None, gives a binary mask on where to draw words. If mask is not
        None, width and height will be ignored and the shape of mask will be
        used instead. All white (#FF or #FFFFFF) entries will be considerd
        "masked out" while other entries will be free to draw on. [This
        changed in the most recent version!]
'''

CLOUD_SIZE_HELP = 'width and height of canvas'

IMAGE_STEP_HELP = '''Step size for the image. image_step[0] | image_step[1] > 1 might speed up computation but
        give a worse fit.
'''

MAX_IMAGE_SIZE_HELP = '''Maximum image size for the largest image. If None, height of the image is
        used.
'''

MIN_IMAGE_SIZE_HELP = '''Smallest image size to use. Will stop when there is no more room in this
        size.
'''

BACKGROUND_COLOR_HELP = 'Background color for the image cloud image.'

CONTOUR_WIDTH_HELP = 'If mask is not None and contour_width > 0, draw the mask contour.'

CONTOUR_COLOR_HELP = 'Mask contour color.'

REPEAT_HELP = 'Whether to repeat images until max_images or min_image_size is reached.'

RELATIVE_SCALING_HELP = '''Importance of relative image frequencies for font-size.  With
        relative_scaling=0, only image-ranks are considered.  With
        relative_scaling=1, a image that is twice as frequent will have twice
        the size.  If you want to consider the image frequencies and not only
        their rank, relative_scaling around .5 often looks good.
        default: it will be set to 0.5 unless repeat is true, in which
        case it will be set to 0.
    '''

PREFER_HORIZONTAL_HELP = '''The ratio of times to try horizontal fitting as opposed to vertical.
        If prefer_horizontal < 1, the algorithm will try rotating the word
        if it doesn't fit. (There is currently no built-in way to get only
        vertical words.)
'''

MARGIN_HELP = 'The gap to allow between images.'

MODE_TYPES = [
    '1', # (1-bit pixels, black and white, stored with one pixel per byte)
    'L', # (8-bit pixels, grayscale)
    'P', # (8-bit pixels, mapped to any other mode using a color palette)
    'RGB', # (3x8-bit pixels, true color)
    'RGBA', # (4x8-bit pixels, true color with transparency mask)
    'CMYK', # (4x8-bit pixels, color separation)
    'YCbCr', # (3x8-bit pixels, color video format)
    'LAB', # (3x8-bit pixels, the L*a*b color space)
    'HSV', # (3x8-bit pixels, Hue, Saturation, Value color space)
    'I', # (32-bit signed integer pixels)
    'F', # (32-bit floating point pixels)
    'LA', # (L with alpha)
    'PA', # (P with alpha)
    'RGBX', # (true color with padding)
    'RGBa', # (true color with premultiplied alpha)
    'La', # (L with premultiplied alpha)
    'I;16', # (16-bit unsigned integer pixels)
    'I;16L', # (16-bit little endian unsigned integer pixels)
    'I;16B', # (16-bit big endian unsigned integer pixels)
    'I;16N'
]
MODE_HELP = '''Transparent background will be generated when mode is "RGBA" and
        background_color is None.: [{0}]
'''.format(','.join(MODE_TYPES))


MODE_HELP = '''Transparent background will be generated when mode is "RGBA" and
        background_color is None.'
'''
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

    size: (width, height)
        width : int (default=400)
            Width of the canvas.

        height : int (default=200)
            Height of the canvas.

    background_color : color value (default="white")
        Background color for the image cloud image.
    
    max_images : number (default=200)
        The maximum number of images.
a
    max_image_size : (width, height) or None (default=None)
        Maximum image size for the largest image. If None, height of the image is
        used.

    min_image_size : (width, height) (default=(4, 4))
        Smallest image size to use. Will stop when there is no more room in this
        size.

    image_step : (width, height) (default=(1, 1))
        Step size for the image. image_step[0] | image_step[1] > 1 might speed up computation but
        give a worse fit.
        
    scale : float (default=1)
        Scaling between computation and drawing. For large word-cloud images,
        using scale instead of larger canvas size is significantly faster, but
        might lead to a coarser fit for the words.

    contour_width: float (default=0)
        If mask is not None and contour_width > 0, draw the mask contour.
    
    contour_color: color value (default="black")
        Mask contour color.
    
    repeat : bool, default=False
        Whether to repeat images until max_images or min_image_size
        is reached.

    relative_scaling : float (default='auto')
        Importance of relative word frequencies for font-size.  With
        relative_scaling=0, only word-ranks are considered.  With
        relative_scaling=1, a word that is twice as frequent will have twice
        the size.  If you want to consider the word frequencies and not only
        their rank, relative_scaling around .5 often looks good.
        If 'auto' it will be set to 0.5 unless repeat is true, in which
        case it will be set to 0.
    
    prefer_horizontal : float (default=0.90)
        The ratio of times to try horizontal fitting as opposed to vertical.
        If prefer_horizontal < 1, the algorithm will try rotating the word
        if it doesn't fit. (There is currently no built-in way to get only
        vertical words.)
        
    margin: int (default=2)
        The gap to allow between images
    
    mode : string (default="RGB")
        Transparent background will be generated when mode is "RGBA" and
        background_color is None.
    """
    def __init__(self, 
                 mask: Image.Image | None = None,
                 size: tuple[int, int] | None = None,
                 background_color: str | None = None,
                 max_images: int | None = None,
                 max_image_size: tuple[int,int] | None = None,
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
        self._size = size if size != None else (800, 400)
        self._background_color = background_color if background_color != None else 'white'
        self._max_images = max_images if max_images != None else 200
        self._max_image_size = max_image_size
        self._min_image_size = min_image_size if min_image_size != None else (4,4)
        self._image_step = image_step if image_step != None else (1,1)
        self._scale = scale if scale != None else 1.0
        self._contour_width = contour_width if contour_width != None else 0
        self._contour_color = contour_color if contour_color != None else 'black'
        self._repeat = repeat if repeat != None else False

        if relative_scaling == None:
            if self._repeat:
                relative_scaling = 0
            else:
                relative_scaling = .5

        if relative_scaling < 0 or relative_scaling > 1:
            raise ValueError("relative_scaling needs to be "
                             "between 0 and 1, got %f." % relative_scaling)
        self._relative_scaling = relative_scaling
        self._prefer_horizontal = prefer_horizontal if prefer_horizontal != None else 0.9
        self._margin = margin if margin != None else 2
        self._mode = mode if mode != None else 'RGB'
        self._random_state = None


    def generate(self, 
                 weighted_images: list[tuple[float, Image.Image]],
                 max_image_size: tuple[int,int] | None = None,
                 reportProgress: Callable[[str], None] | None = None
    ) -> None: 
        
        # make sure weighted_images are sorted and normalized
        weighted_images.sort(key=lambda val: val[0], reverse=True )
        if len(weighted_images) <= 0:
            raise ValueError("We need at least 1 image to plot a image cloud, "
                             "got %d." % len(weighted_images))
        weighted_images = weighted_images[:self._max_images]

        # largest entry will be 1
        max_weight = float(weighted_images[0][0])

        weighted_images = [(weight / max_weight, image)
                       for weight, image in weighted_images]

        if self._random_state is not None:
            random_state = self._random_state
        else:
            random_state = Random()

        if self._mask is not None:
            boolean_mask = self._get_boolean_mask(self._mask)
            width = self._mask.shape[1]
            height = self._mask.shape[0]
        else:
            boolean_mask = None
            height, width = self._size[1], self._size[0]
        occupancy = IntegralOccupancyMap(height, width, boolean_mask)

        # create image
        img_grey = Image.new("L", (width, height))
        img_array = np.asarray(img_grey)
        image_sizes, positions, orientations = [], [], []

        last_weight = 1.

        if max_image_size is None:
            # if not provided use default font_size
            max_image_size = self._max_image_size

        if max_image_size is None:
            # figure out a good font size by trying to draw with
            # just the first two words
            if len(weighted_images) == 1:
                # we only have one word. We make it big!
                image_size = self._size
            else:
                self.generate_from_frequencies(dict(weighted_images[:2]),
                                               max_image_size=self._size)
                # find font sizes
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
                            "Couldn't find space to draw. Either the Canvas size"
                            " is too small or too much of the image is masked "
                            "out.")
        else:
            image_size = max_image_size

        # we set self.words_ here because we called generate_from_frequencies
        # above... hurray for good design?
        self.images_ = dict(weighted_images)

        if self._repeat and len(weighted_images) < self._max_images:
            # pad frequencies with repeating images.
            times_extend = int(np.ceil(self._max_images / len(weighted_images))) - 1
            # get smallest frequency
            weighted_images_org = list(weighted_images)
            downweight = weighted_images[-1][0]
            for i in range(times_extend):
                weighted_images.extend([(weight * downweight ** (i + 1), image)
                                    for weight, image in weighted_images_org])

        # start drawing grey image
        total_images = len(weighted_images)
        for image_index in range(total_images):
            weight, image = weighted_images[image_index]
            if reportProgress:
                reportProgress('generating imagecloud: {0}/{1}...'.format(image_index+1, total_images))
            if weight == 0:
                continue
            # select the font size
            rs = self._relative_scaling
            if rs != 0:
                image_size = (
                                int(round((rs * (weight / float(last_weight))
                                       + (1 - rs)) * image_size[0])),
                                int(round((rs * (weight / float(last_weight))
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
                    reportProgress('image[{0}/{1}] sampling {2}...'.format(image_index+1, total_images, sampling_count))
                    
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
                # if we didn't find a place, make font smaller
                # but first try to rotate!
                if not tried_other_orientation and self._prefer_horizontal < 1:
                    orientation = (Image.ROTATE_90 if orientation is None else
                                   Image.ROTATE_90)
                    tried_other_orientation = True
                else:
                    image_size = (image_size[0] - self._image_step[0], image_size[1] - self._image_step[1])
                    orientation = None

            if image_size[0] < self._min_image_size[0] or image_size[1] < self._min_image_size[1]:
                # we were unable to draw any more
                break

            x, y = np.array(result) + self._margin // 2
            # actually paste image
            img_grey.paste(new_image, (y, x))
            positions.append((x, y))
            orientations.append(orientation)
            image_sizes.append(image_size)
            
            # recompute integral image
            if self._mask is None:
                img_array = np.asarray(img_grey)
            else:
                img_array = np.asarray(img_grey) + boolean_mask
            # recompute bottom right
            # the order of the cumsum's is important for speed ?!
            occupancy.update(img_array, x, y)
            last_weight = weight

        self.layout_ = list(zip(weighted_images, image_sizes, positions,
                                orientations))
    
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

        img = Image.new(self._mode, (int(width * self._scale),
                                    int(height * self._scale)),
                        self._background_color)
        """
        layout_ format: list[
            tuple[
                tuple[weight, image],
                image_size,
                position,
                orientation
            ]
        ]
        """
        total_items = len(self.layout_)
        for item_index in range(total_items):
            if reportProgress:
                reportProgress('scaling/pasting image {0}/{1} into collage'.format(item_index+1, total_items))

            image = self.layout_[item_index][0][1]
            position = self.layout_[item_index][2]
            
            scaled_image = image.resize((image.size[0] * self._scale, image.size[1] * self._scale))
            
            pos = (int(position[1] * self._scale),
                   int(position[0] * self._scale))
            img.paste(scaled_image, pos)
        return self._draw_contour(img=img)

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
