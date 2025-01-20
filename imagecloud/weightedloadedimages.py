from loadedimage import LoadedImage
from PIL import Image
from datafilepath import DataFilepath
import csv
import sys
import statistics

class WeightedLoadedImages(object):
    
    def __init__(self, csv_filepath: str | None = None) -> None:
        self._data_filepath: DataFilepath = DataFilepath(csv_filepath, 'csv')
        self._total_weight: float = 0.0
        self._maximum_bounding_box: tuple[int, int] = (0, 0)
        self._weighted_image_array: list[tuple[float, LoadedImage]] = list()
        
    @property
    def weighted_images(self) -> list[tuple[float, LoadedImage]]:
        return self._weighted_image_array

    def add_weighted_image(self, value: tuple[float, LoadedImage]) -> None:
        self._total_weight += value[0]
        self._maximum_bounding_box = (
            self._maximum_bounding_box[0] + value[1].size[0], 
            self._maximum_bounding_box[1] + value[1].size[1]
        )
        self._weighted_image_array.append(value)
    
    def min_image_size(self) -> tuple[int, int]:
        result: tuple[int, int] = (0, 0)
        min_size: int = sys.maxsize
        for weighted_image in self._weighted_image_array:
            if min_size > weighted_image[1].original_area:
                min_size = weighted_image[1].original_area
                result = weighted_image[1].original_size
        return result
            
    def max_image_size(self) -> tuple[int, int]:
        result: tuple[int, int] = (0, 0)
        max_size: int = 0
        for weighted_image in self._weighted_image_array:
            if max_size < weighted_image[1].original_area:
                max_size = weighted_image[1].original_area
                result = weighted_image[1].original_size
        return result
    
    def avg_image_size(self) -> tuple[int, int]:
        result: tuple[int, int] = (0, 0)
        avg_size: float = sum(weighted_image[1].original_area for weighted_image in self._weighted_image_array) / self._weighted_image_array.count
        abs_distance: int = sys.maxsize
        for weighted_image in self._weighted_image_array:
            dist: int = abs(avg_size - weighted_image[1].original_area)
            if (dist < abs_distance):
                abs_distance = dist
                result = weighted_image[1].original_area
        return result
    
    def median_image_size(self) -> tuple[int, int]:
        result: tuple[int, int] = (0, 0)
        median_size: float = statistics.median(weighted_image[1].original_area for weighted_image in self._weighted_image_array)
        abs_distance: int = sys.maxsize
        for weighted_image in self._weighted_image_array:
            dist: int = abs(median_size - weighted_image[1].original_area)
            if (dist < abs_distance):
                abs_distance = dist
                result = weighted_image[1].original_area
        return result
    
    def set_image_sizes(self, value: tuple[int, int]) -> None:
        for weighted_image in self._weighted_image_array:
            weighted_image[1].resize(value)
    
    def scale_to_weights(self) -> None:
        for weighted_image in self._weighted_image_array:
            weighted_image[1].scale(weighted_image[0] / self._total_weight)
    
    def save(self):
        new_filename: str = self._data_filepath.saveable_filepath
        result: WeightedLoadedImages = WeightedLoadedImages(new_filename)
        with open(new_filename, 'w', newline='') as file:
            csv_writer = csv.DictWriter(file, fieldnames=['image_filepath', 'weight'])
            csv_writer.writeheader()
            for weighted_image in self._weighted_image_array:
                saved_image = weighted_image[1].save()
                result.add_weighted_image((
                    weighted_image[0],
                    saved_image
                ))
                csv_writer.writerow({'image_filepath': saved_image.filepath, 'weight': str(weighted_image[0])})
        return result

    def to_weighted_image_array(self) -> list[tuple[float, Image.Image]]:
        return [(weight_image[0], weight_image[1].image) for weight_image in self._weighted_image_array]
        
    @staticmethod
    def load(csv_filepath: str):
        result: WeightedLoadedImages = WeightedLoadedImages(csv_filepath)
        with open(csv_filepath, 'r') as file:    
            csv_reader = csv.DictReader(file, fieldnames=['image_filepath', 'weight'])
            for row in csv_reader:
                result.add_weighted_image((
                    float(row['weight']),
                    LoadedImage.load(row['image_filepath'])
                ))
        return result
        
CSV_FILE_HELP = '''
csv file with following format:

"image_filepath","weight"
"<full-path-to-image-file-1>",<weight-as-number-1>
...
"<full-path-to-image-file-N>",<weight-as-number-N>

'''