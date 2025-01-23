from collections.abc import Callable
from PIL import Image
import csv

WEIGHT_HEADER = 'weight'
IMAGE_FILEPATH_HEADER = 'image_filepath'
CSV_FILE_HELP = '''csv file with following format:
"{0}","{1}"
"<full-path-to-image-file-1>",<weight-as-number-1>
...
"<full-path-to-image-file-N>",<weight-as-number-N>

'''.format(IMAGE_FILEPATH_HEADER, WEIGHT_HEADER)

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