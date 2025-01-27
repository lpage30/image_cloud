from imagecloud.console_logger import ConsoleLogger
import argparse
import sys
import os
import numpy as np

import imagecloud_clis.cli_helpers as cli_helpers
from imagecloud.imagecloud_defaults import (
    DEFAULT_IMAGE_FORMAT,
    DEFAULT_CLOUD_SIZE,
    DEFAULT_BACKGROUND_COLOR,
    DEFAULT_CONTOUR_COLOR,
    DEFAULT_CONTOUR_WIDTH,
    DEFAULT_MARGIN,
    DEFAULT_MAX_IMAGE_SIZE,
    DEFAULT_MIN_IMAGE_SIZE,
    DEFAULT_MODE,
    DEFAULT_PREFER_HORIZONTAL,
    DEFAULT_STEP_SIZE,
    DEFAULT_MAINTAIN_ASPECT_RATIO
)
from imagecloud.imagecloud_defaults import (
    IMAGE_FORMAT_HELP,
    MASK_HELP,
    CLOUD_SIZE_HELP,
    STEP_SIZE_HELP,
    MAINTAIN_ASPECT_RATIO_HELP,
    MAX_IMAGE_SIZE_HELP,
    MIN_IMAGE_SIZE_HELP,
    BACKGROUND_COLOR_HELP,
    CONTOUR_WIDTH_HELP,
    CONTOUR_COLOR_HELP,
    PREFER_HORIZONTAL_HELP,
    BACKGROUND_COLOR_HELP,
    MARGIN_HELP,
    MODE_HELP
)
from imagecloud.imagecloud_helpers import to_unused_filepath
from imagecloud.weighted_image import (
    WeightedImage,
    WEIGHTED_IMAGES_CSV_FILE_HELP,
    load_weighted_images,
)
from imagecloud.imagecloud_defaults import (
    IMAGE_FORMATS,
    MODE_TYPES
)
from imagecloud.imagecloud import (
    ImageCloud
)
DEFAULT_SHOW = True
DEFAULT_VERBOSE = False
DEFAULT_EXPAND_CLOUD_TO_FIT_ALL = False

class ImageCloudGenerateArguments:
    def __init__ (
        self, 
        input: str,
        output_image_filepath: str | None,
        output_layout_dirpath: str | None,
        output_image_format: str,
        max_image_size: tuple[int, int] | None,
        min_image_size: tuple[int, int],
        cloud_size: tuple[int, int],
        background_color: str,
        contour_width: int,
        contour_color: str,
        mask: str | None,
        step_size: int,
        maintain_aspect_ratio: bool,
        prefer_horizontal: float,
        margin: int,
        mode: str,
        show: bool,
        expand_cloud_to_fit_all: bool,
        logger: ConsoleLogger | None
    ) -> None:
        self.input = input
        self.output_image_filepath = output_image_filepath
        self.output_layout_dirpath = output_layout_dirpath
        self.output_image_format = output_image_format
        self.max_image_size = max_image_size
        self.min_image_size = min_image_size
        self.cloud_size = cloud_size
        self.background_color = background_color
        self.contour_width = contour_width
        self.contour_color = contour_color
        self.mask = mask
        self.step_size = step_size
        self.maintain_aspect_ratio = maintain_aspect_ratio
        self.prefer_horizontal = prefer_horizontal
        self.margin = margin
        self.mode = mode
        self.show = show
        self.expand_cloud_to_fit_all = expand_cloud_to_fit_all
        self.logger = logger
    
    @staticmethod
    def parse(arguments: list[str]):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            prog='generate_imagecloud',
            description='''
            Generate an \'ImageCloud\' from a csv file indicating image filepath and weight for image.
            '''
        )
        parser.add_argument(
            '-i', 
            '--input',
            metavar='<csv_filepath>',
            type=lambda fp: cli_helpers.existing_filepath(parser, fp),
            required=True,
            help='Required, {0}'.format(WEIGHTED_IMAGES_CSV_FILE_HELP)
        )
        parser.add_argument(
            '-output_image_filepath',
            metavar='<generated_image_cloud_image_filepath>',
            type=str,
            help='Optional, output file path for generated image cloud image'
        )
        parser.add_argument(
            '-output_layout_dirpath',
            metavar='<generated_image_cloud_layout_directory-path>',
            type=str,
            help='Optional, output directory path into which generated image cloud layout will be written'
        )
        parser.add_argument(
            '-output_image_format',
            default=DEFAULT_IMAGE_FORMAT,
            metavar='{0}'.format('|'.join(IMAGE_FORMATS)),
            type=lambda v: cli_helpers.is_one_of_array(parser, v, IMAGE_FORMATS),
            help='Optional,(default %(default)s) {0}'.format(IMAGE_FORMAT_HELP)
        )
        parser.add_argument(
            '-cloud_size',
            default=DEFAULT_CLOUD_SIZE,
            metavar='"<width>,<height>"',
            type= lambda v: cli_helpers.is_tuple_integers(parser, v),
            help='Optional, (default %(default)s) {0}'.format(CLOUD_SIZE_HELP)
        )
        parser.add_argument(
            '-min_image_size',
            default=DEFAULT_MIN_IMAGE_SIZE,
            metavar='"<width>,<height>"',
            type=lambda v: cli_helpers.is_tuple_integers(parser, v),
            help='Optional, (default %(default)s) {0}'.format(MIN_IMAGE_SIZE_HELP)
        )
        parser.add_argument(
            '-max_image_size',
            default=DEFAULT_MAX_IMAGE_SIZE,
            metavar='"<width>,<height>"',
            type=lambda v: cli_helpers.is_tuple_integers(parser, v),
            help='Optional, (default %(default)s) {0}'.format(MAX_IMAGE_SIZE_HELP)
        )
        parser.add_argument(
            '-background_color',
            default=DEFAULT_BACKGROUND_COLOR,
            metavar='<color-name>',
            help='Optional, (default %(default)s) {0}'.format(BACKGROUND_COLOR_HELP)
        )
        parser.add_argument(
            '-contour_width',
            default=DEFAULT_CONTOUR_WIDTH,
            metavar='<float>',
            type=lambda v: cli_helpers.is_float(parser, v),
            help='Optional, (default %(default)s) {0}'.format(CONTOUR_WIDTH_HELP)
        )
        parser.add_argument(
            '-contour_color',
            default=DEFAULT_CONTOUR_COLOR,
            metavar='<color-name>',
            help='Optional, (default %(default)s) {0}'.format(CONTOUR_COLOR_HELP)
        )
        parser.add_argument(
            '-mask',
            metavar='<image_file_path>',
            default=None,
            type=lambda fp: cli_helpers.existing_filepath(parser, fp),
            help='Optional, (default %(default)s) {0}'.format(MASK_HELP)
        )
        parser.add_argument(
            '-step_size',
            default=DEFAULT_STEP_SIZE,
            metavar='<int',
            type=lambda v: cli_helpers.is_integer(parser, v),
            help='Optional, (default %(default)s) {0}'.format(STEP_SIZE_HELP)
        )
        parser.add_argument(
            '-maintain_aspect_ratio',
            action='store_true',
            help='Optional, {0}{1}'.format('(default) ' if DEFAULT_MAINTAIN_ASPECT_RATIO else '', MAINTAIN_ASPECT_RATIO_HELP)
        )
        parser.add_argument(
            '-no-maintain_aspect_ratio',
            action='store_false',
            dest='maintain_aspect_ratio',
            help='Optional, {0}{1}'.format('' if DEFAULT_MAINTAIN_ASPECT_RATIO else '(default) ', MAINTAIN_ASPECT_RATIO_HELP)
        )
        parser.set_defaults(maintain_aspect_ratio=DEFAULT_MAINTAIN_ASPECT_RATIO)
        parser.add_argument(
            '-prefer_horizontal',
            default=DEFAULT_PREFER_HORIZONTAL,
            metavar='<float>',
            type=lambda v: cli_helpers.is_float(parser, v),
            help='Optional, (default %(default)s) {0}'.format(PREFER_HORIZONTAL_HELP)
        )
        parser.add_argument(
            '-margin',
            default=DEFAULT_MARGIN,
            metavar='<number>',
            type=lambda v: cli_helpers.is_integer(parser, v),
            help='Optional, (default %(default)s) {0}'.format(MARGIN_HELP)
        )
        parser.add_argument(
            '-mode',
            default=DEFAULT_MODE,
            metavar='{0}'.format('|'.join(MODE_TYPES)),
            type=lambda v: cli_helpers.is_one_of_array(parser, v, MODE_TYPES),
            help='Optional, (default %(default)s) {0}'.format(MODE_HELP)
        )
        parser.add_argument(
            '-show',
            action='store_true',
            help='Optional, {0}show resulting image cloud when finished.'.format('(default) ' if DEFAULT_SHOW else '')
        )
        parser.add_argument(
            '-no-show',
            action='store_false',
            dest='show',
            help='Optional, {0}do not show resulting image cloud when finished.'.format('' if DEFAULT_SHOW else '(default) ')
        )
        parser.set_defaults(show=DEFAULT_SHOW)
        
        parser.add_argument(
            '-expand_cloud_to_fit_all',
            action='store_true',
            help='Optional, {0}Expand cloud_size until all images fit in cloud'.format('(default) ' if DEFAULT_EXPAND_CLOUD_TO_FIT_ALL else '')
        )
        parser.add_argument(
            '-no-expand_cloud_to_fit_all',
            action='store_false',
            dest='expand_cloud_to_fit_all',
            help='Optional, {0}Expand cloud_size until all images fit in cloud'.format('' if DEFAULT_EXPAND_CLOUD_TO_FIT_ALL else '(default) ')
        )
        parser.set_defaults(expand_cloud_to_fit_all=DEFAULT_EXPAND_CLOUD_TO_FIT_ALL)

        parser.add_argument(
            '-verbose',
            action='store_true',
            help='Optional, {0}report progress as constructing cloud'.format('(default) ' if DEFAULT_VERBOSE else '')
        )
        parser.add_argument(
            '-no-verbose',
            action='store_false',
            dest='verbose',
            help='Optional, {0}report progress as constructing cloud'.format('' if DEFAULT_VERBOSE else '(default) ')
        )
        parser.set_defaults(verbose=DEFAULT_VERBOSE)

        args = parser.parse_args(arguments if 0 < len(arguments) else ['-h'])
        return ImageCloudGenerateArguments(
            input=args.input,
            output_image_filepath=args.output_image_filepath,
            output_layout_dirpath=args.output_layout_dirpath,
            output_image_format=args.output_image_format,
            max_image_size=args.max_image_size,
            min_image_size=args.min_image_size,
            cloud_size=args.cloud_size,
            background_color=args.background_color,
            contour_width=args.contour_width,
            contour_color=args.contour_color,
            mask=args.mask,
            step_size=args.step_size,
            maintain_aspect_ratio=args.maintain_aspect_ratio,
            prefer_horizontal=args.prefer_horizontal,
            margin=args.margin,
            mode=args.mode,
            show=args.show,
            expand_cloud_to_fit_all=args.expand_cloud_to_fit_all,
            logger=ConsoleLogger.create(args.verbose)
        )


def generate(args: ImageCloudGenerateArguments | None = None) -> None:
    if args == None:
        args = ImageCloudGenerateArguments.parse(sys.argv[1:])

    print('loading {0} ...'.format(args.input))
    weighted_images: list[WeightedImage] = load_weighted_images(args.input)
    total_images = len(weighted_images)
    print('loaded {0} weights and images'.format(total_images))

    image_cloud = ImageCloud(
        mask=args.mask,
        size=args.cloud_size,
        background_color=args.background_color,
        max_image_size=args.max_image_size,
        min_image_size=args.min_image_size,
        image_step=args.step_size,
        maintain_aspect_ratio=args.maintain_aspect_ratio,
        contour_width=args.contour_width,
        contour_color=args.contour_color,
        prefer_horizontal=args.prefer_horizontal,
        margin=args.margin,
        mode=args.mode,
        logger=args.logger.copy() if args.logger else None
    )
    print('generating image cloud from {0} weighted and normalized images{1}.'.format(
        total_images,
        ' iteratively until all images fit in cloud'if args.expand_cloud_to_fit_all else ''
    ))

    layout = image_cloud.generate(weighted_images, expand_cloud_to_fit_all=args.expand_cloud_to_fit_all)
    reconstructed_occupancy_map = layout.reconstruct_occupancy_map()
    if not(np.array_equal(layout.canvas.occupancy_map, reconstructed_occupancy_map)):
        print('Warning occupancy map from generation not same as reconstructed from images.')
    
    collage = layout.to_image(logger=args.logger.copy() if args.logger else None) if args.output_image_filepath is not None or args.show else None

    if args.output_image_filepath is not None:
        filepath = to_unused_filepath(args.output_image_filepath)
        print('saving image cloud to {0} as {1} type'.format(filepath, args.output_image_format))
        collage.image.save(filepath, args.output_image_format)
        print('completed! {0}'.format(filepath))

    if args.output_layout_dirpath is not None:        
        filepath = to_unused_filepath(os.path.join(args.output_layout_dirpath, 'imagecloud_layout.csv'))
        print('saving image cloud Layout to {0}'.format(filepath))
        layout.write(filepath)
        print('completed! {0}'.format(filepath))

    if args.show:
        collage.image.show()


if __name__ == '__main__':
    generate()