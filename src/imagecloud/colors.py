from PIL import ImagePalette
from enum import Enum
import colorsys
from random import Random
from webcolors import (
    name_to_rgb,
    rgb_to_name,
    names as color_names,
)

class ColorSource(Enum):
    NAME = 1
    DISTINCT = 2
    MIX = 3

class Color:
    def __init__(self, red: int, green: int, blue: int):
        self._rgb: tuple[int, int, int] = (red, green, blue)
        self._integer: int = red << 16 | green << 8 | blue
        try:
            self._name = rgb_to_name(self._rgb)
        except:
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
        
def generate_distinct_colors(count: int) -> list[DistinctColor]:
    lightness: float = 0.5 # fixed lightness 
    saturation: float = 1.0 # full saturation 
    result: list[DistinctColor] = list()
    for i in range(count):
        result.append(
            DistinctColor(
                i/count, # evenly spaced hues across count
                lightness,
                saturation
            )
        )
    return result

def generate_named_colors(count: int) -> list[NamedColor]:
    rand = Random()
    names = color_names()
    result: list[NamedColor] = list()
    for _ in range(count):
        if 0 == len(names):
            names = color_names()
        
        name = names[rand.randint(0, len(names))]
        names.remove(name)
        result.append(NamedColor(name))
    return result

def generate_mix_colors(count: int) -> list[Color]:
    rand = Random()
    total_colors: list[Color] = rand.shuffle([*generate_named_colors(count), *generate_distinct_colors(count)])
    result: list[NamedColor] = list()
    for _ in range(count):
        color = total_colors[rand.randint(0, len(total_colors))]
        total_colors.remove(color)
        result.append(color)
    return result
    

def generate_colors(source: ColorSource, count: int) -> list[Color]:
    match source:
        case ColorSource.NAME:
            return generate_named_colors(count)
        case ColorSource.DISTINCT:
            return generate_distinct_colors(count)
        case _:
            return generate_mix_colors(count)
    
 