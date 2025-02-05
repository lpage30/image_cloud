from imagecloud.base_logger import BaseLogger
import os
import csv
from PIL import Image
from imagecloud.imagecloud_helpers import TimeMeasure
from imagecloud.position_box_size import (ResizeType, Size)
from imagecloud.native.position_box_size import py_sample_resize_to_area

class NamedImage(object):
    
    def __init__(self, image: Image.Image, name: str | None = None, original_image: Image.Image | None = None) -> None:
        self._original_image = original_image if original_image is not None else image
        self._image = image
        self._name = name if name is not None else ''
    
    @property
    def image(self) -> Image.Image:
        return self._image
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def size(self) -> Size:
        return Size(self._image.size)
    
    @property
    def original_named_image(self):
        return NamedImage(self._original_image, self.name)
    
    def show(self) -> None:
        self.image.show(self.name)

    @staticmethod
    def load(image_filepath: str):
        name = os.path.splitext(os.path.basename(image_filepath))[0]
        image = Image.open(image_filepath)
        return NamedImage(image, name)

class WeightedImage(NamedImage):
    
    def __init__(self, weight: float, image: Image.Image, name: str | None = None, original_image: Image.Image | None = None) -> None:
        super().__init__(image, name, original_image)
        self._weight = weight
    
    @property
    def weight(self) -> float:
        return self._weight
    
    @staticmethod
    def load(weight: float, image_filepath: str):
        named_image = NamedImage.load(image_filepath)
        return WeightedImage(weight, named_image.image, named_image.name)
        


def sort_by_weight(
    weighted_images: list[WeightedImage],
    reverse: bool
) -> list[WeightedImage]:
    return sorted(weighted_images, key=lambda i: i.weight, reverse=reverse)


def calculate_distance(one: int, two: int) -> int:
    return abs(one - two)


def grow_size_by_step(
    size: Size,
    step_size: int,
    resize_type: ResizeType
) -> Size:
    return size.adjust(step_size, resize_type)

def shrink_size_by_step(
    size: Size,
    step_size: int,
    resize_type: ResizeType
) -> Size:
    return size.adjust(-step_size, resize_type)

def calculate_closest_size_distance(
    size: Size,
    target_area: int,
    step_size: int,
    resize_type: ResizeType,
) -> tuple[Size, int]:
    
    grown_size = grow_size_by_step(size, step_size, resize_type)
    shrink_size = shrink_size_by_step(size, step_size, resize_type)

    grown_distance = calculate_distance(target_area, grown_size.area)
    shrink_distance = calculate_distance(target_area, shrink_size.area)
    
    if grown_distance <= shrink_distance:
        return (grown_size, grown_distance)
    return (shrink_size, shrink_distance)

    

def resize_images_to_proportionally_fit(
    weighted_images: list[WeightedImage],
    fit_size: Size,
    resize_type: ResizeType,
    step_size: int,
    margin: int,
    logger: BaseLogger
) -> list[WeightedImage]:
    """
    use weights to determine proportion of fit_size for each image
    fit each image to their proportion by iteratively changing the size until the closest fit is made
    return fitted images with their proportions
    """
    result: list[WeightedImage] = list()
    total = len(weighted_images)
    total_weight = sum(weighted_image.weight for weighted_image in weighted_images)
    fit_area = fit_size.area
    logger.info('Proportionally fitting {0} images to {1}'.format(total, str(fit_size)))
    logger.push_indent('fitting')
    fitted_images = 0
    measure0 = TimeMeasure()
    measure0.start()
    for index in range(total):
        weighted_image = weighted_images[index]
        proportion_weight = weighted_image.weight / total_weight
        resize_area = round(proportion_weight * fit_area)
        image_size = weighted_image.size.adjust(margin, False)
        logger.push_indent('image-{0}[{1}/{2}]'.format(weighted_image.name, index+1, total, ))
        measure1 = TimeMeasure()
        measure1.start()
        native_sampled_resize = py_sample_resize_to_area(
            Size.to_native(image_size),
            resize_area,
            step_size,
            resize_type.value
        )
        sampling_total = int(native_sampled_resize['sampling_total'])
        sampled_size = Size.from_native(native_sampled_resize['new_size'])
        measure1.stop()
        new_image = weighted_image.image
        new_image_size = sampled_size.adjust(-1 * margin, False)
        if(weighted_image.size != new_image_size):
            fitted_images += 1
            logger.info('Found Best Fit: samplings({0}) resize({1}->{2}) ({3})'.format(
                sampling_total,
                str(weighted_image.size),
                str(new_image_size),
                measure1.latency_str()
            ))
            new_image = weighted_image.image.resize(new_image_size.tuple)
        logger.pop_indent()
        

        result.append(WeightedImage(
            proportion_weight,
            new_image,
            weighted_image.name,
            weighted_image.image
        ))
    measure0.stop()
    logger.pop_indent()
    logger.info('Fitted {0}/{1} images ({2})'.format(
            fitted_images,
            len(result),
            measure0.latency_str()
        ))    

    return result

WEIGHTED_IMAGE_WEIGHT = 'weight'
WEIGHTED_IMAGE_IMAGE_FILEPATH = 'image_filepath'
WEIGHTED_IMAGES_CSV_FILE_HELP = '''csv file for weighted images with following format:
"{0}","{1}"
"<full-path-to-image-file-1>",<weight-as-number-1>
...
"<full-path-to-image-file-N>",<weight-as-number-N>

'''.format(WEIGHTED_IMAGE_IMAGE_FILEPATH, WEIGHTED_IMAGE_WEIGHT)

def load_weighted_images(csv_filepath: str) -> list[WeightedImage]:
    try:
        result: list[WeightedImage] = list()
        with open(csv_filepath, 'r') as file:    
            csv_reader = csv.DictReader(file, fieldnames=[WEIGHTED_IMAGE_IMAGE_FILEPATH, WEIGHTED_IMAGE_WEIGHT])
            next(csv_reader)
            for row in csv_reader:
                result.append(WeightedImage.load(float(row[WEIGHTED_IMAGE_WEIGHT]), row[WEIGHTED_IMAGE_IMAGE_FILEPATH]))
        return result
    except Exception as e:
        raise Exception(str(e))
