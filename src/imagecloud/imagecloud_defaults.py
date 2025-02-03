DEFAULT_IMAGE_FORMAT = 'png'
DEFAULT_CLOUD_SIZE = '400,200'
DEFAULT_MAINTAIN_ASPECT_RATIO = True
DEFAULT_STEP_SIZE = '1'
DEFAULT_MAX_IMAGE_SIZE = None
DEFAULT_MIN_IMAGE_SIZE = '4,4'
DEFAULT_BACKGROUND_COLOR = None
DEFAULT_CONTOUR_WIDTH = '0'
DEFAULT_CONTOUR_COLOR = 'black'
DEFAULT_MARGIN = '1'
DEFAULT_MODE = 'RGBA'
DEFAULT_MAX_IMAGES = '200'
DEFAULT_SCALE = '1.0'

IMAGE_FORMATS = [
    'blp',
    'bmp',
    'dds',
    'dib',
    'eps',
    'gif',
    'icns',
    'ico',
    'im',
    'jpeg',
    'mpo',
    'msp',
    'pcx',
    'pfm',
    'png',
    'ppm',
    'sgi',
    'webp',
    'xbm'
]
IMAGE_FORMAT_HELP = 'image format: [{0}]'.format(','.join(IMAGE_FORMATS))
    
MASK_HELP = '''Image file
If not None, gives a binary mask on where to draw words.
If mask is not None, width and height will be ignored
and the shape of mask will be used instead. 
All white (#FF or #FFFFFF) entries will be considered "masked out"
while other entries will be free to draw on.\
'''

CLOUD_SIZE_HELP = 'width and height of canvas'

MAINTAIN_ASPECT_RATIO_HELP = '''resize of images to fit will maintain aspect ratio'''
STEP_SIZE_HELP = '''Step size for the image. 
ste p> 1 might speed up computation
but give a worse fit.
'''

MAX_IMAGE_SIZE_HELP = '''Maximum image size for the largest image.
If None, height of the image is used.
'''

MIN_IMAGE_SIZE_HELP = '''Smallest image size to use.
Will stop when there is no more room in this size.
'''

BACKGROUND_COLOR_HELP = 'Background color for the imagecloud image.'

CONTOUR_WIDTH_HELP = 'If mask is not None and contour_width > 0, draw the mask contour.'

CONTOUR_COLOR_HELP = 'Mask contour color.'

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
MODE_HELP = 'Transparent background will be generated when mode is "RGBA" and background_color is None.'
