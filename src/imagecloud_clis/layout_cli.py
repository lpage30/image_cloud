from imagecloud.console_logger import ConsoleLogger
import argparse
import sys

import imagecloud_clis.cli_helpers as cli_helpers

from imagecloud.layout import (
    Layout,
    LAYOUT_CSV_FILE_HELP
)
from imagecloud.imagecloud_defaults import (
    DEFAULT_IMAGE_FORMAT,
    IMAGE_FORMAT_HELP,
    IMAGE_FORMATS
)
from imagecloud.imagecloud_helpers import to_unused_filepath

DEFAULT_SCALE = '1.0'
DEFAULT_VERBOSE = False

class ImageCloudLayoutArguments:
    def __init__ (
        self, 
        input: str,
        output_image_filepath: str | None,
        output_image_format: str,
        scale: float,
        logger: ConsoleLogger | None
    ) -> None:
        self.input = input
        self.output_image_filepath = output_image_filepath
        self.output_image_format = output_image_format
        self.scale = scale
        self.logger = logger
    
    @staticmethod
    def parse(arguments: list[str]):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            prog='layout_imagecloud',
            description='''
            Layout and show a generated \'ImageCloud\' from its layout csv file
            '''
        )
        parser.add_argument(
            '-i', 
            '--input',
            metavar='<csv_filepath>',
            type=lambda fp: cli_helpers.existing_filepath(parser, fp),
            required=True,
            help='Required, {0}'.format(LAYOUT_CSV_FILE_HELP)
        )
        parser.add_argument(
            '-scale',
            default=DEFAULT_SCALE,
            metavar='<float>',
            type=lambda v: cli_helpers.is_float(parser, v),
            help='Optional, (default %(default)s) scale up/down all images'
        )
        parser.add_argument(
            '-output_image_filepath',
            metavar='<layedout_image_cloud_image_filepath>',
            type=str,
            help='Optional, output file path for layed-out image cloud image'
        )
        parser.add_argument(
            '-output_image_format',
            default=DEFAULT_IMAGE_FORMAT,
            metavar='{0}'.format('|'.join(IMAGE_FORMATS)),
            type=lambda v: cli_helpers.is_one_of_array(parser, v, IMAGE_FORMATS),
            help='Optional,(default %(default)s) {0}'.format(IMAGE_FORMAT_HELP)
        )

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
        return ImageCloudLayoutArguments(
            input=args.input,
            output_image_filepath=args.output_image_filepath,
            output_image_format=args.output_image_format,
            scale=args.scale,
            show=args.show,
            logger=ConsoleLogger.create(args.verbose)
        )


def layout(args: ImageCloudLayoutArguments | None = None) -> None:
    if args == None:
        args = ImageCloudLayoutArguments.parse(sys.argv[1:])

    print('loading {0} ...'.format(args.input))
    layout = Layout.load(args.input)
    print('loaded layout with {0} images'.format(len(layout.items)))
    print('laying-out and showing image cloud layout with {0} scaling.'.format(args.scale))

    collage = layout.to_image(scale=args.scale, logger=args.logger)

    if args.output_image_filepath != None:
        filepath = to_unused_filepath(args.output_image_filepath)
        print('saving image cloud to {0} as {1} type'.format(filepath, args.output_image_format))
        collage.image.save(filepath, args.output_image_format)
        print('completed! {0}'.format(filepath))
        
    collage.image.show()


if __name__ == '__main__':
    layout()