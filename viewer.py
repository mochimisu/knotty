#not a great example of python but will do

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from numpy import *
from numpy.linalg import *
from objloader import *
from outersurface import *
from bspline import *
from consts import *
import sys
import argparse
import graph

import knots

class Viewport(object):
    def __init__(self):
        self.w = 1
        self.h = 1
        self.mouse_pos = array([0,0])
        self.orientation = identity3D()
        self.mouse_mode = "rotate"
        self.view_knots1 = False
        self.view_surface = False
        self.view_voxels = False
        self.view_triangles = False
        self.view_knots_spline = True
        self.view_knots_polyline = False
        self.view_knots_control = False
        self.view_knots_triangle = False
        self.view_wireframe = False

viewport = Viewport()
#Glut Window #
window = 0
obj_loader = None
outer_surface = None

def keyPressed(*args):
    #Escape key is from the a
    ESCAPE = '\033'
    if args[0] == ESCAPE:
        glutDestroyWindow(window)
        sys.exit()
    elif args[0] == '9':
        viewport.view_wireframe = not viewport.view_wireframe
    elif args[0] == '8':
        viewport.view_knots_triangle = not viewport.view_knots_triangle
    elif args[0] == '7':
        viewport.view_knots_control = not viewport.view_knots_control
    elif args[0] == '6':
        viewport.view_knots_polyline = not viewport.view_knots_polyline
    elif args[0] == '5':
        viewport.view_knots_spline = not viewport.view_knots_spline
    elif args[0] == '4':
        viewport.view_knots1 = not viewport.view_knots1
    elif args[0] == '3':
        viewport.view_surface = not viewport.view_surface
    elif args[0] == '2':
        viewport.view_voxels = not viewport.view_voxels
    elif args[0] == '1':
        viewport.view_triangles = not viewport.view_triangles

def activeMotion(*args):

    new_mouse = array([float(args[0])/float(viewport.w),
        float(args[1])/float(viewport.h)])
    diff = new_mouse - viewport.mouse_pos
    viewport.mouse_pos = new_mouse
    length = norm(diff)
    if length > 0.001:
        if viewport.mouse_mode == "rotate":
            axis = array([diff[1]/length, diff[0]/length, 0])
            viewport.orientation = (viewport.orientation *
                    rotation3D(axis, -180*length))
        elif viewport.mouse_mode == "scale":
            scale_factor = diff[0]+diff[1]
            viewport.orientation = (viewport.orientation *
                    scaling3D(array([1+scale_factor,
                        1+scale_factor,
                        1+scale_factor])))

        #doesn't work correctly
        elif viewport.mouse_mode == "pan":
            viewport.orientation = (viewport.orientation *
                    translation3D(array([diff[0], -diff[1], 0])))

        glutPostRedisplay()

def passiveMotion(*args):
    viewport.mouse_pos = array([float(args[0])/float(viewport.w),
        float(args[1])/float(viewport.h)])

def mousePressed(*args):
    #left click
    if args[0] == 0:
        viewport.mouse_mode = "rotate"
    #middle click
    elif args[0] == 1:
        viewport.mouse_mode = "pan"
    #right click
    elif args[0] == 2:
        viewport.mouse_mode = "scale"

def initGL(w,h):
    glClearColor(0,0,0,0);
    glClearDepth(1);
    glDepthFunc(GL_LESS)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45,float(w)/float(h), 0.1, 100)
    glMatrixMode(GL_MODELVIEW)

def resizeScene(w,h):
    if h == 0:
        h = 1
    glViewport(0,0,w,h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45,float(w)/float(h), 0.1, 100)
    glMatrixMode(GL_MODELVIEW)

def drawScene():
    if viewport.view_wireframe:
        glPolygonMode(GL_FRONT, GL_LINE)
        glPolygonMode(GL_BACK, GL_LINE)
    else:
        glPolygonMode(GL_FRONT, GL_FILL)
        glPolygonMode(GL_BACK, GL_FILL)

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    glLoadIdentity();
    glTranslatef(0,0,-5)

    glMultMatrixd(viewport.orientation)
    glColor4f(1,1,1,1)
    glMaterialfv(GL_FRONT_AND_BACK,
            GL_AMBIENT_AND_DIFFUSE,
            [1.0,1.0,1.0,1.0])

    if viewport.view_voxels:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDisable(GL_DEPTH_TEST)
        obj_loader.drawVoxels()
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
    if viewport.view_triangles:
        obj_loader.drawTriangles()
    if viewport.view_surface:
        outer_surface.drawSurface()
    if viewport.view_knots1:
        outer_surface.drawKnots1()
    if viewport.view_knots_spline:
        outer_surface.drawKnotsSpline()
    if viewport.view_knots_polyline:
        outer_surface.drawKnotsPolyline()
    if viewport.view_knots_control:
        outer_surface.drawKnotsControl()
    if viewport.view_knots_triangle:
        outer_surface.drawKnotsTriangle()

    glutSwapBuffers()

def main():
    global viewport
    global window
    global obj_loader
    global outer_surface

    parser = argparse.ArgumentParser(description="Knotify some OBJs.")
    parser.add_argument("object_file", metavar ="obj", default="teapot.obj",
            help="OBJ or KVOX file")

    parser.add_argument("--xor", dest="use_xor", action="store_const",
            const=True, default=False,
            help="Use XOR instead of Winding Number")

    parser.add_argument("-b", "--boundaries", dest="use_boundaries",
            action="store_const", const=True, default=False,
            help=("Use only boundary voxels in voxelization (more expensive, "+
              "but can handle non-nice objects)"))

    parser.add_argument("-r", "--resolution", dest="resolution",
            nargs="?", type=int, default=50, 
            help="Voxelization resolution")

    parser.add_argument("-s", "--samples", dest="num_samples",
            nargs="?", type=int, default=2,
            help="Number of samples on spline per control point")

    parser.add_argument("-d", "--dont_save_vox", dest="save_vox",
            action="store_const", const=False, default=True,
            help="Don't save voxel cache")

    parser.add_argument("-k", "--dont_save_kos", dest="save_kos",
            action="store_const", const=False, default=True,
            help="Don't save spline cache")

    parser.add_argument("-f", "--force_new_vox", dest="new_vox",
            action="store_const", const=True, default=False,
            help="Force new voxel cache")

    parser.add_argument("-l", "--force_new_kos", dest="new_kos",
            action="store_const", const=True, default=False,
            help="Force new spline cache")

    parser.add_argument("-a", "--supersampling_rate", dest="supersample",
            nargs="?", type=int, default=4,
            help="Voxelization supersampling rate")

    parser.add_argument("-t", "--dont_save_stl", dest="save_stl",
            action="store_const", const=False, default=True,
            help="Don't save STL file")

    parser.add_argument("-j", "--dont_save_obj", dest="save_obj",
            action="store_const", const=False, default=True,
            help="Don't save OBJ file")

    parser.add_argument("-n", "--dont_print_logo", dest="print_logo",
            action="store_const", const=False, default=True,
            help="Hate happiness")

    parser.add_argument("-c", "--cross_section_scale", dest="cs_scale",
            nargs="?", type=float, default=0.1,
            help="Cross section scale")

    parser.add_argument("--width", dest="width",
            nargs="?", type=int, default=640,
            help="Viewport width")

    parser.add_argument("--height", dest="height",
            nargs="?", type=int, default=480,
            help="Viewport height")

    args = parser.parse_args()

    if args.print_logo:
        print KNOTTY_ASCII_ART
    print "CS285 Fa11 Final Project: Knotty"
    print "Brandon Wang and Andrew Lee"
    print "===="

    print "Inside-outside test:",
    if args.use_boundaries:
        print "Boundaries only"
    elif args.use_xor:
        print "XOR"
    else:
        print "Winding Number"
    print "Resolution: "+str(args.resolution)
    print "Cross Section Scale: "+str(args.cs_scale)
    print "Sample Ratio: "+str(args.num_samples)+"x"
    print "Supersampling rate: "+str(args.supersample)+"x"
    print "===="

    viewport.w = args.width
    viewport.h = args.height

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH)
    glutInitWindowSize(viewport.w,viewport.h)
    glutInitWindowPosition(0,0)
    window = glutCreateWindow("Knotty (in progress)")

    split_filename = args.object_file.split(".")
    filename_no_suffix = split_filename[0]
    filename_suffix = split_filename[1]

    obj_loader = ObjLoader()
    obj_loader.use_xor = args.use_xor
    obj_loader.use_boundaries = args.use_boundaries
    obj_loader.supersampling_rate = args.supersample

    outer_surface = OuterSurface(obj_loader)
    outer_surface.num_samples = args.num_samples
    outer_surface.cs_scale = args.cs_scale

    loaded_outer_surface = False
    if filename_suffix == "obj":
        obj_loader.loadObj(args.object_file)
        if (not args.new_vox and
                obj_loader.loadVoxCheckMeta(filename_no_suffix+".kvox",
                    args.resolution)):
            obj_loader.loadVox(filename_no_suffix+".kvox")
            if not args.new_kos:
                loaded_outer_surface = outer_surface.load(filename_no_suffix+
                                                          ".kos", obj_loader)
        else:
            if args.new_vox:
                print "Forcing new voxel cache"
            obj_loader.createAABBTree()
            obj_loader.voxelize(args.resolution)
        if args.save_vox:
            obj_loader.saveVox(filename_no_suffix+".kvox")
    elif filename_suffix == "kvox":
        obj_loader.loadVox(args.object_file)
    elif filename_suffix == "kos":
        loaded_outer_surface = outer_surface.load(filename_no_suffix+".kos")
    else:
        print "Invalid file specified"

    if not loaded_outer_surface:
        print "Generating outer surface"
        outer_surface.updateVoxels()
        outer_surface.generate()
        outer_surface.applyKnots()
        print "Generating bezier curves"
        outer_surface.createBezierCurves()
        if args.save_kos:
            outer_surface.save(filename_no_suffix+".kos")
            print filename_no_suffix+".kos saved successfully!"
        print "Outer surface loaded"
    else:
        obj_loader = outer_surface.obj_loader
        print filename_no_suffix+".kos loaded successfully!"

    if args.save_stl:
        outer_surface.saveStl(filename_no_suffix+"-knot.stl")
    if args.save_obj:
        outer_surface.saveObj(filename_no_suffix+"-knot.obj")

    glutDisplayFunc(drawScene)
    glutIdleFunc(drawScene)
    glutKeyboardFunc(keyPressed)
    glutMotionFunc(activeMotion)
    glutReshapeFunc(resizeScene)
    glutPassiveMotionFunc(passiveMotion)
    glutMouseFunc(mousePressed)

    initGL(viewport.w, viewport.h)
    glEnable(GL_LIGHTING)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1,1,1,1])
    glLightfv(GL_LIGHT0, GL_POSITION, [1, 1, 1, 0])
    glEnable(GL_LIGHT0)
    glEnable(GL_CULL_FACE)

    glLineWidth(2)

    glutMainLoop()

if __name__ == '__main__':
    try:
        GLU_VERSION_1_2
    except:
        print "We require GLU version >= 1.2"
        sys.exit(1)
    main()
