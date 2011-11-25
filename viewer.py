# PyOpenGL test code
# Referencing CS184 Sp11 C++ Framework code:
# http://www-inst.eecs.berkeley.edu/~cs184/sp11/
# not perfect python, but this is just a simple translation to show PyOpenGL
# (extremely quick and dirty)
# will turn into object viewer later

from OpenGL.GL import * 
from OpenGL.GLUT import *
from OpenGL.GLU import *
from numpy import *
from numpy.linalg import *
from objloader import *
from outersurface import *
from bspline import *
import sys
import argparse

class Viewport(object):
    def __init__(self):
        self.w = 1
        self.h = 1
        self.mouse_pos = array([0,0])
        self.orientation = identity3D()
        self.mouse_mode = "rotate"
        self.view_knots1 = True
        self.view_surface = False
        self.view_voxels = False
        self.view_triangles = False
        self.view_bar_connections = False

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
    elif args[0] == '5':
        viewport.view_knots1 = not viewport.view_knots1
    elif args[0] == '4':
        viewport.view_surface = not viewport.view_surface
    elif args[0] == '3':
        viewport.view_bar_connections = not viewport.view_bar_connections
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
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    #example code
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
    if viewport.view_bar_connections:
        obj_loader.drawBarConnections()
    if viewport.view_triangles:
        obj_loader.drawTriangles()
    if viewport.view_surface:
        outer_surface.drawSurface()
    if viewport.view_knots1:
        outer_surface.drawKnots1()

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
        help=("Use only boundary voxels in voxelization (more expensive, but"+ 
              " can handle non-nice objects)"))
    parser.add_argument("-r", "--resolution", dest="resolution",
            nargs="?", type=int, default=50, help="Voxelization resolution") 
    parser.add_argument("-d", "--dont_save_vox", dest="save_vox",
            action="store_const", const=False, default=True)
    parser.add_argument("-f", "--force_new_vox", dest="new_vox",
            action="store_const", const=True, default=False)
    parser.add_argument("--width", dest="width",
            nargs="?", type=int, default=640, help="Viewport width")
    parser.add_argument("--height", dest="height",
            nargs="?", type=int, default=480, help="Viewport height")
    args = parser.parse_args()

    print "Inside-outside test:",
    if args.use_boundaries:
        print "Boundaries only"
    elif args.use_xor:
        print "XOR"
    else:
        print "Winding Number"

    print "Resolution: "+str(args.resolution)

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
    if filename_suffix == "obj":
        obj_loader.loadObj(args.object_file)
        if (not args.new_vox and 
                obj_loader.loadVoxCheckMeta(filename_no_suffix+".kvox", 
                    args.resolution)):
            obj_loader.loadVox(filename_no_suffix+".kvox")
        else:
            if args.new_vox:
                print "Forcing new voxel cache"
            obj_loader.createAABBTree()
            obj_loader.voxelize(args.resolution)
        if args.save_vox:
            obj_loader.saveVox(filename_no_suffix+".kvox")
    elif filename_suffix == "kvox":
        obj_loader.loadVox(args.object_file)
    else:
        print "Invalid file specified"
    outer_surface = OuterSurface(obj_loader)
    outer_surface.generate()
    

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
    
    glutMainLoop()

if __name__ == '__main__':
    try:
        GLU_VERSION_1_2
    except:
        print "We require GLU version >= 1.2"
        sys.exit(1)
    main()
