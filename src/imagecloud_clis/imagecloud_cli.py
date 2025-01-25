from imagecloud.console_logger import ConsoleLogger, LoggerLevel
import argparse
import csv
import os.path
import sys

import imagecloud_clis.argument_type_validators as validators
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
    DEFAULT_REPEAT,
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
    REPEAT_HELP,
    PREFER_HORIZONTAL_HELP,
    BACKGROUND_COLOR_HELP,
    MARGIN_HELP,
    MODE_HELP
)
from imagecloud.weighted_image import (
    WeightedImage
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
WEIGHT_HEADER = 'weight'
IMAGE_FILEPATH_HEADER = 'image_filepath'
CSV_FILE_HELP = '''csv file with following format:
"{0}","{1}"
"<full-path-to-image-file-1>",<weight-as-number-1>
...
"<full-path-to-image-file-N>",<weight-as-number-N>

'''.format(IMAGE_FILEPATH_HEADER, WEIGHT_HEADER)

    
def create_logger(verbose: bool) -> ConsoleLogger:
    return ConsoleLogger(LoggerLevel.DEBUG if verbose else LoggerLevel.INFO)

class ImageCloudArguments:
    def __init__ (
        self, 
        input: str,
        output: str,
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
        repeat: bool,
        show: bool,
        logger: ConsoleLogger | None
    ) -> None:
        self.input = input
        self.output = output
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
        self.repeat = repeat
        self.show = show
        self.logger = logger
    
    @staticmethod
    def parse(arguments: list[str]):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            prog='imagecloud_cli',
            description='''
            Generate an \'ImageCloud\' from a csv file indicating image filepath and weight for image.
            '''
        )
        parser.add_argument(
            '-i', 
            '--input',
            metavar='<csv_filepath>',
            type=lambda fp: validators.existing_filepath(parser, fp),
            required=True,
            help='Required, {0}'.format(CSV_FILE_HELP)
        )
        parser.add_argument(
            '-o',
            '--output',
            metavar='<generated_image_cloud_filepath>',
            type=str,
            required=True,
            help='Required, output file path for generated image cloud'
        )
        parser.add_argument(
            '-output_image_format',
            default=DEFAULT_IMAGE_FORMAT,
            metavar='{0}'.format('|'.join(IMAGE_FORMATS)),
            type=lambda v: validators.is_one_of_array(parser, v, IMAGE_FORMATS),
            help='Optional,(default %(default)s) {0}'.format(IMAGE_FORMAT_HELP)
        )
        parser.add_argument(
            '-cloud_size',
            default=DEFAULT_CLOUD_SIZE,
            metavar='"<width>,<height>"',
            type= lambda v: validators.is_tuple_integers(parser, v),
            help='Optional, (default %(default)s) {0}'.format(CLOUD_SIZE_HELP)
        )
        parser.add_argument(
            '-min_image_size',
            default=DEFAULT_MIN_IMAGE_SIZE,
            metavar='"<width>,<height>"',
            type=lambda v: validators.is_tuple_integers(parser, v),
            help='Optional, (default %(default)s) {0}'.format(MIN_IMAGE_SIZE_HELP)
        )
        parser.add_argument(
            '-max_image_size',
            default=DEFAULT_MAX_IMAGE_SIZE,
            metavar='"<width>,<height>"',
            type=lambda v: validators.is_tuple_integers(parser, v),
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
            type=lambda v: validators.is_float(parser, v),
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
            type=lambda fp: validators.existing_filepath(parser, fp),
            help='Optional, (default %(default)s) {0}'.format(MASK_HELP)
        )
        parser.add_argument(
            '-step_size',
            default=DEFAULT_STEP_SIZE,
            metavar='<int',
            type=lambda v: validators.is_integer(parser, v),
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
            type=lambda v: validators.is_float(parser, v),
            help='Optional, (default %(default)s) {0}'.format(PREFER_HORIZONTAL_HELP)
        )
        parser.add_argument(
            '-margin',
            default=DEFAULT_MARGIN,
            metavar='<number>',
            type=lambda v: validators.is_integer(parser, v),
            help='Optional, (default %(default)s) {0}'.format(MARGIN_HELP)
        )
        parser.add_argument(
            '-mode',
            default=DEFAULT_MODE,
            metavar='{0}'.format('|'.join(MODE_TYPES)),
            type=lambda v: validators.is_one_of_array(parser, v, MODE_TYPES),
            help='Optional, (default %(default)s) {0}'.format(MODE_HELP)
        )
        parser.add_argument(
            '-repeat',
            action='store_true',
            help='Optional, {0}{1}'.format('(default) ' if DEFAULT_REPEAT else '', REPEAT_HELP)
        )
        parser.add_argument(
            '-no-repeat',
            action='store_false',
            dest='repeat',
            help='Optional, {0}{1}'.format('' if DEFAULT_REPEAT else '(default) ', REPEAT_HELP)
        )
        parser.set_defaults(repeat=DEFAULT_REPEAT)
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
        return ImageCloudArguments(
            input=args.input,
            output=args.output,
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
            repeat=args.repeat,
            show=args.show,
            logger=create_logger(args.verbose)
        )

def load_weighted_images(csv_filepath: str) -> list[WeightedImage]:
    result: list[WeightedImage] = list()
    with open(csv_filepath, 'r') as file:    
        csv_reader = csv.DictReader(file, fieldnames=[IMAGE_FILEPATH_HEADER, WEIGHT_HEADER])
        next(csv_reader)
        for row in csv_reader:
            result.append(WeightedImage.load(float(row[WEIGHT_HEADER]), row[IMAGE_FILEPATH_HEADER]))
    return result

def to_unused_filepath(filepath: str, new_suffix: str | None = None) -> str:
    filepath_parts = filepath.split('.')
    filepath_prefix = '.'.join(filepath_parts[:-1])
    suffix = new_suffix if new_suffix != None else filepath_parts[-1]
    result = '{0}.{1}'.format(filepath_prefix, suffix)
    version: int = 0
    while os.path.isfile(result):
        version += 1
        result = '{0}.{1}.{2}'.format(filepath_prefix, version, suffix)
    return result

def main(args: ImageCloudArguments | None = None) -> None:
    if args == None:
        args = ImageCloudArguments.parse(sys.argv[1:])
    output_filepath = to_unused_filepath(args.output)
    print('Generating image cloud based on weights and images from {0} into {1}'.format(args.input, output_filepath))

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
        repeat=args.repeat,
        prefer_horizontal=args.prefer_horizontal,
        margin=args.margin,
        mode=args.mode,
        logger=args.logger
    )
    print('generating image cloud from {0} weighted and normalized images'.format(total_images))

    image_cloud.generate(weighted_images)
    
    print('saving image cloud to {0} as {1} type'.format(output_filepath, args.output_image_format))
    collage = image_cloud.to_image()
    collage.save(output_filepath, args.output_image_format)
    
    print('completed! {0}'.format(output_filepath))
    if args.show:
        collage.show(output_filepath)


if __name__ == '__main__':
    main()