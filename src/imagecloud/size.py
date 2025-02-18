from imagecloud.native.size import (
    native_create_size,
    native_adjust,
    native_create_weighted_size,
    native_create_weighted_size_array,
    native_resize_to_proportionally_fit
)
from imagecloud.parsers import parse_to_int
from enum import Enum

class ResizeType(Enum):
    NO_RESIZE_TYPE = -1
    MAINTAIN_ASPECT_RATIO = 1
    MAINTAIN_PERCENTAGE_CHANGE = 2

RESIZE_TYPES = [member.name for member in ResizeType]

def parse_to_resize_type(s: str) -> ResizeType:
    for member in ResizeType:
        if s.upper() == member.name:
            return member
    raise ValueError('{0} unsupported. Must be one of [{1}]'.format(s, '{0}'.format('|'.join(RESIZE_TYPES))))

class Size:
    width: int
    height: int
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
    @property
    def image_tuple(self) -> tuple[int, int]:
        return (self.width, self.height)

    @property
    def nd_shape(self) -> tuple[int, int]:
        return (self.height, self.width)
    
    @property
    def area(self) -> int:
        return int(round(self.width * self.height))
    
    def size_to_string(self) -> str:
        return f"Size({self.width}, {self.height})"

    def adjust(self, step: int, resize_type: ResizeType):
        return Size.from_native(
            native_adjust(
                self.to_native_size(), 
                step,
                resize_type.value
            )
        )
    
    def scale(self, scale: float):
        return Size(
            int(round(self.width * scale)),
            int(round(self.height * scale))
        )
    def is_equal(self, other) -> bool:
        return self.width == other.width and self.height == other.height
    
    def is_less_than(self, other) -> bool:
        return self.width < other.width or self.height < other.height
    
    def to_native_size(self):
        return native_create_size(self.width, self.height)
    
    @staticmethod
    def from_native(native_size):
        return Size(native_size['width'], native_size['height'])
    
    @staticmethod
    def parse(s: str):
        width, height = s.split(',')
        return Size(parse_to_int(width), parse_to_int(height))
    

class WeightedSize(Size):
    weight: float
    def __init__(self, weight: float, width: int, height: int) -> None:
        super().__init__(width, height)
        self.weight = weight

    def to_native_weightedsize(self):
        return native_create_weighted_size(self.weight, self.to_native_size())
    
    def from_native(native_weighted_size):
        size = Size.from_native(native_weighted_size['size'])
        return WeightedSize(
            native_weighted_size['weight'],
            size.width,
            size.height
        )

        
def resize_to_proportionally_fit(
    weighted_sizes: list[WeightedSize],
    fit_size: Size,
    resize_type: ResizeType,
    step_size: int,
    margin: int
) -> list[WeightedSize]:
    native_weighted_size_array = native_create_weighted_size_array(len(weighted_sizes))
    for i in range(len(weighted_sizes)):
        native_weighted_size_array[i] = weighted_sizes[i].to_native_weightedsize()
    
    native_weighted_size_array = native_resize_to_proportionally_fit(native_weighted_size_array, fit_size.to_native_size(), resize_type.value, step_size, margin)
    result: list[WeightedSize] = list()
    for item in native_weighted_size_array:
        result.append(WeightedSize.from_native(item))
    return result
    
