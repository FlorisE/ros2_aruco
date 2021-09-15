# ros2_aruco

ROS2 Wrapper for OpenCV Aruco Marker Tracking

This package depends on a recent version of OpenCV python bindings:

```
pip install opencv-contrib-python # or pip3
```

## ROS2 API for the ros2_aruco Node

This node locates Aruco AR markers in images and publishes their ids and poses.

Subscriptions:
* `/camera/image_raw` (`sensor_msgs.msg.Image`)
* `/camera/camera_info` (`sensor_msgs.msg.CameraInfo`)

Published Topics:
* `/aruco_poses` (`geometry_msgs.msg.PoseArray`) - Poses of all detected markers (suitable for rviz visualization)
* `/aruco_markers` (`ros2_aruco_interfaces.msg.ArucoMarkers`) - Provides an array of all poses along with the corresponding marker ids

Parameters:
* `marker_size` - size of the markers in meters (default .0625)
* `aruco_dictionary_id` - dictionary that was used to generate markers (default `DICT_5X5_250`)
* `image_topic` - image topic to subscribe to (default `/camera/image_raw`)
* `camera_info_topic` - Camera info topic to subscribe to (default `/camera/camera_info`)
* `camera_frame` - Camera optical frame to use (default to the frame id provided by the camera info message.)
* `dictionary_size` - when using a custom dictionary, the amount of markers in the dictionary (default -1)
* `dictionary_bits` - when using a custom dictionary, the amount of bits per marker (default -1)
* `dictionary_seed` - when using a custom dictionary, the seed that was used to generate the dictionary (default 0)
* `do_corner_refinement` - refine the corners of detected markers, improves accuracy but has a performance cost (default False)
* `corner_refinement_method` - if `do_corner_refinement`, then use this method for the refinement. Options are `CORNER_REFINEMENT_NONE` (default), `CORNER_REFINEMENT_SUBPIX`, `CORNER_REFINEMENT_CONTOUR` and `CORNER_REFINEMENT_APRILTAG`

To use a custom dictionary, use set the parameter `aruco_dictionary_id` to `CUSTOM` and specify `dictionary_size`, `dictionary_bits` and optionally `dictionary_seed` so they match the values used to generate the dictionary.

## Generating Marker Images

```
ros2 run ros2_aruco aruco_generate_marker
```

Pass the `-h` flag for usage information: 

```
usage: aruco_generate_marker [-h] [--id ID] [--size SIZE] [--dictionary]

Generate a .png image of a specified maker.

optional arguments:
  -h, --help     show this help message and exit
  --id ID        Marker id to generate (default: 1)
  --size SIZE    Side length in pixels (default: 200)
  --dictionary   Dictionary to use. Valid options include: DICT_4X4_100,
                 DICT_4X4_1000, DICT_4X4_250, DICT_4X4_50, DICT_5X5_100,
                 DICT_5X5_1000, DICT_5X5_250, DICT_5X5_50, DICT_6X6_100,
                 DICT_6X6_1000, DICT_6X6_250, DICT_6X6_50, DICT_7X7_100,
                 DICT_7X7_1000, DICT_7X7_250, DICT_7X7_50, DICT_ARUCO_ORIGINAL
                 (default: DICT_5X5_250)
```

To generate a custom dictionary, use the following command instead:

```
ros2 run ros2_aruco aruco_generate_custom_dictionary
```

By default this will generate 100 markers with a side length of 200 pixels with 6 bits each, but you will probably want to customize it.

Here you can also pass the `-h` flag for usage information:

```
usage: aruco_generate_custom_dictionary [-h] [--size SIZE] [--num NUM] [--bits BITS] [--seed SEED]

Generates multiple .png images using a customized dictionary.

optional arguments:
  -h, --help   show this help message and exit
  --size SIZE  Side length in pixels (default: 200)
  --num NUM    Amount of markers to be generated (default: 100)
  --bits BITS  Amount of bits to use (default: 6)
  --seed SEED  The seed used to generate the dictionary (default: 0)
```
