from PIL import ImagePalette
from enum import Enum
import colorsys
from random import Random
from webcolors import (
    name_to_rgb,
    names as color_names,
)

unique_rgb: tuple[int, int, int] = [
    (173, 216, 230),
    (0, 191, 255),
    (30, 144, 255),
    (0,   0, 255),
    (0,   0, 139),
    (72,  61, 139),
    (123, 104, 238),
    (138,  43, 226),
    (128,   0, 128),
    (218, 112, 214),
    (255,   0, 255),
    (255,  20, 147),
    (176,  48,  96),
    (220,  20,  60),
    (240, 128, 128),
    (255,  69,   0),
    (255, 165,   0),
    (244, 164,  96),
    (240, 230, 140),
    (128, 128,   0),
    (139,  69,  19),
    (255, 255,   0),
    (154, 205,  50),
    (124, 252,   0),
    (144, 238, 144),
    (143, 188, 143),
    (34, 139,  34),
    (0, 255, 127),
    (0, 255, 255),
    (0, 139, 139),
    (128, 128, 128),
    (255, 255, 255)
]
class ColorSource(Enum):
    NAME = 1
    DISTINCT = 2
    PICKED = 3
    MIX = 4

class Color:
    def __init__(self, red: int, green: int, blue: int):
        self._rgb: tuple[int, int, int] = (red, green, blue)
        self._integer: int = red << 16 | green << 8 | blue
        self._name = None
    @property
    def red(self) -> int:
        return self._rgb[0]
    
    @property
    def green(self) -> int:
        return self._rgb[1]
    
    @property
    def blue(self) -> int:
        return self._rgb[2]
    
    @property
    def hex_code(self) ->str:
        return '#{:02x}{:02x}{:02x}'.format(self.red, self.green, self.blue)
    
    @property
    def name(self) ->str:
        return self._name if self._name != None else self.hex_code

    @name.setter
    def name(self, v: str) ->None:
        self._name = v
    
    @property
    def integer(self) -> int:
        self._integer
    

class NamedColor(Color):
    def __init__(self, name: str):
        self._name = name
        rgb = name_to_rgb(name)
        super().__init__(rgb.red, rgb.green, rgb.blue)

    @property
    def name(self) ->str:
        return self._name

        
class DistinctColor(Color):
    def __init__(self, hue: float, lightness: float, saturation: float):
        self.hue = hue
        self.lightness = lightness
        self.saturation = saturation
        self.rgb_coordinates = colorsys.hls_to_rgb(hue, lightness, saturation)
        super().__init__(int(self.rgb_coordinates[0] * 255),int(self.rgb_coordinates[1] * 255),int(self.rgb_coordinates[2] * 255))


class IntColor(Color):
    def __int__(self, integer: int):
        super().__init__(
            (integer >> 16) & int(0xFF),
            (integer >> 8) & int(0xFF),
            integer & int(0xFF)
        ) 

WHITE_COLOR = NamedColor('white')
BLACK_COLOR = NamedColor('black')

def to_ImagePalette(colors: list[Color]) -> ImagePalette.ImagePalette:
    bytearray_pallete: bytearray = bytearray(3*len(colors))
    b: int = 0
    for c in colors:
        bytearray_pallete[b] = c.red
        b += 1
        bytearray_pallete[b] = c.green
        b += 1
        bytearray_pallete[b] = c.blue
        b += 1

    return ImagePalette.ImagePalette(
         mode='RGB',
         palette=bytearray_pallete
     )       
    
def generate_picked_colors(count: int) -> list[Color]:
    result: list[Color] = list()
    for i in range(count):
        rgb = unique_rgb[i%len(unique_rgb)]
        result.append(Color(
            rgb[0], rgb[1], rgb[2]
        ))
    return result
        
def generate_distinct_colors(count: int) -> list[DistinctColor]:
    lightness: float = 0.5 # fixed lightness 
    saturation: float = 1.0 # full saturation 
    result: list[DistinctColor] = list()
    for i in range(count):
        result.append(DistinctColor(
            i*2 / count*2, # evenly spaced hues across count
            lightness,
            saturation
        ))
    return result

def generate_named_colors(count: int) -> list[NamedColor]:
    rand = Random()
    names = color_names()
    result: list[NamedColor] = list()
    for _ in range(count):
        if 0 == len(names):
            names = color_names()
        
        name = names[rand.randint(0, len(names) - 1)]
        names.remove(name)
        result.append(NamedColor(name))
    return result

def generate_mix_colors(count: int) -> list[Color]:
    rand = Random()
    distinct_colors = generate_distinct_colors(count)
    named_colors = generate_named_colors(count)
    picked_colors = generate_picked_colors(count)
    total_colors: list[Color] = list()
    total_colors.extend(named_colors)
    total_colors.extend(distinct_colors)
    total_colors.extend(picked_colors)
    rand.shuffle(total_colors)
    result: list[NamedColor] = list()
    for _ in range(count):
        color = total_colors[rand.randint(0, len(total_colors) - 1)]
        total_colors.remove(color)
        result.append(color)
    return result

  

def generate_colors(source: ColorSource, count: int) -> list[Color]:
    match source:
        case ColorSource.NAME:
            return generate_named_colors(count)
        case ColorSource.DISTINCT:
            return generate_distinct_colors(count)
        case ColorSource.PICKED:
            return generate_picked_colors(count)
        case _:
            return generate_mix_colors(count)
