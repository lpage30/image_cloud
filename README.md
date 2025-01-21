[!WARNING]

This Package is PURELY experimental and untested. This warning will be removed once this testing has been completed

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
                      [--output_image_format blp|bmp|dds|dib|eps|gif|icns|ico|im|jpeg|mpo|msp|pcx|pfm|png|ppm|sgi|webp|xbm] [-m <image_file_path>]
                      [--cloud_size "<width>,<height>"] [--step_size "<width>,<height>"] [--normalize_type min|max|avg|median]
                      [--max_image_size "<width>,<height>"] [--min_image_size "<width>,<height>"] [--background_color <color-name>]
                      [--contour_width <float>] [--contour_color <color-name>] [--repeat] [--no-repeat] [--relative_scaling <float>]
                      [--prefer_horizontal <float>] [--margin <number>]
                      [--mode 1|L|P|RGB|RGBA|CMYK|YCbCr|LAB|HSV|I|F|LA|PA|RGBX|RGBa|La|I;16|I;16L|I;16B|I;16N] [--show] [--no-show]

Generate an 'ImageCloud' from a csv file indicating image filepath and weight for image.

options:
  -h, --help            show this help message and exit
  -i, --input <csv_filepath>
                        Required, csv file with following format: "image_filepath","weight" "<full-path-to-image-file-1>",<weight-as-number-1> ...
                        "<full-path-to-image-file-N>",<weight-as-number-N>
  -o, --output <generated_image_cloud_filepath>
                        Required, output file path for generated image cloud
  --output_image_format blp|bmp|dds|dib|eps|gif|icns|ico|im|jpeg|mpo|msp|pcx|pfm|png|ppm|sgi|webp|xbm
                        Optional,(default png) image format: [blp,bmp,dds,dib,eps,gif,icns,ico,im,jpeg,mpo,msp,pcx,pfm,png,ppm,sgi,webp,xbm]
  -m, --mask <image_file_path>
                        Optional, (default None) Image file If not None, gives a binary mask on where to draw words. If mask is not None, width and
                        height will be ignored and the shape of mask will be used instead. All white (#FF or #FFFFFF) entries will be considerd
                        "masked out" while other entries will be free to draw on. [This changed in the most recent version!]
  --cloud_size "<width>,<height>"
                        Optional, (default 400,200) width and height of canvas
  --step_size "<width>,<height>"
                        Optional, (default 1,1) Step size for the image. image_step[0] | image_step[1] > 1 might speed up computation but give a
                        worse fit.
  --normalize_type min|max|avg|median
                        Optional, (default min) type of normalization for images: [min,max,avg,median] of all loaded images
  --max_image_size "<width>,<height>"
                        Optional, (default 800,400) Maximum image size for the largest image. If None, height of the image is used.
  --min_image_size "<width>,<height>"
                        Optional, (default 4,4) Smallest image size to use. Will stop when there is no more room in this size.
  --background_color <color-name>
                        Optional, (default white) Background color for the image cloud image.
  --contour_width <float>
                        Optional, (default 0) If mask is not None and contour_width > 0, draw the mask contour.
  --contour_color <color-name>
                        Optional, (default black) Mask contour color.
  --repeat              Optional, Enable Whether to repeat images until max_images or min_image_size is reached.
  --no-repeat           Optional, (default) Disable Whether to repeat images until max_images or min_image_size is reached.
  --relative_scaling <float>
                        Optional, (default None) Importance of relative image frequencies for font-size. With relative_scaling=0, only image-ranks
                        are considered. With relative_scaling=1, a image that is twice as frequent will have twice the size. If you want to consider
                        the image frequencies and not only their rank, relative_scaling around .5 often looks good. default: it will be set to 0.5
                        unless repeat is true, in which case it will be set to 0.
  --prefer_horizontal <float>
                        Optional, (default 0.9) The ratio of times to try horizontal fitting as opposed to vertical. If prefer_horizontal < 1, the
                        algorithm will try rotating the word if it doesn't fit. (There is currently no built-in way to get only vertical words.)
  --margin <number>     Optional, (default 2) The gap to allow between images.
  --mode 1|L|P|RGB|RGBA|CMYK|YCbCr|LAB|HSV|I|F|LA|PA|RGBX|RGBa|La|I;16|I;16L|I;16B|I;16N
                        Optional, (default RGB) Transparent background will be generated when mode is "RGBA" and background_color is None.'
  --show                Optional, Enable Whether to repeat images until max_images or min_image_size is reached.
  --no-show             Optional, (default) Disable Whether to repeat images until max_images or min_image_size is reached.
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