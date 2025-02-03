from imagecloud_clis.cli_base_arguments import CLIBaseArguments
import argparse
import sys
import numpy as np
import imagecloud_clis.cli_helpers as cli_helpers
from imagecloud.position_box_size import Size
from imagecloud.imagecloud_defaults import (
    DEFAULT_CLOUD_SIZE,
    DEFAULT_BACKGROUND_COLOR,
    DEFAULT_CONTOUR_COLOR,
    DEFAULT_CONTOUR_WIDTH,
    DEFAULT_MARGIN,
    DEFAULT_MAX_IMAGE_SIZE,
    DEFAULT_MIN_IMAGE_SIZE,
    DEFAULT_MODE,
    DEFAULT_STEP_SIZE,
    DEFAULT_MAINTAIN_ASPECT_RATIO
)
from imagecloud.imagecloud_defaults import (
    MASK_HELP,
    CLOUD_SIZE_HELP,
    STEP_SIZE_HELP,
    MAINTAIN_ASPECT_RATIO_HELP,
    MAX_IMAGE_SIZE_HELP,
    MIN_IMAGE_SIZE_HELP,
    BACKGROUND_COLOR_HELP,
    CONTOUR_WIDTH_HELP,
    CONTOUR_COLOR_HELP,
    BACKGROUND_COLOR_HELP,
    MARGIN_HELP,
    MODE_HELP
)
from imagecloud.weighted_image import (
    WeightedImage,
    WEIGHTED_IMAGES_CSV_FILE_HELP,
    load_weighted_images,
)
from imagecloud.imagecloud_defaults import MODE_TYPES
from imagecloud.imagecloud import ImageCloud
DEFAULT_MAXIMIZE_EMPTY_SPACE = False
DEFAULT_SHOW = True
DEFAULT_VERBOSE = False
DEFAULT_CLOUD_EXPAND_STEP_SIZE = '0'
DEFAULT_CLOUD_EXPAND_STEP_SIZE_HELP = '''Step size for expanding cloud to fit more images
images will be proportionally fit to the original cloud size but may still not get placed to fit in cloud.
step > 0 the cloud will expand by this amount in a loop until all images fit into it.
step > 1 might speed up computation but give a worse fit.
'''

class GenerateCLIArguments(CLIBaseArguments):
    name = 'generate_imagecloud'
    def __init__ (
        self, 
        parsedArgs
    ) -> None:
        super().__init__(self.name, parsedArgs)
        self.max_image_size: Size | None = parsedArgs.max_image_size
        self.min_image_size: Size = parsedArgs.min_image_size
        self.cloud_size: Size = parsedArgs.cloud_size
        self.background_color = parsedArgs.background_color
        self.contour_width: int = parsedArgs.contour_width
        self.contour_color: str = parsedArgs.contour_color
        self.mask: str | None = parsedArgs.mask
        self.step_size: int = parsedArgs.step_size
        self.maintain_aspect_ratio: bool = parsedArgs.maintain_aspect_ratio
        self.margin: int = parsedArgs.margin
        self.mode: str = parsedArgs.mode
        self.cloud_expansion_step_size: int = parsedArgs.cloud_expansion_step_size
        self.maximize_empty_space: bool = parsedArgs.maximize_empty_space
    
    @staticmethod
    def parse(arguments: list[str]):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            prog=GenerateCLIArguments.name,
            description='''
            Generate an \'ImageCloud\' from a csv file indicating image filepath and weight for image.
            '''
        )
        CLIBaseArguments.add_parser_arguments(
            parser,
            WEIGHTED_IMAGES_CSV_FILE_HELP,
            DEFAULT_SHOW,
            DEFAULT_VERBOSE
        )

        parser.add_argument(
            '-cloud_size',
            default=DEFAULT_CLOUD_SIZE,
            metavar='"<width>,<height>"',
            type= lambda v: cli_helpers.is_size(parser, v),
            help='Optional, (default %(default)s) {0}'.format(CLOUD_SIZE_HELP)
        )

        parser.add_argument(
            '-cloud_expansion_step_size',
            default=DEFAULT_CLOUD_EXPAND_STEP_SIZE,
            metavar='<int>',
            type=lambda v: cli_helpers.is_integer(parser, v),
            help='Optional, (default %(default)s) {0}'.format(DEFAULT_CLOUD_EXPAND_STEP_SIZE_HELP)
        )

        parser.add_argument(
            '-maximize_empty_space',
            action='store_true',
            help='Optional {0}maximize images, after generation, to fill surrouding empty space.'.format('(default) ' if DEFAULT_MAXIMIZE_EMPTY_SPACE else '')
        )
        parser.add_argument(
            '-no-maximize_empty_space',
            action='store_false',
            dest='maximize_empty_space',
            help='Optional {0}maximize images, after generation, to fill surrouding empty space.'.format('' if DEFAULT_MAXIMIZE_EMPTY_SPACE else '(default) ')
        )
        parser.set_defaults(maximize_empty_space=DEFAULT_MAXIMIZE_EMPTY_SPACE)

        parser.add_argument(
            '-margin',
            default=DEFAULT_MARGIN,
            metavar='<number>',
            type=lambda v: cli_helpers.is_integer(parser, v),
            help='Optional, (default %(default)s) {0}'.format(MARGIN_HELP)
        )

        parser.add_argument(
            '-min_image_size',
            default=DEFAULT_MIN_IMAGE_SIZE,
            metavar='"<width>,<height>"',
            type=lambda v: cli_helpers.is_size(parser, v),
            help='Optional, (default %(default)s) {0}'.format(MIN_IMAGE_SIZE_HELP)
        )

        parser.add_argument(
            '-step_size',
            default=DEFAULT_STEP_SIZE,
            metavar='<int>',
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
            '-max_image_size',
            default=DEFAULT_MAX_IMAGE_SIZE,
            metavar='"<width>,<height>"',
            type=lambda v: cli_helpers.is_size(parser, v),
            help='Optional, (default %(default)s) {0}'.format(MAX_IMAGE_SIZE_HELP)
        )

        parser.add_argument(
            '-mode',
            default=DEFAULT_MODE,
            metavar='{0}'.format('|'.join(MODE_TYPES)),
            type=lambda v: cli_helpers.is_one_of_array(parser, v, MODE_TYPES),
            help='Optional, (default %(default)s) {0}'.format(MODE_HELP)
        )
        parser.add_argument(
            '-background_color',
            default=DEFAULT_BACKGROUND_COLOR,
            metavar='<color-name>',
            help='Optional, (default %(default)s) {0}'.format(BACKGROUND_COLOR_HELP)
        )

        parser.add_argument(
            '-mask',
            metavar='<image_file_path>',
            default=None,
            type=lambda fp: cli_helpers.existing_filepath(parser, fp),
            help='Optional, (default %(default)s) {0}'.format(MASK_HELP)
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

        args = parser.parse_args(arguments if 0 < len(arguments) else ['-h'])
        return GenerateCLIArguments(args)


def generate(args: GenerateCLIArguments | None = None) -> None:
    sys_args = sys.argv[1:]
    if args == None:
        args = GenerateCLIArguments.parse(sys_args)
    
    args.logger.info('{0} {1}'.format(GenerateCLIArguments.name, ' '.join(sys_args)))
    args.logger.info('loading {0} ...'.format(args.input))
    weighted_images: list[WeightedImage] = load_weighted_images(args.input)
    total_images = len(weighted_images)
    args.logger.info('loaded {0} weights and images'.format(total_images))

    image_cloud = ImageCloud(
        logger=args.logger,
        mask=args.mask,
        size=args.cloud_size,
        background_color=args.background_color,
        max_image_size=args.max_image_size,
        min_image_size=args.min_image_size,
        image_step=args.step_size,
        maintain_aspect_ratio=args.maintain_aspect_ratio,
        contour_width=args.contour_width,
        contour_color=args.contour_color,
        margin=args.margin,
        mode=args.mode,
        name=args.get_output_name()
    )
    args.logger.info('generating image cloud from {0} weighted and normalized images.{1}'.format(
        total_images,
        ' Cloud will be expanded iteratively by cloud_expansion_step_size until all images are positioned.' if 0 != args.cloud_expansion_step_size else ''
    ))

    layout = image_cloud.generate(weighted_images, cloud_expansion_step_size=args.cloud_expansion_step_size)
    if args.maximize_empty_space:
        args.logger.info('Maximizing {0} images: expanding them to fit their surrounding empty space.'.format(len(layout.items)))
        layout = image_cloud.maximize_empty_space(layout)

    reconstructed_occupancy_map = layout.reconstruct_occupancy_map()
    if not(np.array_equal(layout.canvas.occupancy_map, reconstructed_occupancy_map)):
        args.logger.info('Warning occupancy map from generation not same as reconstructed from images.')
    
    collage = layout.to_image(args.logger)

    args.try_save_output(collage, None, layout)

    if args.show_imagecloud_reservation_chart:
        reservation_chart = layout.to_reservation_chart_image()
        args.try_save_output(None, reservation_chart, None)
        reservation_chart.show()

    if args.show_imagecloud:
        collage.show()

if __name__ == '__main__':
    generate()