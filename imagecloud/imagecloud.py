from PIL import Image
from PIL import ImageFilter
import warnings
from random import Random
import numpy as np
from integraloccupancymap import IntegralOccupancyMap

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
                 contour_color: str | None = None
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


    def generate(self, 
                 weighted_images: list[tuple[float, Image.Image]],
                 max_image_size: tuple[int,int] | None = None
    ) -> None: 
        
        # make sure weighted_images are sorted and normalized
        weighted_images = weighted_images.sort(key=lambda val: val[0], reverse=True )
        if len(weighted_images) <= 0:
            raise ValueError("We need at least 1 image to plot a image cloud, "
                             "got %d." % len(weighted_images))
        weighted_images = weighted_images[:self._max_images]

        # largest entry will be 1
        max_weight = float(weighted_images[0][0])

        weighted_images = [(weight / max_weight, image)
                       for weight, image in weighted_images]

        if self.random_state is not None:
            random_state = self.random_state
        else:
            random_state = Random()

        if self.mask is not None:
            boolean_mask = self._get_boolean_mask(self.mask)
            width = self.mask.shape[1]
            height = self.mask.shape[0]
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

        if self.repeat and len(weighted_images) < self._max_images:
            # pad frequencies with repeating words.
            times_extend = int(np.ceil(self._max_images / len(weighted_images))) - 1
            # get smallest frequency
            weighted_images_org = list(weighted_images)
            downweight = weighted_images[-1][0]
            for i in range(times_extend):
                weighted_images.extend([(weight * downweight ** (i + 1), image)
                                    for weight, image in weighted_images_org])

        # start drawing grey image
        for weight, image in weighted_images:
            if weight == 0:
                continue
            # select the font size
            rs = self.relative_scaling
            if rs != 0:
                image_size = (
                                int(round((rs * (weight / float(last_weight))
                                       + (1 - rs)) * image_size[0])),
                                int(round((rs * (weight / float(last_weight))
                                       + (1 - rs)) * image_size[1]))
                            )
            if random_state.random() < self.prefer_horizontal:
                orientation = None
            else:
                orientation = Image.ROTATE_90
            tried_other_orientation = False
            while True:
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
                result = occupancy.sample_position(new_image.size[1] + self.margin,
                                                   new_image.size[0] + self.margin,
                                                   random_state)
                if result is not None:
                    # Found a place
                    break
                # if we didn't find a place, make font smaller
                # but first try to rotate!
                if not tried_other_orientation and self.prefer_horizontal < 1:
                    orientation = (Image.ROTATE_90 if orientation is None else
                                   Image.ROTATE_90)
                    tried_other_orientation = True
                else:
                    image_size = (image_size[0] - self._image_step[0], image_size[1] - self._image_step[1])
                    orientation = None

            if image_size[0] < self._min_image_size[0] or image_size[1] < self._min_image_size[1]:
                # we were unable to draw any more
                break

            x, y = np.array(result) + self.margin // 2
            # actually paste image
            img_grey.paste(new_image, (y, x))
            positions.append((x, y))
            orientations.append(orientation)
            image_sizes.append(image_size)
            
            # recompute integral image
            if self.mask is None:
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

    def to_image(self) -> Image:
        self._check_generated()
        if self._mask is not None:
            width = self._mask.shape[1]
            height = self._mask.shape[0]
        else:
            height, width = self._size[1], self._size[0]

        img = Image.new(self.mode, (int(width * self._scale),
                                    int(height * self._scale)),
                        self._background_color)
        for (image, count), image_size, position, orientation in self.layout_:
            
            scaled_image = image.resize((image.size[0] * self._scale, image.size[1] * self._scale))
            
            pos = (int(position[1] * self._scale),
                   int(position[0] * self._scale))
            img.paste(scaled_image, pos)
            

        return self._draw_contour(img=img)

    def to_array(self) -> np.ndarray:
        """Convert to numpy array.

        Returns
        -------
        image : nd-array size (width, height, 3)
            Word cloud image as numpy matrix.
        """
        return np.array(self.to_image())
        
        
    def _draw_contour(self, img) -> Image:
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

MASK_HELP = '''(default: none) Image file
        If not None, gives a binary mask on where to draw words. If mask is not
        None, width and height will be ignored and the shape of mask will be
        used instead. All white (#FF or #FFFFFF) entries will be considerd
        "masked out" while other entries will be free to draw on. [This
        changed in the most recent version!]
'''
CLOUD_SIZE_HELP = '''<width>,<height>
        width : int (default=400)
            Width of the canvas.

        height : int (default=200)
            Height of the canvas.
'''

IMAGE_STEP_HELP = '''<width>,<height> (default=1, 1)
        Step size for the image. image_step[0] | image_step[1] > 1 might speed up computation but
        give a worse fit.
'''
MAX_IMAGE_SIZE_HELP = '''<width>,<height> (default=800, 400)
        Maximum image size for the largest image. If None, height of the image is
        used.
'''
MIN_IMAGE_SIZE_HELP = '''<width>,<height> (default=4, 4)
        Smallest image size to use. Will stop when there is no more room in this
        size.
'''
BACKGROUND_COLOR_HELP = '''(default="white")
        Background color for the image cloud image.
'''

CONTOUR_WIDTH_HELP = '''(default=0)
        If mask is not None and contour_width > 0, draw the mask contour.
'''

CONTOUR_COLOR_HELP = '''(default="black")
        Mask contour color.
'''