# ImageCloud

This tool is used to construct imageclouds from a CSV of weights and image source filepaths.
The idea is similar to a word cloud except with images being scaled instead of words.

## Build/Install

The following bash scripts may be used to clean/build/install (edit locally) this package
- `clean`  deletes all side-effect files from `build`
- `build`  calls `clean` and compiles cython and python code into installable packages
- `install`  calls `build` and does `pip install` of package 
- `uninstall`  does `pip uninstall` of package and then `clean`



## CLI Usage: 
Once installed you will be able to execute scripts defined in the `myproject.toml`

### generate_imagecloud
```
usage: generate_imagecloud [-h] -i <csv_filepath> [-output_directory <output-directory-path>]
                           [-output_image_format blp|bmp|dds|dib|eps|gif|icns|ico|im|jpeg|mpo|msp|pcx|pfm|png|ppm|sgi|webp|xbm]
                           [-show_imagecloud] [-no-show_imagecloud] [-show_imagecloud_reservation_chart]
                           [-no-show_imagecloud_reservation_chart] [-verbose] [-no-verbose] [-log_filepath <log-filepath>]
                           [-cloud_size "<width>,<height>"] [-cloud_expansion_step_size <int>] [-maximize_empty_space]
                           [-no-maximize_empty_space] [-margin <number>] [-min_image_size "<width>,<height>"] [-step_size <int>]
                           [-resize_type NO_RESIZE_TYPE|MAINTAIN_ASPECT_RATIO|MAINTAIN_PERCENTAGE_CHANGE]
                           [-max_image_size "<width>,<height>"]
                           [-mode 1|L|P|RGB|RGBA|CMYK|YCbCr|LAB|HSV|I|F|LA|PA|RGBX|RGBa|La|I;16|I;16L|I;16B|I;16N]
                           [-background_color <color-name>] [-mask <image_file_path>] [-contour_width <float>]
                           [-contour_color <color-name>] [-parallelism <int>]

            Generate an 'ImageCloud' from a csv file indicating image filepath and weight for image.
            

options:
  -h, --help            show this help message and exit
  -i, --input <csv_filepath>
                        Required, csv file for weighted images with following format:
                        "image_filepath","weight"
                        "<full-path-to-image-file-1>",<weight-as-number-1>
                        ...
                        "<full-path-to-image-file-N>",<weight-as-number-N>
                        
  -output_directory <output-directory-path>
                        Optional, output directory for all output
  -output_image_format blp|bmp|dds|dib|eps|gif|icns|ico|im|jpeg|mpo|msp|pcx|pfm|png|ppm|sgi|webp|xbm
                        Optional,(default png) image format: [blp,bmp,dds,dib,eps,gif,icns,ico,im,jpeg,mpo,msp,pcx,pfm,png,ppm,sgi,webp,xbm]
  -show_imagecloud      Optional, (default) show imagecloud.
  -no-show_imagecloud   Optional, do not show mage cloud.
  -show_imagecloud_reservation_chart
                        Optional, show reservation_chart for imagecloud.
  -no-show_imagecloud_reservation_chart
                        Optional, (default) do not show reservation_chart for imagecloud.
  -verbose              Optional, report progress as constructing cloud
  -no-verbose           Optional, (default) report progress as constructing cloud
  -log_filepath <log-filepath>
                        Optional, all output logging will also be written to this logfile
  -cloud_size "<width>,<height>"
                        Optional, (default 400,200) width and height of canvas
  -cloud_expansion_step_size <int>
                        Optional, (default 0) Step size for expanding cloud to fit more images
                        images will be proportionally fit to the original cloud size but may still not get placed to fit in cloud.
                        step > 0 the cloud will expand by this amount in a loop until all images fit into it.
                        step > 1 might speed up computation but give a worse fit.
  -maximize_empty_space
                        Optional maximize images, after generation, to fill surrouding empty space.
  -no-maximize_empty_space
                        Optional (default) maximize images, after generation, to fill surrouding empty space.
  -margin <number>      Optional, (default 1) The gap to allow between images.
  -min_image_size "<width>,<height>"
                        Optional, (default 4,4) Smallest image size to use.
                        Will stop when there is no more room in this size.
  -step_size <int>      Optional, (default 1) Step size for the image. 
                        ste p> 1 might speed up computation
                        but give a worse fit.
  -resize_type NO_RESIZE_TYPE|MAINTAIN_ASPECT_RATIO|MAINTAIN_PERCENTAGE_CHANGE
                        Optional, (default MAINTAIN_ASPECT_RATIO) Image resizing can be done by maintaining aspect ratio (MAINTAIN_ASPECT_RATIO), step/width percent change evenly applied (MAINTAIN_PERCENTAGE_CHANGE), or simply step change (NO_RESIZE_TYPE)
  -max_image_size "<width>,<height>"
                        Optional, (default None) Maximum image size for the largest image.
                        If None, height of the image is used.
  -mode 1|L|P|RGB|RGBA|CMYK|YCbCr|LAB|HSV|I|F|LA|PA|RGBX|RGBa|La|I;16|I;16L|I;16B|I;16N
                        Optional, (default RGBA) Transparent background will be generated when mode is "RGBA" and background_color is None.
  -background_color <color-name>
                        Optional, (default None) Background color for the imagecloud image.
  -mask <image_file_path>
                        Optional, (default None) Image file
                        If not None, gives a binary mask on where to draw words.
                        If mask is not None, width and height will be ignored
                        and the shape of mask will be used instead. 
                        All white (#FF or #FFFFFF) entries will be considered "masked out"
                        while other entries will be free to draw on.
  -contour_width <float>
                        Optional, (default 0) If mask is not None and contour_width > 0, draw the mask contour.
  -contour_color <color-name>
                        Optional, (default black) Mask contour color.
  -parallelism <int>    Optional, (default $(default)s) Experimental, using parallel algorithms to accomplish image-cloud generation.  Value is the number of threads-of-execution to commit to generation.  A value of 1 will execute sequentially (not experimental); uses no parallel algorithms.
```
#### CSV to import
csv file for weighted images with following format:
```csv
"image_filepath","weight"
"<full-path-to-image-file>",<weight-as-number>
```
#### Sample generate script
`sample-generate` is an example of how the `generate_imagecloud` could be used

### layout_imagecloud
```
usage: layout_imagecloud [-h] -i <csv_filepath> [-output_directory <output-directory-path>]
                         [-output_image_format blp|bmp|dds|dib|eps|gif|icns|ico|im|jpeg|mpo|msp|pcx|pfm|png|ppm|sgi|webp|xbm] [-show_imagecloud]
                         [-no-show_imagecloud] [-show_imagecloud_reservation_chart] [-no-show_imagecloud_reservation_chart] [-verbose] [-no-verbose]
                         [-log_filepath <log-filepath>] [-scale <float>] [-maximize_empty_space] [-no-maximize_empty_space]

            Layout and show a generated 'ImageCloud' from its layout csv file
            

options:
  -h, --help            show this help message and exit
  -i, --input <csv_filepath>
                        Required, csv file representing 1 Layout Contour, 1 Layout Canvas and N Layout Items:
                        "layout_max_images","layout_min_image_size_width","layout_min_image_size_height","layout_image_step","layout_resize_type","layout_scale","layout_margin","layout_name","layout_canvas_name","layout_canvas_mode","layout_canvas_background_color","layout_canvas_size_width","layout_canvas_size_height","layout_canvas_occupancy_map_csv_filepath","layout_contour_mask_image_filepath","layout_contour_width","layout_contour_color","layout_item_image_filepath","layout_item_position_x","layout_item_position_y","layout_item_size_width","layout_item_size_height","layout_item_orientation","layout_item_reserved_position_x","layout_item_reserved_position_y","layout_item_reserved_size_width","layout_item_reserved_size_height","layout_item_reservation_no"
                        <integer>,<width>,<height>,<integer>,NO_RESIZE_TYPE|MAINTAIN_ASPECT_RATIO|MAINTAIN_PERCENTAGE_CHANGE,<float>,<image-margin>,<name>,<name>,1|L|P|RGB|RGBA|CMYK|YCbCr|LAB|HSV|I|F|LA|PA|RGBX|RGBa|La|I;16|I;16L|I;16B|I;16N,<empty>|<any-color-name>,<width>,<height>,<csv-filepath-of-occupancy_map>,<empty>|<filepath-of-image-used-as-mask>,<float>,<any-color-name>,<filepath-of-image-to-paste>,<x>,<y>,<width>,<height>,<empty>|FLIP_LEFT_RIGHT|FLIP_TOP_BOTTOM|ROTATE_90|ROTATE_180|ROTATE_270|TRANSPOSE|TRANSVERSE,<x>,<y>,<width>,<height>,<empty>|<reservation_no_in_occupancy_map>
  -output_directory <output-directory-path>
                        Optional, output directory for all output
  -output_image_format blp|bmp|dds|dib|eps|gif|icns|ico|im|jpeg|mpo|msp|pcx|pfm|png|ppm|sgi|webp|xbm
                        Optional,(default png) image format: [blp,bmp,dds,dib,eps,gif,icns,ico,im,jpeg,mpo,msp,pcx,pfm,png,ppm,sgi,webp,xbm]
  -show_imagecloud      Optional, show imagecloud.
  -no-show_imagecloud   Optional, (default) do not show mage cloud.
  -show_imagecloud_reservation_chart
                        Optional, show reservation_chart for imagecloud.
  -no-show_imagecloud_reservation_chart
                        Optional, (default) do not show reservation_chart for imagecloud.
  -verbose              Optional, report progress as constructing cloud
  -no-verbose           Optional, (default) report progress as constructing cloud
  -log_filepath <log-filepath>
                        Optional, all output logging will also be written to this logfile
  -scale <float>        Optional, (default 1.0) scale up/down all images
  -maximize_empty_space
                        Optional maximize images, after generation, to fill surrouding empty space.
  -no-maximize_empty_space
                        Optional (default) maximize images, after generation, to fill surrouding empty space.
  ```
#### CSV to import
csv file representing 1 Layout Contour, 1 Layout Canvas and N Layout Items:
```csv
"layout_max_images","layout_min_image_size_width","layout_min_image_size_height","layout_image_step","layout_resize_type","layout_scale","layout_margin","layout_name","layout_canvas_name","layout_canvas_mode","layout_canvas_background_color","layout_canvas_size_width","layout_canvas_size_height","layout_canvas_occupancy_map_csv_filepath","layout_contour_mask_image_filepath","layout_contour_width","layout_contour_color","layout_item_image_filepath","layout_item_position_x","layout_item_position_y","layout_item_size_width","layout_item_size_height","layout_item_orientation","layout_item_reserved_position_x","layout_item_reserved_position_y","layout_item_reserved_size_width","layout_item_reserved_size_height","layout_item_reservation_no"
<integer>,<width>,<height>,<integer>,NO_RESIZE_TYPE|MAINTAIN_ASPECT_RATIO|MAINTAIN_PERCENTAGE_CHANGE,<float>,<image-margin>,<name>,<name>,1|L|P|RGB|RGBA|CMYK|YCbCr|LAB|HSV|I|F|LA|PA|RGBX|RGBa|La|I;16|I;16L|I;16B|I;16N,<empty>|<any-color-name>,<width>,<height>,<csv-filepath-of-occupancy_map>,<empty>|<filepath-of-image-used-as-mask>,<float>,<any-color-name>,<filepath-of-image-to-paste>,<x>,<y>,<width>,<height>,<empty>|FLIP_LEFT_RIGHT|FLIP_TOP_BOTTOM|ROTATE_90|ROTATE_180|ROTATE_270|TRANSPOSE|TRANSVERSE,<x>,<y>,<width>,<height>,<empty>|<reservation_no_in_occupancy_map>
```
#### Sample layout script
`sample-layout` is an example of how the `layout_imagecloud` could be used. This example builds off the `sample-generate` to operate on its result by maximizing the empty-space, if any, surrounding the images in the image-cloud.

## Images to load
Really any image supported by pillow open is supported.


## References / acknowledgements
- [amueller's wordcloud](https://github.com/amueller/word_cloud)
    - [`wordcloud/wordcloud.py`](https://github.com/amueller/word_cloud/blob/main/wordcloud/wordcloud.py) object implementation especially `generate_from_frequencies()` were used to build this ImageCloud
    - [`wordcloud/query_integral_image.pyx`](https://github.com/amueller/word_cloud/blob/main/wordcloud/query_integral_image.pyx) was copied verbatim and used by this ImageCloud's `IntegratedOccupancyMap` object.