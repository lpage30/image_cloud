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
DEFAULT_SHOW_IMAGECLOUD = False
DEFAULT_SHOW_IMAGECLOUD_RESERVATION_CHART = False

class ImageCloudLayoutArguments:
    def __init__ (
        self, 
        input: str,
        save_imagecloud_filepath: str | None,
        save_reservation_chart_filepath: str | None,
        save_imagecloud_format: str,
        scale: float,
        show_imagecloud: bool,
        show_imagecloud_reservation_chart: bool,
        logger: ConsoleLogger | None
    ) -> None:
        self.input = input
        self.save_imagecloud_filepath = save_imagecloud_filepath
        self.save_reservation_chart_filepath = save_reservation_chart_filepath
        self.save_imagecloud_format = save_imagecloud_format
        self.scale = scale
        self.show_imagecloud = show_imagecloud
        self.show_imagecloud_reservation_chart = show_imagecloud_reservation_chart
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
            '-save_imagecloud_filepath',
            metavar='<filepath_for_save_imagecloud',
            type=str,
            help='Optional, filepath to save imagecloud'
        )
        parser.add_argument(
            '-save_reservation_chart_filepath',
            metavar='<filepath_for_save_imagecloud_reservation_chart',
            type=str,
            help='Optional, filepath to save imagecloud reservation_chart with legend'
        )
        parser.add_argument(
            '-save_imagecloud_format',
            default=DEFAULT_IMAGE_FORMAT,
            metavar='{0}'.format('|'.join(IMAGE_FORMATS)),
            type=lambda v: cli_helpers.is_one_of_array(parser, v, IMAGE_FORMATS),
            help='Optional,(default %(default)s) {0}'.format(IMAGE_FORMAT_HELP)
        )
        parser.add_argument(
            '-show_imagecloud',
            action='store_true',
            help='Optional, {0}show image cloud.'.format('(default) ' if DEFAULT_SHOW_IMAGECLOUD else '')
        )
        parser.add_argument(
            '-no-show_imagecloud',
            action='store_false',
            dest='show_imagecloud',
            help='Optional, {0}do not show mage cloud.'.format('' if DEFAULT_SHOW_IMAGECLOUD else '(default) ')
        )
        parser.set_defaults(show_imagecloud=DEFAULT_SHOW_IMAGECLOUD)

        parser.add_argument(
            '-show_imagecloud_reservation_chart',
            action='store_true',
            help='Optional, {0}show reservation_chart for image cloud.'.format('(default) ' if DEFAULT_SHOW_IMAGECLOUD_RESERVATION_CHART else '')
        )
        parser.add_argument(
            '-no-show_imagecloudreservation_chart',
            action='store_false',
            dest='show_imagecloud_reservation_chart',
            help='Optional, {0}do not show reservation_chart for image cloud.'.format('' if DEFAULT_SHOW_IMAGECLOUD_RESERVATION_CHART else '(default) ')
        )
        parser.set_defaults(show_imagecloud_reservation_chart=DEFAULT_SHOW_IMAGECLOUD_RESERVATION_CHART)

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
            save_imagecloud_filepath=args.save_imagecloud_filepath,
            save_reservation_chart_filepath=args.save_reservation_chart_filepath,
            save_imagecloud_format=args.save_imagecloud_format,
            scale=args.scale,
            show_imagecloud=args.show_imagecloud,
            show_imagecloud_reservation_chart=args.show_imagecloud_reservation_chart,
            logger=ConsoleLogger.create(args.verbose)
        )



def layout(args: ImageCloudLayoutArguments | None = None) -> None:
    if args == None:
        args = ImageCloudLayoutArguments.parse(sys.argv[1:])

    print('loading {0} ...'.format(args.input))
    layout = Layout.load(args.input)
    print('loaded layout with {0} images'.format(len(layout.items)))
    print('laying-out and showing image cloud layout with {0} scaling.'.format(args.scale))

    collage = layout.to_image(scale=args.scale, logger=args.logger.copy() if args.logger else None)
    reservation_chart = layout.to_reservation_chart_image()

    if args.save_imagecloud_filepath is not None:
        filepath = to_unused_filepath(args.save_imagecloud_filepath)
        print('saving image cloud to {0} as {1} type'.format(filepath, args.save_imagecloud_format))
        collage.image.save(filepath, args.save_imagecloud_format)
        print('completed! {0}'.format(filepath))
    
    if args.save_reservation_chart_filepath is not None:
        filepath = to_unused_filepath(args.save_reservation_chart_filepath)
        print('saving image cloud reservation chart to {0} as png type'.format(filepath))
        reservation_chart.image.save(filepath)
        print('completed! {0}'.format(filepath))
        
    if args.show_imagecloud:
        collage.image.show()

    if args.show_imagecloud_reservation_chart:
        reservation_chart.image.show()



if __name__ == '__main__':
    layout()