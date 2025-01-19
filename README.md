# ImageCloud

This tool is used to construct image clouds from a CSV of weights and image source filepaths.
The idea is similar to a word cloud except with images being scaled instead of words.

## Build/Install

The following bash scripts may be used to clean/build/install (edit locally) this package
- `clean.sh`  deletes all side-effect files from `build.sh`
- `build.sh`  calls `clean.sh` and compiles cython and python code into installable packages
- `local-install.sh`  calls `build.sh` and does `pip install -e` of package 



## CLI Usage: 
Once installed you will be able to execute scripts defined in the `myproject.toml`

### imagecloud_cli
```
usage: imagecloud_cli [-h] -i <csv_filepath> -o <generated_image_cloud_filepath>
                      [-m <image_file_path>]
                      [--interpolation none|auto|nearest|bilinear|bicubic|spline16|spline36|hanning|hamming|hermite|kaiser|quadric|catrom|gaussian|bessel|mitchell]
                      [--cloud_size <width>,<height>] [--step_size <width>,<height>]
                      [--normalize_type min|max|avg|median] [--max_image_size <width>,<height>]
                      [--min_image_size <width>,<height>] [--background_color <color-name>]
                      [--contour_width <float>] [--contour_color <color-name>]

Generate an 'ImageCloud' from a csv file indicating image filepath and weight for image.

options:
  -h, --help            show this help message and exit
  -i, --input <csv_filepath>
                        Required, csv file with following format: "image_filepath","weight"
                        "<full-path-to-image-file-1>",<weight-as-number-1> ... "<full-path-to-
                        image-file-N>",<weight-as-number-N>
  -o, --output <generated_image_cloud_filepath>
                        Required, output file path for generated image cloud
  -m, --mask <image_file_path>
                        Optional, (default: none) Image file If not None, gives a binary mask on
                        where to draw words. If mask is not None, width and height will be
                        ignored and the shape of mask will be used instead. All white (#FF or
                        #FFFFFF) entries will be considerd "masked out" while other entries will
                        be free to draw on. [This changed in the most recent version!]
  --interpolation none|auto|nearest|bilinear|bicubic|spline16|spline36|hanning|hamming|hermite|kaiser|quadric|catrom|gaussian|bessel|mitchell
                        Optional, interpolation (default: bilinear): [none,auto,nearest,bilinear,
                        bicubic,spline16,spline36,hanning,hamming,hermite,kaiser,quadric,catrom,g
                        aussian,bessel,mitchell]
  --cloud_size <width>,<height>
                        Optional, <width>,<height> width : int (default=400) Width of the canvas.
                        height : int (default=200) Height of the canvas.
  --step_size <width>,<height>
                        <width>,<height> (default=1, 1) Step size for the image. image_step[0] |
                        image_step[1] > 1 might speed up computation but give a worse fit.
  --normalize_type min|max|avg|median
                        normalize images (default: 'max') to the 'max', 'min', 'avg', or
                        'median'] found size
  --max_image_size <width>,<height>
                        <width>,<height> (default=800, 400) Maximum image size for the largest
                        image. If None, height of the image is used.
  --min_image_size <width>,<height>
                        <width>,<height> (default=4, 4) Smallest image size to use. Will stop
                        when there is no more room in this size.
  --background_color <color-name>
                        Optional, (default="white") Background color for the image cloud image.
  --contour_width <float>
                        Optional, (default=0) If mask is not None and contour_width > 0, draw the
                        mask contour.
  --contour_color <color-name>
                        Optional, (default="black") Mask contour color.
```

## CSV to import
```csv
"image_filepath","weight"
"<full-path-to-image-file>",<weight-as-number>
```
## Images to load
Really any image supported by pillow open is supported.


## References / acknowledgements
- [amueller's wordcloud](https://github.com/amueller/word_cloud)
    - [`wordcloud/wordcloud.py`](https://github.com/amueller/word_cloud/blob/main/wordcloud/wordcloud.py) object implementation especially `generate_from_frequencies()` were used to build this ImageCloud
    - [`wordcloud/query_integral_image.pyx`](https://github.com/amueller/word_cloud/blob/main/wordcloud/query_integral_image.pyx) was copied verbatim and used by this ImageCloud's `IntegratedOccupancyMap` object.