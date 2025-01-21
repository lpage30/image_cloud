from collections.abc import Callable
from PIL import Image
import csv
import sys
import statistics
import os.path

DEFAULT_IMAGE_FORMAT = 'png'
DEFAULT_NORMALIZE_TYPE = 'fitsize'

WEIGHT_HEADER = 'weight'
IMAGE_FILEPATH_HEADER = 'image_filepath'
CSV_FILE_HELP = '''csv file with following format:
"{0}","{1}"
"<full-path-to-image-file-1>",<weight-as-number-1>
...
"<full-path-to-image-file-N>",<weight-as-number-N>

'''.format(IMAGE_FILEPATH_HEADER, WEIGHT_HEADER)

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
NORMALIZING_TYPES = ['min', 'max', 'avg', 'median', 'fitsize', 'none']
NORMALIZING_TYPE_HELP = '''type of normalization applied to all images
- {0}: resize all images to size of the {0} image
- {1}: resize all images to equally fit into provided \'{{0}}\' size
- {2}: no normalization applied
'''.format('|'.join(NORMALIZING_TYPES[:-2]), NORMALIZING_TYPES[-2], NORMALIZING_TYPES[-1])

def to_unused_filepath(filepath_prefix: str, suffix: str) -> str:
    result = '{0}.{1}'.format(filepath_prefix, suffix)
    version: int = 0
    while os.path.isfile(result):
        version += 1
        result = '{0}.{1}.{2}'.format(filepath_prefix, version, suffix)
    return result

    
def load_weights_images_filepaths(csv_filepath: str) -> tuple[list[float], list[Image.Image], list[str]]:
    weights: list[float] = list()
    images: list[Image.Image] = list()
    filepaths: list[str] = list()
    with open(csv_filepath, 'r') as file:    
        csv_reader = csv.DictReader(file, fieldnames=[IMAGE_FILEPATH_HEADER, WEIGHT_HEADER])
        next(csv_reader)
        for row in csv_reader:
            weights.append(float(row[WEIGHT_HEADER]))
            images.append(Image.open(row[IMAGE_FILEPATH_HEADER]))
            filepaths.append(row[IMAGE_FILEPATH_HEADER])
    return (weights, images, filepaths)

def rename_filenames(filepaths: list[str], new_suffix: str) -> list[str]:
    result: list[str] = list()
    for fname in filepaths:
        result.append(to_unused_filepath(fname, new_suffix))
    return result 

def save_weights_images(
    weights: list[float], 
    images: list[Image.Image],
    filepaths: list[str],
    csv_filepath: str,
    image_format: str,
    reportProgress: Callable[[str], None] | None = None
) -> None:
    if len(weights) != len(images):
        raise TypeError('Invalid weight_images: lengths are not same')
    image_filepath_prefix: str = '.'.join(csv_filepath.split('.')[:-1])
    total_images = len(images)
    with open(csv_filepath, 'w', newline='') as file:
        csv_writer = csv.DictWriter(file, fieldnames=[IMAGE_FILEPATH_HEADER, WEIGHT_HEADER])
        csv_writer.writeheader()
        for i in range(total_images):
            image_filepath = '{0}.{1}'.format(
                filepaths[i] if i < len(filepaths) else to_unused_filepath('{0}.{1}'.format(image_filepath_prefix, str(i)), image_format),
                image_format
            )
            if reportProgress:
                reportProgress('writing image[{0}/{1}] as {2}'.format(i+1, total_images, image_filepath))
            images[i].save(image_filepath, image_format)
            csv_writer.writerow({
                IMAGE_FILEPATH_HEADER: image_filepath,
                WEIGHT_HEADER: str(weights[i])
            })

def to_weighted_images(weights: list[float], images: list[Image.Image]) -> list[tuple[float, Image.Image]]:
    if len(weights) != len(images):
        raise TypeError('Invalid weight_images: lengths are not same')
    result: list[tuple[float, Image.Image]] = list()
    for i in range(len(weights)):
        result.append((weights[i], images[i]))
    return result

def split_weights_images(weight_images: list[tuple[float, Image.Image]]) -> tuple[list[float], list[Image.Image]]:
    weights: list[float] = list()
    images: list[Image.Image] = list()
    for weight_image in weight_images:
        weights.append(weight_image[0])
        images.append(weight_image[1])
    return (weights, images)

def min_image(images: list[Image.Image]) -> Image.Image | None:
    result: Image.Image | None = None
    min_area: int = sys.maxsize
    for image in images:
        area = image.width * image.height
        if area < min_area:
            min_area = area
            result = image
    return result

def max_image(images: list[Image.Image]) -> Image.Image | None:
    result: Image.Image | None = None
    max_area: int = 0
    for image in images:
        area = image.width * image.height
        if max_area < area:
            max_area = area
            result = image
    return result


def avg_image(images: list[Image.Image]) -> Image.Image | None:
    result: Image.Image | None = None
    avg_area: float = sum((image.width * image.height) for image in images) / images.count
    min_distance: float = sys.maxsize
    for image in images:
        dist: int = abs(avg_area - (image.width * image.height))
        if (dist < min_distance):
            min_distance = dist
            result = image
    return result
    
def median_image(images: list[Image.Image]) -> Image.Image | None:
    result: Image.Image | None = None
    median_area: float = statistics.median((image.width * image.height) for image in images)
    min_distance: float = sys.maxsize
    for image in images:
        dist: int = abs(median_area - (image.width * image.height))
        if (dist < min_distance):
            min_distance = dist
            result = image
    return result    
    
def resize_images(
    images: list[Image.Image],
    new_size: tuple[int, int],
    maintain_aspect_ratio: bool = True,
    reportProgress: Callable[[str], None] | None = None
) -> list[Image.Image]:
    new_area = new_size[0] * new_size[1]
    result: list[Image.Image] = list()
    total_images = len(images)
    for i in range(total_images):
        image = images[i]
        if maintain_aspect_ratio:
            area = image.width * image.height
            percent_change: float = new_area / area
            if reportProgress:
                reportProgress('resize-scaling image[{0}/{1}] by {2}%'.format(i+1, total_images, percent_change))
            result.append(image.resize((round(image.size[0] * percent_change), round(image.size[1] * percent_change))))
        else:
            if reportProgress:
                reportProgress('resizing image[{0}/{1}]'.format(i+1, total_images))
            result.append(image.resize(new_size))
    return result

def scale_images_to_weights(
    weights: list[float],
    images: list[Image.Image],
    reportProgress: Callable[[str], None] | None = None
) -> list[Image.Image]:
    result: list[Image.Image] = list()
    if len(weights) != len(images):
        raise TypeError('Invalid weight_images: lengths are not same')
    total_weight = sum(weight for weight in weights)
    total_images = len(images)
    for i in range(total_images):
        percent_change: float = weights[i] / total_weight
        if reportProgress:
            reportProgress('weight-scaling image[{0}/{1}] to weight by {2}%'.format(i+1, total_images, percent_change))
        result.append(images[i].resize((round(images[i].size[0] * percent_change), round(images[i].size[1] * percent_change))))
    return result

def fitsize_images(
    images: list[Image.Image],
    fit_size: tuple[int, int],
    reportProgress: Callable[[str], None] | None = None
) -> list[Image.Image]:
    fit_area_per_image = (fit_size[0] * fit_size[1]) / len(images)
    result: list[Image.Image] = list()
    total_images = len(images)
    for i in range(total_images):
        image = images[i]
        area = image.width * image.height
        percent_change: float = fit_area_per_image / area
        if reportProgress:
            reportProgress('fit-scaling image[{0}/{1}] by {2}%'.format(i+1, total_images, percent_change))
        result.append(image.resize((round(image.size[0] * percent_change), round(image.size[1] * percent_change))))
    return result

def normalize_images(
    normalizing_type: str,
    images: list[Image.Image],
    fit_size: tuple[int, int] | None = None,
    reportProgress: Callable[[str], None] | None = None
) -> list[Image.Image]:
    normalizing_image: Image.Image | None
    
    match normalizing_type:
        case 'min':
            normalizing_image = min_image(images)
        case 'max':
            normalizing_image = max_image(images)
        case 'avg':
            normalizing_image = avg_image(images)
        case 'median':
            normalizing_image = median_image(images)
        case 'fitsize':
            return fitsize_images(images, fit_size, reportProgress=reportProgress)
        case 'none':
            return images
        case _:
            raise NotImplementedError('normalizing_type {0} not yet supported.'.format(normalizing_type))
    
    if normalizing_image == None:
        raise ValueError('{0} image not found in {1} images'.format(normalizing_type, len(images)))
    
    return resize_images(images, normalizing_image.size, reportProgress=reportProgress) 
    