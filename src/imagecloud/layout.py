from imagecloud.base_logger import BaseLogger
from imagecloud.image_wrappers import NamedImage
from imagecloud.size import (Size, ResizeType, RESIZE_TYPES)
from imagecloud.box import Box
from imagecloud.reservations import (
    Reservations,
    ReservationMapType, 
    ReservationMapDataType
)
import imagecloud.imagecloud_defaults as helper
from imagecloud.parsers import to_unused_filepath
import numpy as np
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import io
import os
from PIL import Image, ImageFilter
from typing import Any, Dict
import csv
import traceback
from imagecloud.colors import (
    Color,
    ColorSource,
    generate_colors,
    to_ImagePalette
)

def is_empty(value: str | None) -> bool:
    return value in ['', None]

def to_existing_filepath(original_filepath: str, possible_dirnames: list[str] | str) -> str:
    basename = os.path.basename(original_filepath)
    possible_dirnames = [os.path.dirname(original_filepath), *possible_dirnames]
    tried_filepaths: list[str] = list()
    for dirname in possible_dirnames:
        filepath = os.path.join(dirname, basename)
        if os.path.exists(filepath):
            return filepath
        tried_filepaths.append(filepath)
    
    raise ValueError('The file {0} does not exist! (Tried [{1}])'.format(original_filepath, ', '.join(tried_filepaths)))
    
    
  
class LayoutCanvas:
    def __init__(
        self,
        size: Size,
        mode: str,
        background_color: str | None,
        reservation_map: ReservationMapType | None,
        name: str | None = None
    ) -> None:
        self._name = name if name else 'imagecloud'
        self._size = size
        self._mode = mode
        self._background_color = background_color
        self._reservation_map: ReservationMapType = reservation_map if reservation_map is not None else np.zeros(size, dtype=ReservationMapDataType)
        self._reservation_colors = [*generate_colors(ColorSource.PICKED, self._reservation_map.max() + 1)]

    
    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, v: str) -> None:
        self._name = v
    
    @property
    def size(self) -> Size:
        return self._size

    @property
    def mode(self) -> str:
        return self._mode
    
    @property
    def background_color(self) -> str | None:
        return self._background_color
    
    @property
    def reservation_map(self) -> ReservationMapType:
        return self._reservation_map
    
    @property
    def reservation_colors(self) -> list[Color]:
        return self._reservation_colors
    
    def to_image(self, scale: float = 1.0) -> NamedImage:
        image = Image.new(
            self.mode, 
            self.size.scale(scale).image_tuple,
            self.background_color
        )
        return NamedImage(image, self.name)
    
    def to_reservation_image(self) -> NamedImage:
        image = Image.new(
            'P',
            (self.reservation_map.shape[0], self.reservation_map.shape[1])
        )
        image.putpalette(to_ImagePalette(self.reservation_colors))
        pixels = image.load()
        for x in range(self.reservation_map.shape[0]):
            for y in range(self.reservation_map.shape[1]):
                pixels[x, y] = int(self.reservation_map[x,y])
        
        return NamedImage(image, '{0}.reservation_map'.format(self.name))
    
    def write(self, layout_directory: str) -> Dict[str,Any]:
        reservation_map_csv_filepath = to_unused_filepath(layout_directory, '{0}.reservation_map'.format(self.name), 'csv')
        np.savetxt(
            fname=reservation_map_csv_filepath,
            X=self._reservation_map,
            fmt='%d',
            delimiter=','
        )
        return {
            LAYOUT_CANVAS_NAME: self.name,
            LAYOUT_CANVAS_MODE: self.mode,
            LAYOUT_CANVAS_BACKGROUND_COLOR: self.background_color if self.background_color is not None else '',
            LAYOUT_CANVAS_SIZE_WIDTH: self.size.width,
            LAYOUT_CANVAS_SIZE_HEIGHT: self.size.height,
            LAYOUT_CANVAS_RESERVATION_MAP_FILEPATH: reservation_map_csv_filepath
        }

    @staticmethod
    def empty_csv_data() -> Dict[str,Any]:
        return { header:'' for header in LAYOUT_CANVAS_HEADERS }

    @staticmethod
    def load(row: Dict[str,Any], _row_no: int, layout_directory: str):
        if all([is_empty(row[header])  for header in LAYOUT_CANVAS_HEADERS]): 
            return None
        
        return LayoutCanvas(
            Size(int(row[LAYOUT_CANVAS_SIZE_WIDTH]), int(row[LAYOUT_CANVAS_SIZE_HEIGHT])),
            row[LAYOUT_CANVAS_MODE],
            row[LAYOUT_CANVAS_BACKGROUND_COLOR] if not(is_empty(row[LAYOUT_CANVAS_BACKGROUND_COLOR])) else None,
            np.loadtxt(
                fname=to_existing_filepath(row[LAYOUT_CANVAS_RESERVATION_MAP_FILEPATH], layout_directory),
                dtype=ReservationMapDataType,
                delimiter=','
            ) if not(is_empty(row[LAYOUT_CANVAS_RESERVATION_MAP_FILEPATH])) else None,
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

    def write(self, layout_name: str, layout_directory: str) -> Dict[str,Any]:
        mask_filepath = ''
        if self.mask is not None:
            mask_filepath = to_unused_filepath(layout_directory, '{0}.contour_mask'.format(layout_name), 'png')
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
    def load(row: Dict[str,Any], _row_no: int, layout_directory: str):
        if all([is_empty(row[header])  for header in LAYOUT_CONTOUR_HEADERS]): 
            return None

        return LayoutContour(
            np.array(NamedImage.load(to_existing_filepath(row[LAYOUT_CONTOUR_MASK_IMAGE_FILEPATH], layout_directory)).image) if not(is_empty(row[LAYOUT_CONTOUR_MASK_IMAGE_FILEPATH])) else None,
            float(row[LAYOUT_CONTOUR_WIDTH]),
            row[LAYOUT_CONTOUR_COLOR]
        )
        
        

class LayoutItem:
    def __init__(
        self,
        image: NamedImage,
        placement_box: Box,
        orientation: Image.Transpose | None,
        reservation_box: Box,        
        reservation_no: int,
        latency_str: str = ''
    ) -> None:
        
        self._original_image = image.original_named_image
        self._placement_box = placement_box
        self._orientation = orientation
        self._reservation_box = reservation_box
        self._reservation_no = reservation_no
        self._reservation_color = None
        self._latency_str = latency_str
    
    @property
    def name(self) -> str:
        return self.original_image.name

    @property
    def original_image(self) -> NamedImage:
        return self._original_image
    
    @property
    def placement_box(self) -> Box:
        return self._placement_box
        
    @property
    def orientation(self) -> Image.Transpose | None:
        return self._orientation

    @property    
    def reservation_box(self) -> Box:
        return self._reservation_box

    @property
    def reservation_no(self) -> int:
        return self._reservation_no
    
    @property
    def reservation_color(self) -> Color | None:
        return self._reservation_color

    @reservation_color.setter 
    def reservation_color(self, color: Color) -> None:
        self._reservation_color = color

    def to_image(
        self,
        logger: BaseLogger,
        scale: float = 1.0
    ) -> NamedImage:
        new_image = self.original_image.image

        if self.orientation:
            logger.info('Transposing {0} {1}'.format(self.name, self.orientation.name))
            new_image = new_image.transpose(self.orientation)
        
        new_size = self.placement_box.size.scale(scale)
        if new_image.size != new_size.image_tuple:
            logger.info('Resizing {0} ({1},{2}) -> {3}'.format(
                self.original_image.name,
                new_image.size[0], new_image.size[1],
                new_size.size_to_string()
            ))
            new_image = new_image.resize(new_size.image_tuple)
        return NamedImage(new_image, self.original_image.name)

    def to_legend_handle(self) -> mpatches.Patch:
        return mpatches.Patch(
            color=self.reservation_color.hex_code,
            label=self.name
        )

    def write(self, layout_directory: str) -> Dict[str,Any]:
        image_filepath = to_unused_filepath(layout_directory, self.original_image.name, 'png')
        self.original_image.image.save(image_filepath, 'png')
        
        return {
            LAYOUT_ITEM_IMAGE_FILEPATH: image_filepath,
            LAYOUT_ITEM_POSITION_X: self.placement_box.left,
            LAYOUT_ITEM_POSITION_Y: self.placement_box.upper,
            LAYOUT_ITEM_SIZE_WIDTH: self.placement_box.width,
            LAYOUT_ITEM_SIZE_HEIGHT: self.placement_box.height,
            LAYOUT_ITEM_ORIENTATION: self.orientation.name if self.orientation is not None else '',
            LAYOUT_ITEM_RESERVATION_POSITION_X: self.reservation_box.left,
            LAYOUT_ITEM_RESERVATION_POSITION_Y: self.reservation_box.upper,
            LAYOUT_ITEM_RESERVATION_SIZE_WIDTH: self.reservation_box.width,
            LAYOUT_ITEM_RESERVATION_SIZE_HEIGHT: self.reservation_box.height,
            LAYOUT_ITEM_RESERVATION_NO: self.reservation_no,
            LAYOUT_ITEM_LATENCY: self._latency_str
        }

    @staticmethod
    def empty_csv_data() -> Dict[str,Any]:
        return { header:'' for header in LAYOUT_ITEM_HEADERS }

    @staticmethod
    def load(row: Dict[str,Any], row_no: int, layout_directory: str):
        if all([is_empty(row[header])  for header in LAYOUT_ITEM_HEADERS]): 
            return None

        placement_box = Box(
            int(row[LAYOUT_ITEM_POSITION_X]),
            int(row[LAYOUT_ITEM_POSITION_Y]),
            int(row[LAYOUT_ITEM_POSITION_X]) + int(row[LAYOUT_ITEM_SIZE_WIDTH]), 
            int(row[LAYOUT_ITEM_POSITION_Y]) + int(row[LAYOUT_ITEM_SIZE_HEIGHT])
        )
        reservation_box = placement_box
        reservation_headers = [
            LAYOUT_ITEM_RESERVATION_POSITION_X,
            LAYOUT_ITEM_RESERVATION_POSITION_Y,
            LAYOUT_ITEM_RESERVATION_SIZE_WIDTH,
            LAYOUT_ITEM_RESERVATION_SIZE_HEIGHT
        ]

        if all([header in row and not(is_empty(row[header])) for header in reservation_headers]):
            reservation_box = Box(
                int(row[LAYOUT_ITEM_RESERVATION_POSITION_X]),
                int(row[LAYOUT_ITEM_RESERVATION_POSITION_Y]),
                int(row[LAYOUT_ITEM_RESERVATION_POSITION_X]) + int(row[LAYOUT_ITEM_RESERVATION_SIZE_WIDTH]), 
                int(row[LAYOUT_ITEM_RESERVATION_POSITION_Y]) + int(row[LAYOUT_ITEM_RESERVATION_SIZE_HEIGHT])
            )
        
        return LayoutItem(
            NamedImage.load(to_existing_filepath(row[LAYOUT_ITEM_IMAGE_FILEPATH], layout_directory)),
            placement_box,
            Image.Transpose[row[LAYOUT_ITEM_ORIENTATION]] if not(is_empty(row[LAYOUT_ITEM_ORIENTATION])) else None,
            reservation_box,
            int(row[LAYOUT_ITEM_RESERVATION_NO]) if not(is_empty(row[LAYOUT_ITEM_RESERVATION_NO])) else row_no,
            row[LAYOUT_ITEM_LATENCY] if not(is_empty(row[LAYOUT_ITEM_LATENCY])) else ''
        )

class Layout:
    def __init__(
        self,
        canvas: LayoutCanvas,
        contour: LayoutContour,
        items: list[LayoutItem],
        max_images: int | None = None,
        min_image_size: Size | None = None,
        image_step: int | None = None,
        resize_type: ResizeType | None = None,
        scale: float | None = None,
        margin: int | None = None,
        name: str | None = None,
        total_threads: int | None = None,
        latency_str: str = ''
    ) -> None:
        self._name = name if name else 'imagecloud.layout'
        self._canvas = canvas
        self._contour = contour
        self._items = items
        for item in items:
            item.reservation_color = canvas.reservation_colors[item.reservation_no]
            
        self.max_images = max_images if max_images is not None else int(helper.DEFAULT_MAX_IMAGES)
        self.min_image_size = min_image_size if min_image_size is not None else int(helper.DEFAULT_MIN_IMAGE_SIZE)
        self.image_step = image_step if image_step is not None else int(helper.DEFAULT_STEP_SIZE)
        self.resize_type = resize_type if resize_type is not None else ResizeType[helper.DEFAULT_RESIZE_TYPE]
        self.scale = scale if scale is not None else int(helper.DEFAULT_SCALE)

        self.margin = margin if margin is not None else int(helper.DEFAULT_MARGIN)
        self.total_threads = total_threads if total_threads is not None else int(helper.DEFAULT_PARALLELISM)
        self._latency_str = latency_str
    
    @property
    def name(self) -> str:
        return self._name

    def set_names(self, layout: str, canvas: str) -> None:
        self._name = layout
        self.canvas.name = canvas
        
    @property
    def canvas(self) -> LayoutCanvas:
        return self._canvas
    
    @property
    def contour(self) -> LayoutContour:
        return self._contour

    @property
    def items(self) -> list[LayoutItem]:
        return self._items
    
    def reconstruct_reservation_map(self,logger: BaseLogger ) -> ReservationMapType:
        return Reservations.create_reservation_map(
            logger,
            self.canvas.size,
            [item.reservation_box for item in self.items]
        )
    
    def to_image(
        self,
        logger: BaseLogger,
        scale: float = 1.0
    ) -> NamedImage:
        logger.reset_context()
        canvas = self.canvas.to_image(scale)

        total = len(self.items)
        logger.info('pasting {0} images into imagecloud canvas'.format(total))

        for i in range(total):
            item: LayoutItem = self.items[i]
            logger.info('pasting Image[{0}/{1}] {2} into imagecloud canvas'.format(i + 1, total, item.original_image.name))            
            image = item.to_image(logger, scale)
            box = item.placement_box.scale(scale)
            try:
                canvas.image.paste(
                    im=image.image,
                    box=box.image_tuple
                )
            except Exception as e:
                logger.error('Error pasting {0} into {1}. {2} \n{3}'.format(image.name, canvas.name, str(e), '\n'.join(traceback.format_exception(e))))

        return self.contour.to_image(canvas)

    def to_reservation_chart_image(self) -> NamedImage:
        reservation_image: NamedImage = self.canvas.to_reservation_image()
        legend_handles: list[mpatches.Patch] = [
            mpatches.Patch(
                color=self.canvas.reservation_colors[0].hex_code,
                label='UNRESERVED'
            ),
            *[item.to_legend_handle() for item in self.items]
        ]
        plt.imshow(reservation_image.image)
        plt.legend(handles=legend_handles, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
        plt.axis('off')
        plt.grid(True)
        plt.tight_layout()        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image = Image.open(buf)
        image.load()
        result = NamedImage(
            image,
            reservation_image.name
        )
        buf.close()
        return result

    def write(self, csv_filepath: str) -> None:
        layout_directory = os.path.dirname(csv_filepath)
        layout_data = {
            LAYOUT_MAX_IMAGES: self.max_images,
            LAYOUT_MIN_IMAGE_SIZE_WIDTH: self.min_image_size.width,
            LAYOUT_MIN_IMAGE_SIZE_HEIGHT: self.min_image_size.height,
            LAYOUT_IMAGE_STEP: self.image_step,
            LAYOUT_RESIZE_TYPE: self.resize_type.name,
            LAYOUT_SCALE: self.scale,
            LAYOUT_MARGIN: self.margin,
            LAYOUT_NAME: self.name,
            LAYOUT_TOTAL_THREADS: self.total_threads,
            LAYOUT_LATENCY: self._latency_str
        }
        with open(csv_filepath, 'w') as file:
            csv_writer = csv.DictWriter(file, fieldnames=LAYOUT_CSV_HEADERS)
            csv_writer.writeheader()
            for i in range(len(self.items)):
                csv_writer.writerow({
                    **(layout_data if i == 0 else { header:'' for header in LAYOUT_HEADERS }),
                    **(self.canvas.write(layout_directory) if i == 0 else LayoutCanvas.empty_csv_data()),
                    **(self.contour.write(self.name, layout_directory) if i == 0 else LayoutContour.empty_csv_data()),
                    **(self.items[i].write(layout_directory))
                })
                
        
    @staticmethod
    def load(csv_filepath: str):
        try:
            canvas: LayoutCanvas | None = None
            items: list[LayoutItem] = list()
            contour: LayoutContour | None = None
            layout_directory: str = os.path.dirname(csv_filepath)
            layout_data = {}
            with open(csv_filepath, 'r') as file:    
                csv_reader = csv.DictReader(file, fieldnames=LAYOUT_CSV_HEADERS)
                next(csv_reader)
                row_no = 0
                for row in csv_reader:
                    row_no += 1
                    if not(all([header not in row or is_empty(row[header])  for header in LAYOUT_HEADERS])):
                        layout_data = {}
                        for header in LAYOUT_HEADERS:
                            if header in row and not is_empty(row[header]):
                                layout_data[header] = row[header]

                    if canvas == None:
                        canvas = LayoutCanvas.load(row, row_no, layout_directory)
                    if contour == None:
                        contour = LayoutContour.load(row, row_no, layout_directory)
                    items.append(LayoutItem.load(row, row_no, layout_directory))
            
            if canvas == None or contour == None or 0 == len(items):
                return None
            
            max_images = int(layout_data[LAYOUT_MAX_IMAGES]) if LAYOUT_MAX_IMAGES in layout_data else None
            min_image_size = Size(int(layout_data[LAYOUT_MIN_IMAGE_SIZE_WIDTH]), int(layout_data[LAYOUT_MIN_IMAGE_SIZE_HEIGHT])) if LAYOUT_MIN_IMAGE_SIZE_WIDTH in layout_data and LAYOUT_MIN_IMAGE_SIZE_HEIGHT in layout_data else None
            image_step = int(layout_data[LAYOUT_IMAGE_STEP]) if LAYOUT_IMAGE_STEP in layout_data else None
            resize_type = ResizeType[layout_data[LAYOUT_RESIZE_TYPE]] if LAYOUT_RESIZE_TYPE in layout_data else None
            scale = float(layout_data[LAYOUT_SCALE]) if LAYOUT_SCALE in layout_data else None
            margin = int(layout_data[LAYOUT_MARGIN]) if LAYOUT_MARGIN in layout_data else None
            name = layout_data[LAYOUT_NAME] if LAYOUT_NAME in layout_data else None  
            total_threads = int(layout_data[LAYOUT_TOTAL_THREADS]) if LAYOUT_TOTAL_THREADS in layout_data else None
            latency_str = layout_data[LAYOUT_LATENCY] if LAYOUT_LATENCY in layout_data else ''
            return Layout(
                canvas,
                contour,
                items,
                max_images,
                min_image_size,
                image_step,
                resize_type,
                scale,
                margin,
                name,
                total_threads,
                latency_str
            )
        except Exception as e:
            raise Exception(str(e))

LAYOUT_MAX_IMAGES = 'layout_max_images'
LAYOUT_MAX_IMAGES_HELP = '<integer>'
LAYOUT_MIN_IMAGE_SIZE_WIDTH = 'layout_min_image_size_width'
LAYOUT_MIN_IMAGE_SIZE_WIDTH_HELP = '<width>'
LAYOUT_MIN_IMAGE_SIZE_HEIGHT = 'layout_min_image_size_height'
LAYOUT_MIN_IMAGE_SIZE_HEIGHT_HELP = '<height>'
LAYOUT_IMAGE_STEP = 'layout_image_step'
LAYOUT_IMAGE_STEP_HELP = '<integer>'
LAYOUT_RESIZE_TYPE = 'layout_resize_type'
LAYOUT_RESIZE_TYPE_HELP = '|'.join(RESIZE_TYPES)
LAYOUT_SCALE = 'layout_scale'
LAYOUT_SCALE_HELP = '<float>'
LAYOUT_MARGIN = 'layout_margin'
LAYOUT_MARGIN_HELP = '<image-margin>'
LAYOUT_NAME = 'layout_name'
LAYOUT_NAME_HELP = '<name>'
LAYOUT_TOTAL_THREADS = 'layout_total_threads'
LAYOUT_TOTAL_THREADS_HELP = '<integer>'
LAYOUT_LATENCY = 'layout_latency'
LAYOUT_LATENCY_HELP = '<string>'
LAYOUT_HEADERS = [
    LAYOUT_MAX_IMAGES,
    LAYOUT_MIN_IMAGE_SIZE_WIDTH,
    LAYOUT_MIN_IMAGE_SIZE_HEIGHT,
    LAYOUT_IMAGE_STEP,
    LAYOUT_RESIZE_TYPE,
    LAYOUT_SCALE,
    LAYOUT_MARGIN,
    LAYOUT_NAME,
    LAYOUT_TOTAL_THREADS,
    LAYOUT_LATENCY
]
LAYOUT_HEADERS_HELP = [
    LAYOUT_MAX_IMAGES_HELP,
    LAYOUT_MIN_IMAGE_SIZE_WIDTH_HELP,
    LAYOUT_MIN_IMAGE_SIZE_HEIGHT_HELP,
    LAYOUT_IMAGE_STEP_HELP,
    LAYOUT_RESIZE_TYPE_HELP,
    LAYOUT_SCALE_HELP,
    LAYOUT_MARGIN_HELP,
    LAYOUT_NAME_HELP,
    LAYOUT_TOTAL_THREADS_HELP,
    LAYOUT_LATENCY_HELP
]
LAYOUT_CANVAS_SIZE_WIDTH = 'layout_canvas_size_width'
LAYOUT_CANVAS_SIZE_WIDTH_HELP = '<width>'
LAYOUT_CANVAS_SIZE_HEIGHT = 'layout_canvas_size_height'
LAYOUT_CANVAS_SIZE_HEIGHT_HELP = '<height>'
LAYOUT_CANVAS_MODE = 'layout_canvas_mode'
LAYOUT_CANVAS_MODE_HELP = '|'.join(helper.MODE_TYPES)
LAYOUT_CANVAS_BACKGROUND_COLOR = 'layout_canvas_background_color'
LAYOUT_CANVAS_BACKGROUND_COLOR_HELP = '<empty>|<any-color-name>'
LAYOUT_CANVAS_NAME = 'layout_canvas_name'
LAYOUT_CANVAS_NAME_HELP = '<name>'
LAYOUT_CANVAS_RESERVATION_MAP_FILEPATH = 'layout_canvas_reservation_map_csv_filepath'
LAYOUT_CANVAS_RESERVATION_MAP_FILEPATH_HELP = '<csv-filepath-of-reservation_map>'
LAYOUT_CANVAS_HEADERS = [
    LAYOUT_CANVAS_NAME,
    LAYOUT_CANVAS_MODE,
    LAYOUT_CANVAS_BACKGROUND_COLOR,
    LAYOUT_CANVAS_SIZE_WIDTH,
    LAYOUT_CANVAS_SIZE_HEIGHT,
    LAYOUT_CANVAS_RESERVATION_MAP_FILEPATH
]
LAYOUT_CANVAS_HEADER_HELP = [
    LAYOUT_CANVAS_NAME_HELP,
    LAYOUT_CANVAS_MODE_HELP,
    LAYOUT_CANVAS_BACKGROUND_COLOR_HELP,
    LAYOUT_CANVAS_SIZE_WIDTH_HELP,
    LAYOUT_CANVAS_SIZE_HEIGHT_HELP,
    LAYOUT_CANVAS_RESERVATION_MAP_FILEPATH_HELP
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
LAYOUT_ITEM_POSITION_X = 'layout_item_position_x'
LAYOUT_ITEM_POSITION_X_HELP = '<x>'
LAYOUT_ITEM_POSITION_Y = 'layout_item_position_y'
LAYOUT_ITEM_POSITION_Y_HELP = '<y>'
LAYOUT_ITEM_SIZE_WIDTH = 'layout_item_size_width'
LAYOUT_ITEM_SIZE_WIDTH_HELP = '<width>'
LAYOUT_ITEM_SIZE_HEIGHT = 'layout_item_size_height'
LAYOUT_ITEM_SIZE_HEIGHT_HELP = '<height>'
LAYOUT_ITEM_ORIENTATION = 'layout_item_orientation'
LAYOUT_ITEM_ORIENTATION_HELP = '<empty>|{0}'.format('|'.join([member.name for member in Image.Transpose]))
LAYOUT_ITEM_RESERVATION_POSITION_X = 'layout_item_reserved_position_x'
LAYOUT_ITEM_RESERVATION_POSITION_X_HELP = '<x>'
LAYOUT_ITEM_RESERVATION_POSITION_Y = 'layout_item_reserved_position_y'
LAYOUT_ITEM_RESERVATION_POSITION_Y_HELP = '<y>'
LAYOUT_ITEM_RESERVATION_SIZE_WIDTH = 'layout_item_reserved_size_width'
LAYOUT_ITEM_RESERVATION_SIZE_WIDTH_HELP = '<width>'
LAYOUT_ITEM_RESERVATION_SIZE_HEIGHT = 'layout_item_reserved_size_height'
LAYOUT_ITEM_RESERVATION_SIZE_HEIGHT_HELP = '<height>'
LAYOUT_ITEM_RESERVATION_NO = 'layout_item_reservation_no'
LAYOUT_ITEM_RESERVATION_NO_HELP = '<empty>|<reservation_no_in_reservation_map>'
LAYOUT_ITEM_LATENCY = 'layout_item_latency'
LAYOUT_ITEM_LATENCY_HELP = '<string>' 
LAYOUT_ITEM_HEADERS = [
    LAYOUT_ITEM_IMAGE_FILEPATH,
    LAYOUT_ITEM_POSITION_X,
    LAYOUT_ITEM_POSITION_Y,
    LAYOUT_ITEM_SIZE_WIDTH,
    LAYOUT_ITEM_SIZE_HEIGHT,
    LAYOUT_ITEM_ORIENTATION,
    LAYOUT_ITEM_RESERVATION_POSITION_X,
    LAYOUT_ITEM_RESERVATION_POSITION_Y,
    LAYOUT_ITEM_RESERVATION_SIZE_WIDTH,
    LAYOUT_ITEM_RESERVATION_SIZE_HEIGHT,
    LAYOUT_ITEM_RESERVATION_NO,
    LAYOUT_ITEM_LATENCY
]
LAYOUT_ITEM_HEADER_HELP = [
    LAYOUT_ITEM_IMAGE_FILEPATH_HELP,
    LAYOUT_ITEM_POSITION_X_HELP,
    LAYOUT_ITEM_POSITION_Y_HELP,
    LAYOUT_ITEM_SIZE_WIDTH_HELP,
    LAYOUT_ITEM_SIZE_HEIGHT_HELP,
    LAYOUT_ITEM_ORIENTATION_HELP,
    LAYOUT_ITEM_RESERVATION_POSITION_X_HELP,
    LAYOUT_ITEM_RESERVATION_POSITION_Y_HELP,
    LAYOUT_ITEM_RESERVATION_SIZE_WIDTH_HELP,
    LAYOUT_ITEM_RESERVATION_SIZE_HEIGHT_HELP,
    LAYOUT_ITEM_RESERVATION_NO_HELP,
    LAYOUT_ITEM_LATENCY_HELP
]

LAYOUT_CSV_HEADERS = [
    *LAYOUT_HEADERS,
    *LAYOUT_CANVAS_HEADERS,
    *LAYOUT_CONTOUR_HEADERS,
    *LAYOUT_ITEM_HEADERS,
]
LAYOUT_CSV_HEADER_HELP = [
    *LAYOUT_HEADERS_HELP,
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