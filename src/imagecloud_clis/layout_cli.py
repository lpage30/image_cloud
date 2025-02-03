from imagecloud_clis.cli_base_arguments import CLIBaseArguments
import argparse
import sys
import imagecloud_clis.cli_helpers as cli_helpers
from imagecloud.layout import Layout, LAYOUT_CSV_FILE_HELP
from imagecloud.imagecloud import ImageCloud

DEFAULT_SCALE = '1.0'
DEFAULT_VERBOSE = False
DEFAULT_MAXIMIZE_EMPTY_SPACE = False
DEFAULT_SHOW = False

class LayoutCLIrguments(CLIBaseArguments):
    name = 'layout_imagecloud'
    def __init__ (
        self, 
        parsedArgs
    ) -> None:
        super().__init__(self.name, parsedArgs)
        self.scale: float = parsedArgs.scale
        self.maximize_empty_space: bool = parsedArgs.maximize_empty_space
    
    @staticmethod
    def parse(arguments: list[str]):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            prog=LayoutCLIrguments.name,
            description='''
            Layout and show a generated \'ImageCloud\' from its layout csv file
            '''
        )
        CLIBaseArguments.add_parser_arguments(
            parser,
            LAYOUT_CSV_FILE_HELP,
            DEFAULT_SHOW,
            DEFAULT_VERBOSE
        )
        parser.add_argument(
            '-scale',
            default=DEFAULT_SCALE,
            metavar='<float>',
            type=lambda v: cli_helpers.is_float(parser, v),
            help='Optional, (default %(default)s) scale up/down all images'
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


        args = parser.parse_args(arguments if 0 < len(arguments) else ['-h'])
        return LayoutCLIrguments(args)




def layout(args: LayoutCLIrguments | None = None) -> None:
    sys_args = sys.argv[1:]    
    if args == None:
        args = LayoutCLIrguments.parse(sys_args)
    
    args.logger.info('{0} {1}'.format(LayoutCLIrguments.name, ' '.join(sys_args)))
    args.logger.info('loading {0} ...'.format(args.input))
    layout = Layout.load(args.input)
    args.logger.info('loaded layout with {0} images'.format(len(layout.items)))
    args.logger.info('laying-out and showing imagecloud layout with {0} scaling.'.format(args.scale))
    
    layout.set_names(
        args.get_output_name(layout.name),
        args.get_output_name(layout.canvas.name)
    )

    if args.maximize_empty_space:
        args.logger.info('Maximizing {0} images: expanding them to fit their surrounding empty space.'.format(len(layout.items)))
        cloud = ImageCloud.create(layout, args.logger.copy())
        layout = cloud.maximize_empty_space(layout)

    collage = layout.to_image(args.logger.copy(), args.scale)
    reservation_chart = layout.to_reservation_chart_image()
    args.try_save_output(collage, reservation_chart, layout)
        
    if args.show_imagecloud:
        collage.show()

    if args.show_imagecloud_reservation_chart:
        reservation_chart.show()



if __name__ == '__main__':
    layout()