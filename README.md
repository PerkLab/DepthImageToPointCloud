# DepthImageToPointCloud
This repo contains a slicer module for generating point clouds from static or streamed depth images.

Note that depth images can be streamed into 3D Slicer using the [PLUS toolkit](https://plustoolkit.github.io/).

## Determining Intel RealSense Intrinsic Parameters
This module requires the focal length and principle point (x and y coordinates) of the depth camera. To determine these values for the Intel RealSense, you can use the rs-sensor-control.exe tool included in the [Intel RealSense SDK 2.0](https://www.intelrealsense.com/developers/).

### To use rs-sensor-control.exe:
1. Start by [installing](https://www.intelrealsense.com/sdk-2/) the SDK.
2. Navigate to the installation folder, open the "tools" folder and run "rs-sensor-control.exe"(on Windows 10, the full path was "C:\Program Files (x86)\Intel RealSense SDK 2.0\tools\rs-sensor-control.exe").
3. Ensure the camera is connected, and select the correct device number from the first menu.
4. Input 0 for "Stereo Module" from the next menu, then input 2 for "Show stream instrinsics".
5. From the list of stream profiles, select the Depth stream that corresponds with the resolution and framerate you intend to use with the module. 

Note that this module assumes the focal length is identical in the x and y axes.


## Point Cloud Parameters
- **Lower / Upper Depth Threshold**: Limits the maximum / minimum depth values; pixels that fall outside these bounds will not be included in the point cloud.

- **Depth Scaling Factor**: Used to increase or decrease the scale of the resulting point cloud.

- **Point Cloud Density**: Used to modify the proportion of pixels included in the generated point cloud. 
    - Default value is 1, which produces a single point for all pixels in the depth image
    - Increasing this value will decrease the density of the point cloud; this will improve the refresh rate for streaming.