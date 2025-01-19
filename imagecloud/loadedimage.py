from PIL import Image
import matplotlib.pyplot as plt
from .datafilepath import DataFilepath

class LoadedImage(object):
    def __init__(self) -> None:
        self._data_filepath: DataFilepath = DataFilepath()
        self._image: Image.Image = Image()
        self._maintain_aspect_ratio: bool = True
        self._original_size: tuple[int, int] = self._image.size

    @property
    def image(self) -> Image.Image:
        return self._image
    
    @property
    def filepath(self) -> str | None:
        return self._data_filepath.original_filepath

    def set_image(self, value: Image.Image, filepath: str | None = None) -> None:
        self._data_filepath = DataFilepath(filepath, value.format)
        self._save_count: int = 0
        self._image = value
        self._original_size = self._image.size

    @property
    def maintain_aspect_ratio(self) -> bool:
        return self._maintain_aspect_ratio

    @maintain_aspect_ratio.setter
    def maintain_aspect_ratio(self, value: bool) -> None:
        self._maintain_aspect_ratio = value

    @property
    def original_size(self) -> tuple[int,int]:
        return self._original_size

    @property
    def original_area(self) -> int:
        return self._original_size[0] * self._original_size[1]
    
    @property
    def original_width(self) -> int:
        return self.original_size[0]

    @property
    def original_height(self) -> int:
        return self.original_size[1]

    @property
    def size(self) -> tuple[int,int]:
        return self._image.size
    
    @property
    def area(self) -> int:
        return self._image.size[0] * self._image.size[1]


    @property
    def width(self) -> int:
        return self.size[0]

    @property
    def height(self) -> int:
        return self.size[1]


    @width.setter
    def width(self, value: int) -> None:
        self.image.resize((
            value, 
            ((value / self.original_width) * self.original_height) if self.maintain_aspect_ratio else self.height
        ))

    @height.setter
    def height(self, value: int) -> None:
        self._image = self.image.resize((
            ((value / self.original_height) * self.original_width) if self.maintain_aspect_ratio else self.width,
            value            
        ))
    
    def scale(self, pct_value: float) -> None:
        self._image = self.image.resize((
            pct_value * self.original_width,
            pct_value * self.original_height
        ))

    def resize(self, new_size: tuple[int, int], maintain_aspect_ratio: bool | None = None) -> None:
        if ((maintain_aspect_ratio == None and self.maintain_aspect_ratio) or maintain_aspect_ratio):
            self.scale(max(
                    new_size[0] / self.original_width,
                    new_size[1] / self.original_height
            ))
        else:
            self._image = self.image.resize(new_size)

    def reset_size(self) -> None:
        self._image = self.image.resize(self.original_size)
    
    def reset_original_size(self) -> None:
        self._original_size = self.image.size
    
    def save(self):
        result: LoadedImage = LoadedImage()
        new_filepath: str = self._data_filepath.saveable_filepath
        result.set_image(self._image, new_filepath)
        self._image.save(new_filepath, self._image_format)
        return result
    
    def show(
        self, 
        size: tuple[float, float] | None = None,
        interpolation: str | None = None     
    ) -> None:
        """
        size size of figure in which to show image
        interpolation values:
            'none', 'auto', 'nearest', 'bilinear',
            'bicubic', 'spline16', 'spline36', 'hanning', 'hamming', 'hermite',
            'kaiser', 'quadric', 'catrom', 'gaussian', 'bessel', 'mitchell',
            'sinc', 'lanczos', 'blackman'.
        """
        
        plt.figure(figsize=size if size != None else (10, 8))
        plt.imshow(self._image, interpolation=interpolation if interpolation != None else 'bilinear')
        plt.axis('off')
        plt.show()

    @staticmethod
    def load(image_filepath: str):
        result = LoadedImage()
        result.set_image(Image.open(image_filepath), image_filepath)
        return result
    
IMAGE_FILE_HELP = '''
any pillow supported image file: png, jpg, ...
'''
INTERPOLATION_TYPES = ['none', 'auto', 'nearest', 'bilinear',
            'bicubic', 'spline16', 'spline36', 'hanning', 'hamming', 'hermite',
            'kaiser', 'quadric', 'catrom', 'gaussian', 'bessel', 'mitchell']

INTERPOLATION_HELP = 'interpolation (default: bilinear): [{0}]'.format(','.join(INTERPOLATION_TYPES))

