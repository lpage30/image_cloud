from typing import TypedDict
import argparse
import os.path
import sys
try:
    from . import images as imgs
    from . import imagecloud as ic
except Exception as e:
    import images as imgs
    import imagecloud as ic

DEFAULT_SHOW = True

def existing_filepath(parser: argparse.ArgumentParser, value: str) -> str:
    if not os.path.exists(value):
        parser.error('The file {0} does not exist!'.format(value))
    else:
        return value
    
def is_one_of_array(parser: argparse.ArgumentParser, value: str, valid_values: list[str]) -> str:
    if value in valid_values:
        return value
    else:
        parser.error('Invalid value {0} must be one of [{1}]'.format(value, ','.join(valid_values)))

def is_integer(parser: argparse.ArgumentParser, value: str):
    try:
        return ic.parse_to_int(str)
    except Exception as e:
        parser.error(str(e))

def is_float(parser: argparse.ArgumentParser, value: str):
    try:
        return ic.parse_to_float(value)
    except Exception as e:
        parser.error(str(e))

def is_tuple_integers(parser: argparse.ArgumentParser, value: str):
    try:
        return ic.parse_to_tuple(value)
    except Exception as e:
        parser.error(str(e))
    
class ImageCloudArguments(TypedDict):
    input: str
    output: str
    output_image_format: str
    normalize_type: str
    max_image_size: tuple[int, int] | None
    min_image_size: tuple[int, int]
    cloud_size: tuple[int, int]
    background_color: str
    contour_width: int
    contour_color: str
    mask: str | None
    step_size: tuple[int, int]
    relative_scaling: float | None
    prefer_horizontal: float
    margin: int
    mode: str
    repeat: bool
    show: bool

def main(args: ImageCloudArguments | None = None) -> None:
    if args == None:
        args = parse_arguments(sys.argv[1:])
    output_fileparts = args.output.split('.')
    output_filepath = imgs.to_unused_filepath('.'.join(output_fileparts[:-1]), output_fileparts[-1])
    print('Generating image cloud based on weights and images from {0} into {1}'.format(args.input, output_filepath))

    print('loading {0} ...'.format(args.input))
    weights, images, filepaths = imgs.load_weights_images_filepaths(args.input)
    total_images = len(images)
    print('loaded {0} weights and images'.format(total_images))

    print('normalizing {0} weights and images using {1} image size...'.format(total_images, args.normalize_type))
    normalized_images = imgs.normalize_images(args.normalize_type, images, args.cloud_size, reportProgress=print)
    normalized_filepaths = imgs.rename_filenames(filepaths, 'normalizing-type-{0}.{1}'.format(args.normalize_type, args.output_image_format))
    normalized_csv_filename = imgs.to_unused_filepath(args.input,'normalizing-type-{0}.csv'.format(args.normalize_type))
    print('saving {0} weights and normalized images to {1}'.format(total_images, normalized_csv_filename))
    imgs.save_weights_images(
        weights,
        normalized_images,
        normalized_filepaths,
        normalized_csv_filename,
        args.output_image_format,
        reportProgress=print
    )
    weighted_images = imgs.to_weighted_images(weights, normalized_images)

    image_cloud = ic.ImageCloud(
        mask=args.mask,
        size=args.cloud_size,
        background_color=args.background_color,
        max_image_size=args.max_image_size,
        min_image_size=args.min_image_size,
        image_step=args.step_size,
        contour_width=args.contour_width,
        contour_color=args.contour_color,
        repeat=args.repeat,
        relative_scaling=args.relative_scaling,
        prefer_horizontal=args.prefer_horizontal,
        margin=args.margin,
        mode=args.mode
    )
    print('generating image cloud from {0} weighted and normalized images'.format(total_images))

    image_cloud.generate(weighted_images, reportProgress=print)
    
    print('saving image cloud to {0} as {1} type'.format(output_filepath, args.output_image_format))
    collage = image_cloud.to_image(reportProgress=print)
    collage.save(output_filepath, args.output_image_format)
    
    print('completed! {0}'.format(output_filepath))
    if args.show:
        collage.show(output_filepath)


def parse_arguments(arguments: list[str]) -> ImageCloudArguments:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog='imagecloud_cli',
        description='''
        Generate an \'ImageCloud\' from a csv file indicating image filepath and weight for image.
        '''
    )
    parser.add_argument(
        '-i', '--input',
        metavar='<csv_filepath>',
        type=lambda fp: existing_filepath(parser, fp),
        required=True,
        help='Required, {0}'.format(imgs.CSV_FILE_HELP)
    )
    parser.add_argument(
        '-o', '--output',
        metavar='<generated_image_cloud_filepath>',
        type=str,
        required=True,
        help='Required, output file path for generated image cloud'
    )
    parser.add_argument(
        '--output_image_format',
        default=imgs.DEFAULT_IMAGE_FORMAT,
        metavar='{0}'.format('|'.join(imgs.IMAGE_FORMATS)),
        type=lambda v: is_one_of_array(parser, v, imgs.IMAGE_FORMATS),
        help='Optional,(default %(default)s) {0}'.format(imgs.IMAGE_FORMAT_HELP)
    )
    parser.add_argument(
        '--normalize_type',
        default=imgs.DEFAULT_NORMALIZE_TYPE,
        metavar='{0}'.format('|'.join(imgs.NORMALIZING_TYPES)),
        type=lambda v: is_one_of_array(parser, v, imgs.NORMALIZING_TYPES),
        help='Optional, (default %(default)s) {0}'.format(imgs.NORMALIZING_TYPE_HELP.format('cloud_size'))
    )
    parser.add_argument(
        '--cloud_size',
        default=ic.DEFAULT_CLOUD_SIZE,
        metavar='"<width>,<height>"',
        type= lambda v: is_tuple_integers(parser, v),
        help='Optional, (default %(default)s) {0}'.format(ic.CLOUD_SIZE_HELP)
    )
    parser.add_argument(
        '--min_image_size',
        default=ic.DEFAULT_MIN_IMAGE_SIZE,
        metavar='"<width>,<height>"',
        type=lambda v: is_tuple_integers(parser, v),
        help='Optional, (default %(default)s) {0}'.format(ic.MIN_IMAGE_SIZE_HELP)
    )
    parser.add_argument(
        '--max_image_size',
        default=ic.DEFAULT_MAX_IMAGE_SIZE,
        metavar='"<width>,<height>"',
        type=lambda v: is_tuple_integers(parser, v),
        help='Optional, (default %(default)s) {0}'.format(ic.MAX_IMAGE_SIZE_HELP)
    )
    parser.add_argument(
        '--background_color',
        default=ic.DEFAULT_BACKGROUND_COLOR,
        metavar='<color-name>',
        help='Optional, (default %(default)s) {0}'.format(ic.BACKGROUND_COLOR_HELP)
    )
    parser.add_argument(
        '--contour_width',
        default=ic.DEFAULT_CONTOUR_WIDTH,
        metavar='<float>',
        type=lambda v: is_float(parser, v),
        help='Optional, (default %(default)s) {0}'.format(ic.CONTOUR_WIDTH_HELP)
    )
    parser.add_argument(
        '--contour_color',
        default=ic.DEFAULT_CONTOUR_COLOR,
        metavar='<color-name>',
        help='Optional, (default %(default)s) {0}'.format(ic.CONTOUR_COLOR_HELP)
    )
    parser.add_argument(
        '-m', '--mask',
        metavar='<image_file_path>',
        default=None,
        type=lambda fp: existing_filepath(parser, fp),
        help='Optional, (default %(default)s) {0}'.format(ic.MASK_HELP)
    )
    parser.add_argument(
        '--step_size',
        default=ic.DEFAULT_STEP_SIZE,
        metavar='"<width>,<height>"',
        type=lambda v: is_tuple_integers(parser, v),
        help='Optional, (default %(default)s) {0}'.format(ic.IMAGE_STEP_HELP)
    )
    parser.add_argument(
        '--relative_scaling',
        default=ic.DEFAULT_RELATIVE_SCALING,
        metavar='<float>',
        type=lambda v: is_float(parser, v),
        help='Optional, (default %(default)s) {0}'.format(ic.RELATIVE_SCALING_HELP)
    )
    parser.add_argument(
        '--prefer_horizontal',
        default=ic.DEFAULT_PREFER_HORIZONTAL,
        metavar='<float>',
        type=lambda v: is_float(parser, v),
        help='Optional, (default %(default)s) {0}'.format(ic.PREFER_HORIZONTAL_HELP)
    )
    parser.add_argument(
        '--margin',
        default=ic.DEFAULT_MARGIN,
        metavar='<number>',
        type=lambda v: is_integer(parser, v),
        help='Optional, (default %(default)s) {0}'.format(ic.MARGIN_HELP)
    )
    parser.add_argument(
        '--mode',
        default=ic.DEFAULT_MODE,
        metavar='{0}'.format('|'.join(ic.MODE_TYPES)),
        type=lambda v: is_one_of_array(parser, v, ic.MODE_TYPES),
        help='Optional, (default %(default)s) {0}'.format(ic.MODE_HELP)
    )
    parser.add_argument(
        '--repeat',
        action='store_true',
        help='Optional, {0}{1}'.format('(default) ' if ic.DEFAULT_REPEAT else '', ic.REPEAT_HELP)
    )
    parser.add_argument('--no-repeat',
        action='store_false',
        dest='repeat',
        help='Optional, {0}{1}'.format('' if ic.DEFAULT_REPEAT else '(default) ', ic.REPEAT_HELP)
    )
    parser.set_defaults(repeat=ic.DEFAULT_REPEAT)
    parser.add_argument(
        '--show',
        action='store_true',
        help='Optional, {0}show resulting image cloud when finished.'.format('(default) ' if DEFAULT_SHOW else '')
    )
    parser.add_argument('--no-show',
        action='store_false',
        dest='show',
        help='Optional, {0}do not show resulting image cloud when finished.'.format('' if DEFAULT_SHOW else '(default) ')
    )
    parser.set_defaults(show=DEFAULT_SHOW)

    args = parser.parse_args(arguments if 0 < len(arguments) else ['-h'])
    return ImageCloudArguments(
        input=args.input,
        output=args.output,
        output_image_format=args.output_image_format,
        normalize_type=args.normalize_type,
        max_image_size=args.max_image_size,
        min_image_size=args.min_image_size,
        cloud_size=args.cloud_size,
        background_color=args.background_color,
        contour_width=args.contour_width,
        contour_color=args.contour_color,
        mask=args.mask,
        step_size=args.step_size,
        relative_scaling=args.relative_scaling,
        prefer_horizontal=args.prefer_horizontal,
        margin=args.margin,
        mode=args.mode,
        repeat=args.repeat,
        show=args.show
    )


if __name__ == '__main__':
    main()