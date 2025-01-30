from PIL import Image
import imagecloud.native_integral_occupancy_functions as native
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
    
    @property
    def native(self):
        return native.to_position(self.left, self.upper)
    
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
    def native(self):
        return native.to_size(self.width, self.height)
    
    @property
    def area(self) -> int:
        return round(self.width * self.height)

    def transpose(self, transpose: Image.Transpose):
        if transpose in [Image.Transpose.ROTATE_90, Image.Transpose.ROTATE_270]:
            return Size((self.height, self.width))
        return Size((self.width, self.height))

    def untranspose(self, transpose: Image.Transpose):
        if transpose in [Image.Transpose.ROTATE_90, Image.Transpose.ROTATE_270]:
            return Size((self.height, self.width))
        return Size((self.width, self.height))

    def adjust(self, step: int, maintain_aspect_ratio: bool):
        increase: bool = 0 <= step
        step = abs(step)
        if maintain_aspect_ratio:
            percent_change = step / self.width
            step_size = (
                round(percent_change * self.width),
                round(percent_change * self.height)
            )
        else:
            step_size = (
                step,
                step
            )
        if increase:
            return Size(((self.width + step_size[0]), (self.height + step_size[1])))
        else:
            return Size(((self.width - step_size[0]), (self.height - step_size[1])))
    
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

    @property
    def native(self):
        return native.to_box(self.position.native, self.size.native)
    
    @staticmethod
    def from_native(native_box):
        return BoxCoordinates(Position.from_native_box(native_box), Size.from_native_box(native_box))
    
    @staticmethod
    def from_points(upper_left: Point, lower_right: Point):
        return BoxCoordinates(
            Position(upper_left.tuple),
            Size((lower_right.width(upper_left), lower_right.height(upper_left)))
        )
