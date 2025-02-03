import argparse
from imagecloud.base_logger import BaseLogger
from imagecloud.file_logger import FileLogger
import imagecloud_clis.cli_helpers as cli_helpers
from imagecloud.imagecloud_helpers import to_unused_filepath
from imagecloud.imagecloud_defaults import DEFAULT_IMAGE_FORMAT, IMAGE_FORMATS, IMAGE_FORMAT_HELP
from imagecloud.weighted_image import NamedImage
from imagecloud.layout import Layout


class CLIBaseArguments:
    def __init__ (
        self,
        name: str,
        parsedArgs: argparse.Namespace
    ):
        self.input: str = parsedArgs.input
        self.output_directory: str | None = parsedArgs.output_directory
        self.output_image_format: str = parsedArgs.output_image_format
        self.show_imagecloud: bool = parsedArgs.show_imagecloud
        self.show_imagecloud_reservation_chart: bool = parsedArgs.show_imagecloud_reservation_chart
        if parsedArgs.log_filepath:
            self.logger: BaseLogger = FileLogger.create(name, parsedArgs.verbose, parsedArgs.log_filepath)
        else:
            self.logger: BaseLogger = BaseLogger.create(name, parsedArgs.verbose)

    def get_output_name(self, existing_name: str | None = None) -> str:
        return cli_helpers.to_name(self.input, self.output_image_format, existing_name, self.output_directory)

    def try_save_output(
        self, 
        collage: NamedImage | None = None,
        reservation_chart: NamedImage | None = None,
        layout: Layout | None = None
    ) -> bool:
        result: bool = False
        if self.output_directory is None:
            return result

        if collage:
            result = True
            filepath = to_unused_filepath(self.output_directory, collage.name, self.output_image_format)
            print('saving image cloud to {0}'.format(filepath))
            collage.image.save(filepath, self.output_image_format)
            print('completed! {0}'.format(filepath))

        if reservation_chart:
            result = True
            filepath = to_unused_filepath(self.output_directory, reservation_chart.name, self.output_image_format)
            print('saving image cloud reservation chart to {0}'.format(filepath))
            collage.image.save(filepath, self.output_image_format)
            print('completed! {0}'.format(filepath))
        
        if layout:
            result = True
            filepath = to_unused_filepath(self.output_directory, layout.name, 'csv')
            print('saving image cloud Layout to {0}'.format(filepath))
            layout.write(filepath)
            print('completed! {0}'.format(filepath))
        
        return result

    @staticmethod
    def add_parser_arguments(
        argParser: argparse.ArgumentParser,
        inputHelp: str,
        showDefault: bool,
        verboseDefault: bool
    ) -> None:
        argParser.add_argument(
            '-i', 
            '--input',
            metavar='<csv_filepath>',
            type=lambda fp: cli_helpers.existing_filepath(argParser, fp),
            required=True,
            help='Required, {0}'.format(inputHelp)
        )
        argParser.add_argument(
            '-output_directory',
            metavar='<output-directory-path>',
            type=lambda d: cli_helpers.existing_dirpath(argParser, d),
            help='Optional, output directory for all output'
        )
        argParser.add_argument(
            '-output_image_format',
            default=DEFAULT_IMAGE_FORMAT,
            metavar='{0}'.format('|'.join(IMAGE_FORMATS)),
            type=lambda v: cli_helpers.is_one_of_array(argParser, v, IMAGE_FORMATS),
            help='Optional,(default %(default)s) {0}'.format(IMAGE_FORMAT_HELP)
        )
        argParser.add_argument(
            '-show_imagecloud',
            action='store_true',
            help='Optional, {0}show image cloud.'.format('(default) ' if showDefault else '')
        )
        argParser.add_argument(
            '-no-show_imagecloud',
            action='store_false',
            dest='show_imagecloud',
            help='Optional, {0}do not show mage cloud.'.format('' if showDefault else '(default) ')
        )
        argParser.set_defaults(show_imagecloud=showDefault)

        argParser.add_argument(
            '-show_imagecloud_reservation_chart',
            action='store_true',
            help='Optional, show reservation_chart for image cloud.'
        )
        argParser.add_argument(
            '-no-show_imagecloud_reservation_chart',
            action='store_false',
            dest='show_imagecloud_reservation_chart',
            help='Optional, (default) do not show reservation_chart for image cloud.'
        )
        argParser.set_defaults(show_imagecloud_reservation_chart=False)

        argParser.add_argument(
            '-verbose',
            action='store_true',
            help='Optional, {0}report progress as constructing cloud'.format('(default) ' if verboseDefault else '')
        )
        argParser.add_argument(
            '-no-verbose',
            action='store_false',
            dest='verbose',
            help='Optional, {0}report progress as constructing cloud'.format('' if verboseDefault else '(default) ')
        )
        argParser.set_defaults(verbose=verboseDefault)
        
        argParser.add_argument(
            '-log_filepath',
            metavar='<log-filepath>',
            type=lambda fp: cli_helpers.existing_dirpath_of_filepath(argParser, fp),
            help='Optional, all output logging will also be written to this logfile'
            
        )
