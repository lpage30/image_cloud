import argparse
import os.path
from .weightedloadedimages import WeightedLoadedImages, CSV_FILE_HELP
from .loadedimage import LoadedImage, INTERPOLATION_TYPES, INTERPOLATION_HELP
from .imagecloud import ImageCloud, MASK_HELP, CLOUD_SIZE_HELP, IMAGE_STEP_HELP, MAX_IMAGE_SIZE_HELP, MIN_IMAGE_SIZE_HELP, BACKGROUND_COLOR_HELP, CONTOUR_WIDTH_HELP, CONTOUR_COLOR_HELP

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
    if value.isnumeric():
        return int(value)
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
        '-m', '--mask',
        metavar='<image_file_path>',
        default=None,
        type=lambda fp: existing_filepath(parser, fp),
        help='Optional, {0}'.format(MASK_HELP)
    )
    parser.add_argument(
        '--interpolation',
        default=None,
        metavar='{0}'.format('|'.join(INTERPOLATION_TYPES)),
        type=lambda v: is_one_of_array(parser, v, INTERPOLATION_TYPES),
        help='Optional, {0}'.format(INTERPOLATION_HELP)
    )
    parser.add_argument(
        '--cloud_size',
        default=None,
        metavar='"<width>,<height>"',
        type= lambda v: is_tuple_integers(parser, v),
        help='Optional, {0}'.format(CLOUD_SIZE_HELP)
    )
    parser.add_argument(
        '--step_size',
        default=None,
        metavar='"<width>,<height>"',
        type=lambda v: is_tuple_integers(parser, v),
        help=IMAGE_STEP_HELP
    )
    parser.add_argument(
        '--normalize_type',
        default='max',
        metavar='min|max|avg|median',
        type=lambda v: v if v in ['max', 'min', 'avg', 'median'] else parser.error('Invalid value {0} one of max or min'.format(v)),
        help='normalize images (default: \'max\') to the \'max\', \'min\', \'avg\', or \'median\'] found size'
    )
    parser.add_argument(
        '--max_image_size',
        default=None,
        metavar='"<width>,<height>"',
        type=lambda v: is_tuple_integers(parser, v),
        help=MAX_IMAGE_SIZE_HELP
    )
    parser.add_argument(
        '--min_image_size',
        default=None,
        metavar='"<width>,<height>"',
        type=lambda v: is_tuple_integers(parser, v),
        help=MIN_IMAGE_SIZE_HELP
    )
    parser.add_argument(
        '--background_color',
        default=None,
        metavar='<color-name>',
        help='Optional, {0}'.format(BACKGROUND_COLOR_HELP)
    )
    parser.add_argument(
        '--contour_width',
        default=None,
        metavar='<float>',
        type=lambda v: is_tuple_integers(parser, v),
        help='Optional, {0}'.format(CONTOUR_WIDTH_HELP)
    )
    parser.add_argument(
        '--contour_color',
        default=None,
        metavar='<color-name>',
        help='Optional, {0}'.format(CONTOUR_COLOR_HELP)
    )
    return parser

def main():
    args = argument_parser().parse_args()
    weighted_images = WeightedLoadedImages.load(args.input)
    image_cloud = ImageCloud(
        mask=args.mask,
        size=args.cloud_size,
        background_color=args.background_color,
        max_image_size=args.max_image_size,
        min_image_size=args.min_image_size,
        image_step=args.step_size,
        contour_width=args.contour_width,
        contour_color=args.contour_color
    )
    cloud_image: LoadedImage = LoadedImage()
    match args.normalize_type:
        case 'min':
            normalized_size = weighted_images.min_image_size()
        case 'avg':
            normalized_size = weighted_images.avg_image_size()
        case 'median':
            normalized_size = weighted_images.median_image_size()
        case _:
            normalized_size = weighted_images.max_image_size()
    
    weighted_images.set_image_sizes(normalized_size)
    image_cloud.generate(weighted_images.to_weighted_image_array())
    
    cloud_image.set_image(image_cloud.to_image(), args.output)
    cloud_image.save()
    
    cloud_image.show(interpolation=args.interpolation)
    
            
            



if __name__ == "__main__":
    main()

