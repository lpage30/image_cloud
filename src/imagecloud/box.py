from imagecloud.size import Size
from imagecloud.native.box import native_create_box

class Box:
    left: int
    upper: int
    right: int
    lower: int
    size: Size
    
    def __init__(self, left: int, upper: int, right: int, lower: int) -> None:
        self.left = left
        self.upper = upper
        self.right = right
        self.lower = lower
        self.size = Size(right - left, lower - upper)
    
    @property
    def width(self) -> int:
        return self.size.width
    @property
    def height(self) -> int:
        return self.size.height
    # see definition of 'box': https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.paste

    @property
    def image_tuple(self) -> tuple[int, int, int, int]:
        return (self.left, self.upper, self.right, self.lower)
    
    @property
    def area(self) -> int:
        return self.size.area
    
    def scale(self, scale: float):
        return Box(
            int(round(self.left * scale)),
            int(round(self.upper * scale)),
            int(round(self.right * scale)),
            int(round(self.lower * scale))
        )
    def equals(self, other) -> bool:
        return (
            self.left == other.left and
            self.upper == other.upper and
            self.right == other.right and
            self.lower == other.lower
        )
    def contains(self, other) -> bool:
        return (self.left <= other.left and self.upper <= other.upper and 
            self.right >= other.right and self.lower >= other.lower)

    def box_to_string(self) -> str:
        return f'Box({self.left}, {self.upper}, {self.right}, {self.lower})'
    
    def remove_margin(self, margin: int):
        padding = int(round(margin/2))
        return Box(
            self.left + padding,
            self.upper + padding,
            self.right - padding,
            self.lower - padding
        )
    def to_native(self):
        return native_create_box(
            self.left,
            self.upper,
            self.right,
            self.lower
        )
    
    @staticmethod
    def from_native(native_box):
        return Box(
            native_box['left'],
            native_box['upper'],
            native_box['right'],
            native_box['lower']
        )
