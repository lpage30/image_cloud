# ImageCloud

This tool is used to construct image clouds from a CSV of weights and image source filepaths.
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
usage: generate_imagecloud [-h] -i <csv_filepath> [-output_image_filepath <generated_image_cloud_image_filepath>]
                           [-output_layout_dirpath <generated_image_cloud_layout_directory-path>]
                           [-output_image_format blp|bmp|dds|dib|eps|gif|icns|ico|im|jpeg|mpo|msp|pcx|pfm|png|ppm|sgi|webp|xbm]
                           [-cloud_size "<width>,<height>"] [-min_image_size "<width>,<height>"] [-max_image_size "<width>,<height>"]
                           [-background_color <color-name>] [-contour_width <float>] [-contour_color <color-name>] [-mask <image_file_path>]
                           [-step_size <int>] [-cloud_expansion_step_size <int>] [-maintain_aspect_ratio] [-no-maintain_aspect_ratio]
                           [-prefer_horizontal <float>] [-margin <number>]
                           [-mode 1|L|P|RGB|RGBA|CMYK|YCbCr|LAB|HSV|I|F|LA|PA|RGBX|RGBa|La|I;16|I;16L|I;16B|I;16N] [-maximize_empty_space]
                           [-no-maximize_empty_space] [-show] [-no-show] [-verbose] [-no-verbose]

            Generate an 'ImageCloud' from a csv file indicating image filepath and weight for image.
            

options:
  -h, --help            show this help message and exit
  -i, --input <csv_filepath>
                        Required, csv file for weighted images with following format:
                        "image_filepath","weight"
                        "<full-path-to-image-file-1>",<weight-as-number-1>
                        ...
                        "<full-path-to-image-file-N>",<weight-as-number-N>
                        
  -output_image_filepath <generated_image_cloud_image_filepath>
                        Optional, output file path for generated image cloud image
  -output_layout_dirpath <generated_image_cloud_layout_directory-path>
                        Optional, output directory path into which generated image cloud layout will be written
  -output_image_format blp|bmp|dds|dib|eps|gif|icns|ico|im|jpeg|mpo|msp|pcx|pfm|png|ppm|sgi|webp|xbm
                        Optional,(default png) image format: [blp,bmp,dds,dib,eps,gif,icns,ico,im,jpeg,mpo,msp,pcx,pfm,png,ppm,sgi,webp,xbm]
  -cloud_size "<width>,<height>"
                        Optional, (default 400,200) width and height of canvas
  -min_image_size "<width>,<height>"
                        Optional, (default 4,4) Smallest image size to use.
                        Will stop when there is no more room in this size.
  -max_image_size "<width>,<height>"
                        Optional, (default None) Maximum image size for the largest image.
                        If None, height of the image is used.
  -background_color <color-name>
                        Optional, (default None) Background color for the image cloud image.
  -contour_width <float>
                        Optional, (default 0) If mask is not None and contour_width > 0, draw the mask contour.
  -contour_color <color-name>
                        Optional, (default black) Mask contour color.
  -mask <image_file_path>
                        Optional, (default None) Image file
                        If not None, gives a binary mask on where to draw words.
                        If mask is not None, width and height will be ignored
                        and the shape of mask will be used instead. 
                        All white (#FF or #FFFFFF) entries will be considered "masked out"
                        while other entries will be free to draw on.
  -step_size <int>      Optional, (default 1) Step size for the image. 
                        ste p> 1 might speed up computation
                        but give a worse fit.
  -cloud_expansion_step_size <int>
                        Optional, (default 0) Step size for expanding cloud to fit more images
                        images will be proportionally fit to the original cloud size but may still not get placed to fit in cloud.
                        step > 0 the cloud will expand by this amount in a loop until all images fit into it.
                        step > 1 might speed up computation but give a worse fit.
  -maintain_aspect_ratio
                        Optional, (default) resize of images to fit will maintain aspect ratio
  -no-maintain_aspect_ratio
                        Optional, resize of images to fit will maintain aspect ratio
  -prefer_horizontal <float>
                        Optional, (default 0.9) The ratio of times to try horizontal fitting as opposed to vertical.
                        If prefer_horizontal < 1, the algorithm will try rotating the image if it doesn't fit. 
  -margin <number>      Optional, (default 1) The gap to allow between images.
  -mode 1|L|P|RGB|RGBA|CMYK|YCbCr|LAB|HSV|I|F|LA|PA|RGBX|RGBa|La|I;16|I;16L|I;16B|I;16N
                        Optional, (default RGBA) Transparent background will be generated when mode is "RGBA" and background_color is None.
  -maximize_empty_space
                        Optional maximize images, after generation, to fill surrouding empty space.
  -no-maximize_empty_space
                        Optional (default) maximize images, after generation, to fill surrouding empty space.
  -show                 Optional, (default) show resulting image cloud when finished.
  -no-show              Optional, do not show resulting image cloud when finished.
  -verbose              Optional, report progress as constructing cloud
  -no-verbose           Optional, (default) report progress as constructing cloud
```
#### CSV to import
csv file for weighted images with following format:
```csv
"image_filepath","weight"
"<full-path-to-image-file>",<weight-as-number>
```
### layout_imagecloud
```
usage: layout_imagecloud [-h] -i <csv_filepath> [-scale <float>] [-save_imagecloud_filepath <filepath_for_save_imagecloud]
                         [-save_reservation_chart_filepath <filepath_for_save_imagecloud_reservation_chart]
                         [-save_imagecloud_format blp|bmp|dds|dib|eps|gif|icns|ico|im|jpeg|mpo|msp|pcx|pfm|png|ppm|sgi|webp|xbm]
                         [-maximize_empty_space] [-no-maximize_empty_space] [-show_imagecloud] [-no-show_imagecloud]
                         [-show_imagecloud_reservation_chart] [-no-show_image_cloudreservation_chart] [-verbose] [-no-verbose]

            Layout and show a generated 'ImageCloud' from its layout csv file
            

options:
  -h, --help            show this help message and exit
  -i, --input <csv_filepath>
                        Required, csv file representing 1 Layout Contour, 1 Layout Canvas and N Layout Items:
                        "layout_max_images","layout_min_image_size_width","layout_min_image_size_height","layout_image_step","layout_maintain_aspect_ratio","layout_scale","layout_margin_prefer_horizontal","layout_margin","layout_canvas_name","layout_canvas_mode","layout_canvas_background_color","layout_canvas_size_width","layout_canvas_size_height","layout_canvas_occupancy_map_csv_filepath","layout_contour_mask_image_filepath","layout_contour_width","layout_contour_color","layout_item_image_filepath","layout_item_position_x","layout_item_position_y","layout_item_size_width","layout_item_size_height","layout_item_orientation","layout_item_reserved_position_x","layout_item_reserved_position_y","layout_item_reserved_size_width","layout_item_reserved_size_height","layout_item_reservation_no"
                        <integer>,<width>,<height>,<integer>,True|False,<float>,<float>,<image-margin>,<name>,1|L|P|RGB|RGBA|CMYK|YCbCr|LAB|HSV|I|F|LA|PA|RGBX|RGBa|La|I;16|I;16L|I;16B|I;16N,<empty>|<any-color-name>,<width>,<height>,<csv-filepath-of-occupancy_map>,<empty>|<filepath-of-image-used-as-mask>,<float>,<any-color-name>,<filepath-of-image-to-paste>,<x>,<y>,<width>,<height>,<empty>|FLIP_LEFT_RIGHT|FLIP_TOP_BOTTOM|ROTATE_90|ROTATE_180|ROTATE_270|TRANSPOSE|TRANSVERSE,<x>,<y>,<width>,<height>,<empty>|<reservation_no_in_occupancy_map>
  -scale <float>        Optional, (default 1.0) scale up/down all images
  -save_imagecloud_filepath <filepath_for_save_imagecloud
                        Optional, filepath to save imagecloud
  -save_reservation_chart_filepath <filepath_for_save_imagecloud_reservation_chart
                        Optional, filepath to save imagecloud reservation_chart with legend
  -save_imagecloud_format blp|bmp|dds|dib|eps|gif|icns|ico|im|jpeg|mpo|msp|pcx|pfm|png|ppm|sgi|webp|xbm
                        Optional,(default png) image format: [blp,bmp,dds,dib,eps,gif,icns,ico,im,jpeg,mpo,msp,pcx,pfm,png,ppm,sgi,webp,xbm]
  -maximize_empty_space
                        Optional maximize images, after generation, to fill surrouding empty space.
  -no-maximize_empty_space
                        Optional (default) maximize images, after generation, to fill surrouding empty space.
  -show_imagecloud      Optional, show image cloud.
  -no-show_imagecloud   Optional, (default) do not show mage cloud.
  -show_imagecloud_reservation_chart
                        Optional, show reservation_chart for image cloud.
  -no-show_image_cloudreservation_chart
                        Optional, (default) do not show reservation_chart for image cloud.
  -verbose              Optional, report progress as constructing cloud
  -no-verbose           Optional, (default) report progress as constructing cloud
  ```
#### CSV to import
csv file representing 1 Layout Contour, 1 Layout Canvas and N Layout Items:
```csv

"layout_max_images","layout_min_image_size_width","layout_min_image_size_height","layout_image_step","layout_maintain_aspect_ratio","layout_scale","layout_margin_prefer_horizontal","layout_margin","layout_canvas_name","layout_canvas_mode","layout_canvas_background_color","layout_canvas_size_width","layout_canvas_size_height","layout_canvas_occupancy_map_csv_filepath","layout_contour_mask_image_filepath","layout_contour_width","layout_contour_color","layout_item_image_filepath","layout_item_position_x","layout_item_position_y","layout_item_size_width","layout_item_size_height","layout_item_orientation","layout_item_reserved_position_x","layout_item_reserved_position_y","layout_item_reserved_size_width","layout_item_reserved_size_height","layout_item_reservation_no"
<integer>,<width>,<height>,<integer>,True|False,<float>,<float>,<image-margin>,<name>,1|L|P|RGB|RGBA|CMYK|YCbCr|LAB|HSV|I|F|LA|PA|RGBX|RGBa|La|I;16|I;16L|I;16B|I;16N,<empty>|<any-color-name>,<width>,<height>,<csv-filepath-of-occupancy_map>,<empty>|<filepath-of-image-used-as-mask>,<float>,<any-color-name>,<filepath-of-image-to-paste>,<x>,<y>,<width>,<height>,<empty>|FLIP_LEFT_RIGHT|FLIP_TOP_BOTTOM|ROTATE_90|ROTATE_180|ROTATE_270|TRANSPOSE|TRANSVERSE,<x>,<y>,<width>,<height>,<empty>|<reservation_no_in_occupancy_map>
```

## Images to load
Really any image supported by pillow open is supported.


## References / acknowledgements
- [amueller's wordcloud](https://github.com/amueller/word_cloud)
    - [`wordcloud/wordcloud.py`](https://github.com/amueller/word_cloud/blob/main/wordcloud/wordcloud.py) object implementation especially `generate_from_frequencies()` were used to build this ImageCloud
    - [`wordcloud/query_integral_image.pyx`](https://github.com/amueller/word_cloud/blob/main/wordcloud/query_integral_image.pyx) was copied verbatim and used by this ImageCloud's `IntegratedOccupancyMap` object.