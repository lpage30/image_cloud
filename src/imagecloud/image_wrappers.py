import os
import csv
from PIL import Image
from imagecloud.size import (
    ResizeType,
    Size,
    WeightedSize
)
from imagecloud.native.size import (
    native_create_weighted_size_array,
    native_resize_to_proportionally_fit
)

class NamedImage:
    
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
        return Size(self._image.width, self._image.height)
    
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

class WeightedImage(NamedImage, WeightedSize):
    
    def __init__(self, weight: float, image: Image.Image, name: str | None = None, original_image: Image.Image | None = None) -> None:
        super().__init__(image=image, name=name, original_image=original_image)
        WeightedSize.__init__(self, weight=weight, width=image.width, height=image.height)

    @staticmethod
    def load(weight: float, image_filepath: str):
        named_image = NamedImage.load(image_filepath)
        return WeightedImage(weight, named_image.image, named_image.name)
        


def sort_by_weight(
    weighted_images: list[WeightedImage],
    reverse: bool
) -> list[WeightedImage]:
    return sorted(weighted_images, key=lambda i: i.weight, reverse=reverse)



def resize_images_to_proportionally_fit(
    weighted_images: list[WeightedImage],
    fit_size: Size,
    resize_type: ResizeType,
    step_size: int,
    margin: int
) -> list[WeightedImage]:
    
    weighted_sizes: WeightedSize[:] = native_create_weighted_size_array(len(weighted_images))
    for i in range(len(weighted_images)):
        weighted_sizes[i] = weighted_images[i].to_native_weightedsize()
    
    weighted_sizes = native_resize_to_proportionally_fit(
        weighted_sizes,
        fit_size.to_native_size(),
        resize_type.value,
        step_size,
        margin
    )
    result: list[WeightedImage] = list()
    for i in range(len(weighted_images)):
        result.append(WeightedImage(
            weighted_images[i].weight, 
            weighted_images[i].image.resize(WeightedSize.from_native(weighted_sizes[i]).image_tuple),
            weighted_images[i].name,
            weighted_images[i].original_named_image.image
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
