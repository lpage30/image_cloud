import argparse
import os.path
from .images import (
    load_weights_images,
    normalize_images,
    to_weighted_images,
    CSV_FILE_HELP,
    IMAGE_FORMAT_HELP,
    IMAGE_FORMATS,
    NORMALIZING_TYPE_HELP,
    NORMALIZING_TYPES
)
from .imagecloud import (
    ImageCloud,
    MASK_HELP,
    CLOUD_SIZE_HELP,
    IMAGE_STEP_HELP,
    MAX_IMAGE_SIZE_HELP,
    MIN_IMAGE_SIZE_HELP,
    BACKGROUND_COLOR_HELP,
    CONTOUR_WIDTH_HELP,
    CONTOUR_COLOR_HELP,
    REPEAT_HELP,
    RELATIVE_SCALING_HELP,
    PREFER_HORIZONTAL_HELP,
    MARGIN_HELP,
    MODE_TYPES,
    MODE_HELP
)

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
    if value.isdigit():
        return int(value)
    else:
        parser.error('Invalid value {0} must be a number'.format(value))

def is_float(parser: argparse.ArgumentParser, value: str):
    if value.replace('.','',1).isdigit():
        return float(value)
    else:
        parser.error('Invalid value {0} must be a number'.format(value))

def is_tuple_integers(parser: argparse.ArgumentParser, value: str):
    values = value.split(',')
    result: list[int] = list()
    if 1 < len(values):
        for v in values:
            if v.isnumeric():
                result.append(int(v))
                continue
            else:
                parser.error('Invalid value {0} must be a number'.format(v))
                break
        return tuple(result)
    else:
        parser.error('Invalid value {0} must have more than 1 for size'.format(value))
    

def argument_parser():
    parser = argparse.ArgumentParser(
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
        help='Required, {0}'.format(CSV_FILE_HELP)
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
        default='png',
        metavar='{0}'.format('|'.join(IMAGE_FORMATS)),
        type=lambda v: is_one_of_array(parser, v, IMAGE_FORMATS),
        help='Optional,(default %(default)s) {0}'.format(IMAGE_FORMAT_HELP)
    )
    parser.add_argument(
        '-m', '--mask',
        metavar='<image_file_path>',
        default=None,
        type=lambda fp: existing_filepath(parser, fp),
        help='Optional, (default %(default)s) {0}'.format(MASK_HELP)
    )
    parser.add_argument(
        '--cloud_size',
        default='400,200',
        metavar='"<width>,<height>"',
        type= lambda v: is_tuple_integers(parser, v),
        help='Optional, (default %(default)s) {0}'.format(CLOUD_SIZE_HELP)
    )
    parser.add_argument(
        '--step_size',
        default='1,1',
        metavar='"<width>,<height>"',
        type=lambda v: is_tuple_integers(parser, v),
        help='Optional, (default %(default)s) {0}'.format(IMAGE_STEP_HELP)
    )
    parser.add_argument(
        '--normalize_type',
        default='min',
        metavar='{0}'.format('|'.join(NORMALIZING_TYPES)),
        type=lambda v: is_one_of_array(parser, v, NORMALIZING_TYPES),
        help='Optional, (default %(default)s) {0}'.format(NORMALIZING_TYPE_HELP)
    )
    parser.add_argument(
        '--max_image_size',
        default='800,400',
        metavar='"<width>,<height>"',
        type=lambda v: is_tuple_integers(parser, v),
        help='Optional, (default %(default)s) {0}'.format(MAX_IMAGE_SIZE_HELP)
    )
    parser.add_argument(
        '--min_image_size',
        default='4,4',
        metavar='"<width>,<height>"',
        type=lambda v: is_tuple_integers(parser, v),
        help='Optional, (default %(default)s) {0}'.format(MIN_IMAGE_SIZE_HELP)
    )
    parser.add_argument(
        '--background_color',
        default='white',
        metavar='<color-name>',
        help='Optional, (default %(default)s) {0}'.format(BACKGROUND_COLOR_HELP)
    )
    parser.add_argument(
        '--contour_width',
        default='0',
        metavar='<float>',
        type=lambda v: is_float(parser, v),
        help='Optional, (default %(default)s) {0}'.format(CONTOUR_WIDTH_HELP)
    )
    parser.add_argument(
        '--contour_color',
        default='black',
        metavar='<color-name>',
        help='Optional, (default %(default)s) {0}'.format(CONTOUR_COLOR_HELP)
    )
    parser.add_argument(
        '--repeat',
        action='store_true',
        help='Optional, Enable {0}'.format(REPEAT_HELP)
    )
    parser.add_argument('--no-repeat',
        action='store_false',
        dest='repeat',
        help='Optional, (default) Disable {0}'.format(REPEAT_HELP)
    )
    parser.set_defaults(repeat=False)
    parser.add_argument(
        '--relative_scaling',
        default=None,
        metavar='<float>',
        type=lambda v: is_float(parser, v),
        help='Optional, (default %(default)s) {0}'.format(RELATIVE_SCALING_HELP)
    )
    parser.add_argument(
        '--prefer_horizontal',
        default='0.9',
        metavar='<float>',
        type=lambda v: is_float(parser, v),
        help='Optional, (default %(default)s) {0}'.format(PREFER_HORIZONTAL_HELP)
    )
    parser.add_argument(
        '--margin',
        default='2',
        metavar='<number>',
        type=lambda v: is_integer(parser, v),
        help='Optional, (default %(default)s) {0}'.format(MARGIN_HELP)
    )
    parser.add_argument(
        '--mode',
        default='RGB',
        metavar='{0}'.format('|'.join(MODE_TYPES)),
        type=lambda v: is_one_of_array(parser, v, MODE_TYPES),
        help='Optional, (default %(default)s) {0}'.format(MODE_HELP)
    )
    parser.add_argument(
        '--show',
        action='store_true',
        help='Optional, Enable {0}'.format(REPEAT_HELP)
    )
    parser.add_argument('--no-show',
        action='store_false',
        dest='show',
        help='Optional, (default) Disable {0}'.format(REPEAT_HELP)
    )
    parser.set_defaults(show=False)
    return parser


def main():
    args = argument_parser().parse_args()
    print('Generating ImageCloud based on weights and images from {0} into {1}'.format(args.input, args.output))

    print('loading {0} ...'.format(args.input))
    weights, images = load_weights_images(args.input)
    print('loaded {0} weights and images'.format(len(weights)))

    print('normalizing {0} weights and images using {1} image size...'.format(len(weights), args.normalize_type))
    normalized_images = normalize_images(args.normalize_type, images, reportProgress=print)
    weighted_images = to_weighted_images(weights, normalized_images)

    image_cloud = ImageCloud(
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
    print('generating image cloud from {0} weighted and normalized images'.format(len(weights)))

    image_cloud.generate(weighted_images, reportProgress=print)
    
    print('saving image cloud to {0} as {1} type'.format(args.output, args.output_image_format))
    collage = image_cloud.to_image(reportProgress=print)
    collage.save(args.output, args.output_image_format)
    
    print('completed! {0}'.format(args.output))
    if args.show:
        collage.show(args.output)

if __name__ == "__main__":
    main()

