from imagecloud.console_logger import ConsoleLogger
from imagecloud.weighted_image import (
    BoxCoordinates,
    NamedImage,
    scale_tuple
)
from imagecloud.imagecloud_defaults import MODE_TYPES
from imagecloud.imagecloud_helpers import to_unused_filepath
from imagecloud.integral_occupancy_map import (
    IntegralOccupancyMap,
    OccupancyMapType, 
    OccupancyMapDataType
)
import numpy as np
import os
from PIL import Image, ImageFilter
from typing import Any, Dict
import csv
import traceback

def is_empty(value: str | None) -> bool:
    return value in ['', None]
  
class LayoutCanvas:
    def __init__(
        self,
        size: tuple[int, int],
        mode: str,
        background_color: str | None,
        occupancy_map: OccupancyMapType | None,
        name: str | None = None
    ) -> None:
        self._name = name if name else 'imagecloud'
        self._size = size
        self._mode = mode
        self._background_color = background_color
        self._occupancy_map: OccupancyMapType = occupancy_map if occupancy_map is not None else np.zeros(size, dtype=OccupancyMapDataType)
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def size(self) -> tuple[int, int]:
        return self._size

    @property
    def mode(self) -> str:
        return self._mode
    
    @property
    def background_color(self) -> str | None:
        return self._background_color
    
    @property
    def occupancy_map(self) -> OccupancyMapType:
        return self._occupancy_map
    
    def to_image(self, scale: float = 1.0) -> NamedImage:
        image = Image.new(
            self.mode, (
                round(self.size[0] * scale),
                round(self.size[1] * scale)
            ),
            self.background_color
        )
        return NamedImage(image, self.name)
    
    def write(self, layout_directory: str) -> Dict[str,Any]:
        occupancy_csv_filepath = to_unused_filepath(os.path.join(layout_directory, 'layout_canvas_occupancy_map.csv'))
        np.savetxt(
            fname=occupancy_csv_filepath,
            X=self._occupancy_map,
            fmt='%d',
            delimiter=','
        )
        return {
            LAYOUT_CANVAS_NAME: self.name,
            LAYOUT_CANVAS_MODE: self.mode,
            LAYOUT_CANVAS_BACKGROUND_COLOR: self.background_color if self.background_color is not None else '',
            LAYOUT_CANVAS_SIZE_WIDTH: self.size[0],
            LAYOUT_CANVAS_SIZE_HEIGHT: self.size[1],
            LAYOUT_CANVAS_OCCUPANCY_MAP_FILEPATH: occupancy_csv_filepath
        }

    @staticmethod
    def empty_csv_data() -> Dict[str,Any]:
        return { header:'' for header in LAYOUT_CANVAS_HEADERS }

    @staticmethod
    def load(row: Dict[str,Any], _row_no: int):
        if all([is_empty(row[header])  for header in LAYOUT_CANVAS_HEADERS]): 
            return None
        
        return LayoutCanvas(
            (int(row[LAYOUT_CANVAS_SIZE_WIDTH]), int(row[LAYOUT_CANVAS_SIZE_HEIGHT])),
            row[LAYOUT_CANVAS_MODE],
            row[LAYOUT_CANVAS_BACKGROUND_COLOR] if not(is_empty(row[LAYOUT_CANVAS_BACKGROUND_COLOR])) else None,
            np.loadtxt(
                fname=row[LAYOUT_CANVAS_OCCUPANCY_MAP_FILEPATH],
                dtype=OccupancyMapDataType,
                delimiter=','
            ) if not(is_empty(row[LAYOUT_CANVAS_OCCUPANCY_MAP_FILEPATH])) else None,
            row[LAYOUT_CANVAS_NAME] if not(is_empty(row[LAYOUT_CANVAS_NAME])) else None
        )

class LayoutContour:
    
    def __init__(
        self,
        mask: np.ndarray | None,
        width: float,
        color: str
    ) -> None:
        self._mask = mask
        self._width = width
        self._color = color
    
    @property
    def mask(self) -> np.ndarray | None:
        return self._mask
    
    @property
    def width(self) -> float:
        return self._width
    
    @property
    def color(self) -> str:
        return self._color
    
    def to_image(self, image: NamedImage) -> NamedImage:
        if self.mask == None or self.width == 0:
            return image
        
        contour = Image.fromarray(self.mask.astype(np.uint8))
        contour = contour.resize(image.image.size)
        contour = contour.filter(ImageFilter.FIND_EDGES)
        contour = np.array(contour)

        # make sure borders are not drawn before changing width
        contour[[0, -1], :] = 0
        contour[:, [0, -1]] = 0

        # use gaussian to change width, divide by 10 to give more resolution
        radius = self.width / 10
        contour = Image.fromarray(contour)
        contour = contour.filter(ImageFilter.GaussianBlur(radius=radius))
        contour = np.array(contour) > 0
        contour = np.dstack((contour, contour, contour))

        # color the contour
        ret = np.array(image.image) * np.invert(contour)
        if self.color != 'black':
            color = Image.new(image.image.mode, image.image.size, self.color)
            ret += np.array(color) * contour

        return NamedImage(
            Image.fromarray(ret),
            image.name
        )

    def write(self, layout_directory: str) -> Dict[str,Any]:
        mask_filepath = ''
        if self.mask is not None:
            mask_filepath = to_unused_filepath(os.path.join(layout_directory, 'layout_contour_mask.png'))
            Image.fromarray(self.mask).save(mask_filepath)

        return {     
            LAYOUT_CONTOUR_MASK_IMAGE_FILEPATH: mask_filepath,
            LAYOUT_CONTOUR_WIDTH: self.width,
            LAYOUT_CONTOUR_COLOR: self.color
        }

    @staticmethod
    def empty_csv_data() -> Dict[str,Any]:
        return { header:'' for header in LAYOUT_CONTOUR_HEADERS }

    @staticmethod
    def load(row: Dict[str,Any], _row_no: int):
        if all([is_empty(row[header])  for header in LAYOUT_CONTOUR_HEADERS]): 
            return None

        return LayoutContour(
            np.array(NamedImage.load(row[LAYOUT_CONTOUR_MASK_IMAGE_FILEPATH]).image) if not(is_empty(row[LAYOUT_CONTOUR_MASK_IMAGE_FILEPATH])) else None,
            float(row[LAYOUT_CONTOUR_WIDTH]),
            row[LAYOUT_CONTOUR_COLOR]
        )
        
        

class LayoutItem:
    def __init__(
        self,
        original_image: NamedImage,
        size: tuple[int, int],
        position: tuple[int, int],
        orientation: Image.Transpose | None,
        reservation_no: int,
    ) -> None:
        self._original_image = original_image
        self._size = size
        self._position = position
        self._orientation = orientation
        self._reservation_no = reservation_no
    
    @property
    def original_image(self) -> NamedImage:
        return self._original_image
    
    @property
    def size(self) -> tuple[int, int]:
        return self._size
    
    @property
    def position(self) -> tuple[int, int]:
        return self._position
    
    @property
    def orientation(self) -> Image.Transpose | None:
        return self._orientation

    @property
    def reservation_no(self) -> int:
        return self._reservation_no
    
    def reservation_box(
        self, 
        scale: float = 1.0
    ) -> tuple[int, int, int, int]:
        left = round(self.position[0] * scale)
        upper = round(self.position[1] * scale)
        right = left + round(self.size[0] * scale)
        lower = upper - round(self.size[1] * scale)
        return (
            round(self.position[0] * scale),
            round(self.position[0] * scale)
        )
    def to_image(
        self,
        scale: float = 1.0,
        logger: ConsoleLogger | None = None
    ) -> NamedImage:
        new_image = self.original_image.image

        if self.orientation:
            if logger:
                logger.info('Transposing {0} {1}'.format(self.original_image.name, self.orientation.name))
            new_image = new_image.transpose(self.orientation)
        
        new_size = (
            round(self.size[0] * scale),
            round(self.size[1] * scale)
        )
        if new_image.size != new_size:
            if logger:
                logger.info('Resizing {0} ({1},{2}) -> ({3},{4})'.format(
                    self.original_image.name,
                    new_image.size[0], new_image.size[1],
                    new_size[0], new_size[1]
                ))
            new_image = new_image.resize(new_size)

        return NamedImage(new_image, self.original_image.name)

    def write(self, layout_directory: str) -> Dict[str,Any]:
        image_filepath = to_unused_filepath(os.path.join(layout_directory, '{0}.png'.format(self.original_image.name)))
        self.original_image.image.save(image_filepath)
        
        return {
            LAYOUT_ITEM_IMAGE_FILEPATH: image_filepath,
            LAYOUT_ITEM_SIZE_WIDTH: self.size[0],
            LAYOUT_ITEM_SIZE_HEIGHT: self.size[1],
            LAYOUT_ITEM_POSITION_X: self.position[0],
            LAYOUT_ITEM_POSITION_Y: self.position[1],
            LAYOUT_ITEM_ORIENTATION: self.orientation.name if self.orientation is not None else '',
            LAYOUT_ITEM_RESERVATION_NO: self.reservation_no
        }

    @staticmethod
    def empty_csv_data() -> Dict[str,Any]:
        return { header:'' for header in LAYOUT_ITEM_HEADERS }

    @staticmethod
    def load(row: Dict[str,Any], row_no: int):
        if all([is_empty(row[header])  for header in LAYOUT_ITEM_HEADERS]): 
            return None

        return LayoutItem(
            NamedImage.load(row[LAYOUT_ITEM_IMAGE_FILEPATH]),
            (int(row[LAYOUT_ITEM_SIZE_WIDTH]), int(row[LAYOUT_ITEM_SIZE_HEIGHT])),
            (int(row[LAYOUT_ITEM_POSITION_X]), int(row[LAYOUT_ITEM_POSITION_Y])),
            Image.Transpose[row[LAYOUT_ITEM_ORIENTATION]] if not(is_empty(row[LAYOUT_ITEM_ORIENTATION])) else None,
            int(row[LAYOUT_ITEM_RESERVATION_NO]) if not(is_empty(row[LAYOUT_ITEM_RESERVATION_NO])) else row_no
        )

class Layout:
    def __init__(
        self,
        canvas: LayoutCanvas,
        contour: LayoutContour,
        items: list[LayoutItem]
    ) -> None:
        self._canvas = canvas
        self._contour = contour
        self._items = items
    
    @property
    def canvas(self) -> LayoutCanvas:
        return self._canvas
    
    @property
    def contour(self) -> LayoutContour:
        return self._contour

    @property
    def items(self) -> list[LayoutItem]:
        return self._items
    
    def reconstruct_occupancy_map(self) -> OccupancyMapType:
        return IntegralOccupancyMap.create_occupancy_map(
            self.canvas.size,
            [(item.position, item.size) for item in self.items]
        )
    
    def to_image(
        self,
        scale: float = 1.0,
        logger: ConsoleLogger | None = None
    ) -> NamedImage:
        canvas = self.canvas.to_image(scale)

        total = len(self.items)
        if logger:
            logger.info('pasting {0} images into imagecloud canvas'.format(total))

        for i in range(total):
            item = self.items[i]
            if logger:
                logger.info('pasting Image[{0}/{1}] {2} into imagecloud canvas'.format(i + 1, total, item.original_image.name))            
            image = item.to_image(scale, logger)
            box = BoxCoordinates(scale_tuple(item.position, scale), scale_tuple(item.size, scale))
            try:
                canvas.image.paste(
                    im=image.image,
                    box=box.tuple
                )
            except Exception as e:
                if logger:
                    logger.info('Error pasting {0} into {1}. {2} \n{3}'.format(image.name, canvas.name, str(e), '\n'.join(traceback.format_exception(e))))

        return self.contour.to_image(canvas)

    def write(self, csv_filepath: str) -> None:
        layout_directory = os.path.dirname(csv_filepath)
        with open(csv_filepath, 'w') as file:
            csv_writer = csv.DictWriter(file, fieldnames=LAYOUT_CSV_HEADERS)
            csv_writer.writeheader()
            for i in range(len(self.items)):
                csv_writer.writerow({
                    **(self.canvas.write(layout_directory) if i == 0 else LayoutCanvas.empty_csv_data()),
                    **(self.contour.write(layout_directory) if i == 0 else LayoutContour.empty_csv_data()),
                    **(self.items[i].write(layout_directory))
                })
                

    @staticmethod
    def load(csv_filepath: str):
        canvas: LayoutCanvas | None = None
        items: list[LayoutItem] = list()
        contour: LayoutContour | None = None

        with open(csv_filepath, 'r') as file:    
            csv_reader = csv.DictReader(file, fieldnames=LAYOUT_CSV_HEADERS)
            next(csv_reader)
            row_no = 0
            for row in csv_reader:
                row_no += 1
                if canvas == None:
                    canvas = LayoutCanvas.load(row, row_no)
                if contour == None:
                    contour = LayoutContour.load(row, row_no)
                items.append(LayoutItem.load(row, row_no))
        
        if canvas == None or contour == None or 0 == len(items):
            return None
        return Layout(canvas, contour, items)

LAYOUT_CANVAS_SIZE_WIDTH = 'layout_canvas_size_width'
LAYOUT_CANVAS_SIZE_WIDTH_HELP = '<width>'
LAYOUT_CANVAS_SIZE_HEIGHT = 'layout_canvas_size_height'
LAYOUT_CANVAS_SIZE_HEIGHT_HELP = '<height>'
LAYOUT_CANVAS_MODE = 'layout_canvas_mode'
LAYOUT_CANVAS_MODE_HELP = '|'.join(MODE_TYPES)
LAYOUT_CANVAS_BACKGROUND_COLOR = 'layout_canvas_background_color'
LAYOUT_CANVAS_BACKGROUND_COLOR_HELP = '<empty>|<any-color-name>'
LAYOUT_CANVAS_NAME = 'layout_canvas_name'
LAYOUT_CANVAS_NAME_HELP = '<name>'
LAYOUT_CANVAS_OCCUPANCY_MAP_FILEPATH = 'layout_canvas_occupancy_map_csv_filepath'
LAYOUT_CANVAS_OCCUPANCY_MAP_FILEPATH_HELP = '<csv-filepath-of-occupancy_map>'
LAYOUT_CANVAS_HEADERS = [
    LAYOUT_CANVAS_NAME,
    LAYOUT_CANVAS_MODE,
    LAYOUT_CANVAS_BACKGROUND_COLOR,
    LAYOUT_CANVAS_SIZE_WIDTH,
    LAYOUT_CANVAS_SIZE_HEIGHT,
    LAYOUT_CANVAS_OCCUPANCY_MAP_FILEPATH
]
LAYOUT_CANVAS_HEADER_HELP = [
    LAYOUT_CANVAS_NAME_HELP,
    LAYOUT_CANVAS_MODE_HELP,
    LAYOUT_CANVAS_BACKGROUND_COLOR_HELP,
    LAYOUT_CANVAS_SIZE_WIDTH_HELP,
    LAYOUT_CANVAS_SIZE_HEIGHT_HELP,
    LAYOUT_CANVAS_OCCUPANCY_MAP_FILEPATH_HELP
]

LAYOUT_CONTOUR_MASK_IMAGE_FILEPATH = 'layout_contour_mask_image_filepath'
LAYOUT_CONTOUR_MASK_IMAGE_FILEPATH_HELP = '<empty>|<filepath-of-image-used-as-mask>'
LAYOUT_CONTOUR_WIDTH = 'layout_contour_width'
LAYOUT_CONTOUR_WIDTH_HELP = '<float>'
LAYOUT_CONTOUR_COLOR = 'layout_contour_color'
LAYOUT_CONTOUR_COLOR_HELP = '<any-color-name>'
LAYOUT_CONTOUR_HEADERS = [
    LAYOUT_CONTOUR_MASK_IMAGE_FILEPATH,
    LAYOUT_CONTOUR_WIDTH,
    LAYOUT_CONTOUR_COLOR
]
LAYOUT_CONTOUR_HEADER_HELP = [
    LAYOUT_CONTOUR_MASK_IMAGE_FILEPATH_HELP,
    LAYOUT_CONTOUR_WIDTH_HELP,
    LAYOUT_CONTOUR_COLOR_HELP
]

LAYOUT_ITEM_IMAGE_FILEPATH = 'layout_item_image_filepath'
LAYOUT_ITEM_IMAGE_FILEPATH_HELP = '<filepath-of-image-to-paste>'
LAYOUT_ITEM_SIZE_WIDTH = 'layout_item_size_width'
LAYOUT_ITEM_SIZE_WIDTH_HELP = '<width>'
LAYOUT_ITEM_SIZE_HEIGHT = 'layout_item_size_height'
LAYOUT_ITEM_SIZE_HEIGHT_HELP = '<height>'
LAYOUT_ITEM_POSITION_X = 'layout_item_position_x'
LAYOUT_ITEM_POSITION_X_HELP = '<x>'
LAYOUT_ITEM_POSITION_Y = 'layout_item_position_y'
LAYOUT_ITEM_POSITION_Y_HELP = '<y>'
LAYOUT_ITEM_ORIENTATION = 'layout_item_orientation'
LAYOUT_ITEM_ORIENTATION_HELP = '<empty>|FLIP_LEFT_RIGHT|FLIP_TOP_BOTTOM|ROTATE_90|ROTATE_180|ROTATE_270|TRANSPOSE|TRANSVERSE'
LAYOUT_ITEM_RESERVATION_NO = 'layout_item_reservation_no'
LAYOUT_ITEM_RESERVATION_NO_HELP = '<empty>|<reservation_no_in_occupancy_map>'
LAYOUT_ITEM_HEADERS = [
    LAYOUT_ITEM_IMAGE_FILEPATH,
    LAYOUT_ITEM_SIZE_WIDTH,
    LAYOUT_ITEM_SIZE_HEIGHT,
    LAYOUT_ITEM_POSITION_X,
    LAYOUT_ITEM_POSITION_Y,
    LAYOUT_ITEM_ORIENTATION,
    LAYOUT_ITEM_RESERVATION_NO
]
LAYOUT_ITEM_HEADER_HELP = [
    LAYOUT_ITEM_IMAGE_FILEPATH_HELP,
    LAYOUT_ITEM_SIZE_WIDTH_HELP,
    LAYOUT_ITEM_SIZE_HEIGHT_HELP,
    LAYOUT_ITEM_POSITION_X_HELP,
    LAYOUT_ITEM_POSITION_Y_HELP,
    LAYOUT_ITEM_ORIENTATION_HELP,
    LAYOUT_ITEM_RESERVATION_NO_HELP
]

LAYOUT_CSV_HEADERS = [
    *LAYOUT_CANVAS_HEADERS,
    *LAYOUT_CONTOUR_HEADERS,
    *LAYOUT_ITEM_HEADERS,
]
LAYOUT_CSV_HEADER_HELP = [
    *LAYOUT_CANVAS_HEADER_HELP,
    *LAYOUT_CONTOUR_HEADER_HELP,
    *LAYOUT_ITEM_HEADER_HELP,
]

LAYOUT_CSV_FILE_HELP = '''csv file representing 1 Layout Contour, 1 Layout Canvas and N Layout Items:
"{0}"
{1}
'''.format(
    '","'.join(LAYOUT_CSV_HEADERS),
    ','.join(LAYOUT_CSV_HEADER_HELP)
)