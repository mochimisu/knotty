# Knotty - Chinese Knot Generator
CS285 Project - Brandon Wang, Andrew Lee

## Requirements
* Python 2.x
* PyOpenGL:
`easy_install PyOpenGL PyOpenGL-accelerate`
* NumPy:
`easy_install numpy`

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

* Polygon:
  * Spline to polygon
	* Watertight polygon
	* Polygon to STL
  * Polygon to OBJ

###Not Done
* Eulerian path construction (Single thread)
* Extensions to non-axis-aligned shapes (Triangles, quads)
