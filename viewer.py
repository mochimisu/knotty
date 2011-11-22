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
import sys
import argparse

class Viewport(object):
    def __init__(self):
        self.w = 1
        self.h = 1
        self.mouse_pos = array([0,0])
        self.orientation = identity3D()
        self.mouse_mode = "rotate"
        self.view_surface = False
        self.view_voxels = True
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


    glutSwapBuffers()

def main():
    global viewport
    global window
    global obj_loader
    global outer_surface
    
    parser = argparse.ArgumentParser(description="Knotify some OBJs.")
    parser.add_argument("object_file", metavar ="obj", default="teapot.obj")
    parser.add_argument("--xor", dest="use_xor", action="store_const",
            const=True, default=False, 
            help="Use XOR instead of Winding Number")
    args = parser.parse_args()

    print "Inside-outside test: ",
    if args.use_xor:
        print "XOR"
    else:
        print "Winding Number"

    viewport.w = 640
    viewport.h = 480

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH)
    glutInitWindowSize(viewport.w,viewport.h)
    glutInitWindowPosition(0,0)
    window = glutCreateWindow("Knotty (in progress)")

    obj_loader = ObjLoader()
    obj_loader.use_xor = args.use_xor
    obj_loader.load(args.object_file)
    obj_loader.voxelize(50)
    outer_surface = OuterSurface(obj_loader)
    outer_surface.generate()

    glutDisplayFunc(drawScene)
    glutIdleFunc(drawScene)
    glutKeyboardFunc(keyPressed)
    glutMotionFunc(activeMotion)
    glutPassiveMotionFunc(passiveMotion)
    glutMouseFunc(mousePressed)

    initGL(viewport.w, viewport.h)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1,1,1,1])
    
    glutMainLoop()

if __name__ == '__main__':
    try:
        GLU_VERSION_1_2
    except:
        print "We require GLU version >= 1.2"
        sys.exit(1)
    main()
