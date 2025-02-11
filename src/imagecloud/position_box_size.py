from PIL import Image
from enum import Enum
from imagecloud.native.position_box_size import (
    native_to_position,
    native_to_size,
    native_to_box
)

class ResizeType(Enum):
    NO_RESIZE_TYPE = -1
    MAINTAIN_ASPECT_RATIO = 1
    MAINTAIN_PERCENTAGE_CHANGE = 2

RESIZE_TYPES = [member.name for member in ResizeType]
class Point:
    x: int
    y: int
    def __init__(self, point: tuple[int, int]) -> None:
        self.x = point[0]
        self.y = point[1]
        
    @property
    def tuple(self) -> tuple[int, int]:
        return (self.x, self.y)

    def width(self, other) -> int:
        return self.x - other.x

    def height(self, other) -> int:
        return self.y - other.y

    def __str__(self):
        return f"({self.x},{self.y})"

class Position(Point):
    left: int
    upper: int
    def __init__(self, position: tuple[int, int]) -> None:
        super().__init__(position)
        self.left = position[0]
        self.upper = position[1]
        
    def scale(self, scale: float):
        return Position((
            round(self.left * scale),
            round(self.upper * scale)
        ))

    def adjust(self, step: int):
        down: bool = 0 <= step
        step = abs(step)
        if down:
            return Position(((self.left + step), (self.upper + step)))
        else:
            return Position(((self.left - step), (self.upper - step)))

    @staticmethod
    def to_native(pos):
        return native_to_position(pos.left, pos.upper)

    @staticmethod
    def from_native(native_pos):
        return Position((native_pos['left'], native_pos['upper']))

    @staticmethod
    def from_native_box(native_box):
        return Position((native_box['left'], native_box['upper']))

class Size:
    width: int
    height: int
    def __init__(self, size: tuple[int, int]) -> None:
        self.width = size[0]
        self.height = size[1]
    @property
    def tuple(self) -> tuple[int, int]:
        return (self.width, self.height)
    
    @property
    def area(self) -> int:
        return round(self.width * self.height)
    
    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height

    def percent_change(self, step: int) -> float:
        return abs(step) / self.width
    
    def transpose(self, transpose: Image.Transpose):
        if transpose in [Image.Transpose.ROTATE_90, Image.Transpose.ROTATE_270]:
            return Size((self.height, self.width))
        return Size((self.width, self.height))

    def untranspose(self, transpose: Image.Transpose):
        if transpose in [Image.Transpose.ROTATE_90, Image.Transpose.ROTATE_270]:
            return Size((self.height, self.width))
        return Size((self.width, self.height))

    def adjust(self, step: int, resize_type: ResizeType):
        increase: bool = 0 <= step
        step = abs(step)
        match resize_type:
            case ResizeType.MAINTAIN_ASPECT_RATIO:
                if increase:
                    return Size((
                        self.width + step,
                        int(round((self.width + step) / self.aspect_ratio()))
                    ))
                else:
                    return Size((
                        self.width - step,
                        int(round((self.width - step) / self.aspect_ratio()))
                    ))
            case ResizeType.MAINTAIN_PERCENTAGE_CHANGE:
                    if increase:
                        return Size((
                            self.width + int(round(self.percent_change(step) * self.width)),
                            self.height + int(round(self.percent_change(step) * self.height))
                        ))
                    else:
                        return Size((
                            self.width - int(round(self.percent_change(step) * self.width)),
                            self.height - int(round(self.percent_change(step) * self.height))
                        ))
            case _:
                if increase:
                    return Size((
                        self.width + step,
                        self.height + step
                    ))
                else:
                    return Size((
                        self.width - step,
                        self.height - step,
                    ))

    def scale(self, scale: float):
        return Size((
            round(self.width * scale),
            round(self.height * scale)
        ))

    def __str__(self):
        return f"({self.width},{self.height})"
    
    def __eq__(self, other):
        return self.width == other.width and self.height == other.height

    def __ne__(self, other):
        return self.width != other.width or self.height != other.height
        
    def __gt__(self, other):
        return self.width > other.width or self.height > other.height

    def __ge__(self, other):
        return self.width >= other.width or self.height >= other.height        
    
    def __lt__(self, other):
        return self.width < other.width or self.height < other.height

    def __le__(self, other):
        return self.width <= other.width or self.height <= other.height        
    
    @staticmethod
    def to_native(size):
        return native_to_size(size.width, size.height)

    @staticmethod
    def from_native(native_size):
        return Size((native_size['width'], native_size['height']))
    
    @staticmethod
    def from_native_box(native_box):
        return Size((native_box['right'] - native_box['left'], native_box['lower'] - native_box['upper']))


    
class BoxCoordinates:
    # see definition of 'box': https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.paste

    left: int
    upper: int
    right: int
    lower: int
    def __init__(self, position: Position, size: Size) -> None:
        self.left = position.left
        self.upper = position.upper
        self.right = self.left + size.width
        self.lower = self.upper + size.height
    
    @property
    def tuple(self) -> tuple[int, int, int, int]:
        return (self.left, self.upper, self.right, self.lower)
    
    @property
    def position(self) -> Position:
        return Position((self.left, self.upper))
    
    @property
    def upper_left(self) -> Point:
        return Point((self.left, self.upper))
    
    @property
    def lower_right(self) -> Point:
        return Point((self.right, self.lower))
    
    @property
    def size(self) -> Size:
        return Size((self.right - self.left, self.lower - self.upper))
    
    @property
    def area(self) -> int:
        return self.size.area
    
    def scale(self, scale: float):
        return BoxCoordinates(
            self.position.scale(scale),
            self.size.scale(scale)
        )
    
    def __eq__(self, other):
        return self.left == other.left and self.upper == other.upper and self.right == other.right and self.lower == other.lower

    def __hash__(self):
        return hash(self.tuple)    
    
    def __str__(self):
        return f"({self.left},{self.upper},{self.right},{self.lower})"

    def add_margin(self, margin: int):
        padding: int = margin //2
        return BoxCoordinates(
            self.position.adjust(-padding),
            self.size.adjust(padding, False)
        )
    
    def remove_margin(self, margin: int):
        padding: int = margin //2
        return BoxCoordinates(
            self.position.adjust(padding),
            self.size.adjust(-padding, False)
        )

    @staticmethod
    def to_native(box):
        return native_to_box(Position.to_native(box.position), Size.to_native(box.size))
    
    @staticmethod
    def from_native(native_box):
        return BoxCoordinates(Position.from_native_box(native_box), Size.from_native_box(native_box))
    
    @staticmethod
    def from_points(upper_left: Point, lower_right: Point):
        return BoxCoordinates(
            Position(upper_left.tuple),
            Size((lower_right.width(upper_left), lower_right.height(upper_left)))
        )
