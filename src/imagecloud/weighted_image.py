from imagecloud.console_logger import ConsoleLogger
import os
from PIL import Image

class NamedImage(object):
    
    def __init__(self, image: Image.Image, name: str | None = None) -> None:
        self._image = image
        self._name = name if name != None else ''
    
    @property
    def image(self) -> Image.Image:
        return self._image

    @property
    def name(self) -> str:
        return self._name
    
    @image.setter
    def image(self, image: Image.Image) -> None:
        self._image = image

    @name.setter
    def name(self, name: str) -> None:
        self._name = name
        
    @staticmethod
    def load(image_filepath: str):
        name = os.path.splitext(os.path.basename(image_filepath))[0]
        image = Image.open(image_filepath)
        return NamedImage(image, name)

class WeightedImage(NamedImage):
    
    def __init__(self, weight: float, image: Image.Image, name: str | None = None) -> None:
        super().__init__(image, name)
        self._weight = weight
    
    @property
    def weight(self) -> float:
        return self._weight

    
    @weight.setter
    def weight(self, weight: float) -> None:
        self._weight = weight
        
    @staticmethod
    def load(weight: float, image_filepath: str):
        named_image = NamedImage.load(image_filepath)
        return WeightedImage(weight, named_image.image, named_image.name)
        


def sort_by_weight(
    weighted_images: list[WeightedImage],
    reverse: bool
) -> list[WeightedImage]:
    return sorted(weighted_images, key=lambda i: i.weight, reverse=reverse)

def calculate_area(size: tuple[int, int]) -> int:
    return round(size[0] * size[1])

def calculate_distance(one: int, two: int) -> int:
    return abs(one - two)

def transpose_size(size: tuple[int, int], transpose: Image.Transpose) -> tuple[int, int]:
    if transpose in [Image.Transpose.ROTATE_90, Image.Transpose.ROTATE_270]:
        return (size[1], size[0])
    return size

def remove_transpose_size(size: tuple[int, int], transpose_to_remove: Image.Transpose) -> tuple[int, int]:
    if transpose_to_remove in [Image.Transpose.ROTATE_90, Image.Transpose.ROTATE_270]:
        return (size[1], size[0])
    return size

def _change_size_by_step(
    size: tuple[int, int],
    step_size: int,
    maintain_aspect_ratio: bool,
    grow: bool # grow == grow=True, shrink == grow=False
) -> tuple[int, int]:
    if maintain_aspect_ratio:
        step_change =  (
            round((step_size / size[0]) * size[0]),
            round((step_size / size[1]) * size[1])
        )
    else:
        step_change = (
            step_size,
            step_size
        )
    if grow:
        return ((size[0] + step_change[0]), (size[1] + step_change[1]))
    else:
        return ((size[0] - step_change[0]), (size[1] - step_change[1]))

def grow_size_by_step(
    size: tuple[int, int],
    step_size: int,
    maintain_aspect_ratio: bool
) -> tuple[int, int]:
    return _change_size_by_step(size, step_size, maintain_aspect_ratio, True)

def shrink_size_by_step(
    size: tuple[int, int],
    step_size: int,
    maintain_aspect_ratio: bool
) -> tuple[int, int]:
    return _change_size_by_step(size, step_size, maintain_aspect_ratio, False)

def calculate_closest_size_distance(
    size: tuple[int, int],
    target_area: int,
    step_size: int,
    maintain_aspect_ratio: bool,
) -> tuple[tuple[int, int], int]:
    
    grown_size = grow_size_by_step(size, step_size, maintain_aspect_ratio)
    shrink_size = shrink_size_by_step(size, step_size, maintain_aspect_ratio)

    grown_distance = calculate_distance(target_area, calculate_area(grown_size))
    shrink_distance = calculate_distance(target_area, calculate_area(shrink_size))
    
    if grown_distance <= shrink_distance:
        return (grown_size, grown_distance)
    return (shrink_size, shrink_distance)

    

def resize_images_to_proportionally_fit(
    weighted_images: list[WeightedImage],
    fit_size: tuple[int, int],
    maintain_aspect_ratio: bool,
    step_size: int,
    logger: ConsoleLogger | None = None
) -> list[WeightedImage]:
    """
    use weights to determine proportion of fit_size for each image
    fit each image to their proportion by iteratively changing the size until the closest fit is made
    return fitted images with their proportions
    """
    result: list[WeightedImage] = list()
    total = len(weighted_images)
    total_weight = sum(weighted_image.weight for weighted_image in weighted_images)
    fit_area = fit_size[0] * fit_size[1]
    for index in range(total):
        weighted_image = weighted_images[index]
        proportion_weight = weighted_image.weight / total_weight
        resize_area = round(proportion_weight * fit_area)
        last_image_size = weighted_image.image.size
        last_distance = calculate_distance(resize_area, calculate_area(last_image_size))
        if logger:
            logger.info('resizing Image[{0}/{1}] {2} to fit...'.format(index+1, total, weighted_image.name))

        search_count = 0
        while True:
            search_count += 1
            if logger and 0 == search_count % 10:
                logger.debug('Image[{0}/{1}] {2} finding best fit {3}...'.format(index+1, total, weighted_image.name, search_count))

            best_image_size, best_distance = calculate_closest_size_distance(
                last_image_size,
                resize_area,
                step_size,
                maintain_aspect_ratio
            )
            if last_distance < best_distance:
                break
            else:
                last_distance = best_distance
                last_image_size = best_image_size

        new_image = weighted_image.image
        if(weighted_image.image.size != last_image_size):
            if logger:
                logger.info('Image[{0}/{1}] {2} attempts {3} resize ({4},{5}) -> ({6},{7})'.format(
                    index+1, total, search_count, weighted_image.name,
                    weighted_image.image.size[0], weighted_image.image.size[1],
                    last_image_size[0], last_image_size[1]
                ))
            new_image = weighted_image.image.resize(last_image_size)

        result.append(WeightedImage(
            proportion_weight,
            new_image,
            weighted_image.name
        ))
    return result

        