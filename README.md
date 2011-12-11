# Knotty - Chinese Knot Generator
CS285 Project - Brandon Wang, Andrew Lee

## Requirements
* Python 2.x
* PyOpenGL:
`easy_install PyOpenGL PyOpenGL-accelerate`
* NumPy:
`easy_install numpy`

## How to use
`python knotty.py your_file.obj`
### Typically used options
* Specifications:
  `python knotty.py your file.obj -r [RESOLUTION] -c [CS_SCALE] -z [MAX_DIM]
  * RESOLUTION: Maximum voxel dimension
  * CS_SCALE: Cross section scale/radius
  * MAX_DIM: Maximum dimension size for STL/OBJ output

* Non-well-behaved OBJ's:
  `python knotty.py your_file.obj -b`
  Use `-b` for a slower, more accurate voxelization

## Current Status
###Done
* Initial OpenGL Code:
  * PyOpenGL working
  * Viewport/quaternion rotation working

* Voxelization:

  * "Well-behaved" OBJs
    * Winding Number
    * Parity/XOR

  * All OBJ
    * 3 pass boundary voxels

* Patterning:
  * Up and down control points specified
  * Control points to spline
  * Eulerian path construction (Single thread)

* Polygon:
  * Spline to polygon
  * Watertight polygon
  * Polygon to STL
  * Polygon to OBJ

###Not Done
* Extensions to non-axis-aligned shapes (Triangles, quads)
