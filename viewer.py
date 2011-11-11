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
import sys

class Viewport(object):
    def __init__(self):
        self.mousePos = array([0,0,0])
        self.w = 1
        self.h = 1
        self.mousePos = array([0,0])
        self.orientation =  matrix([[1,0,0,0],
                             [0,1,0,0],
                             [0,0,1,0],
                             [0,0,0,1]])

viewport = Viewport()
#Glut Window #
window = 0 

def keyPressed(*args):
    #Escape key is from the a
    ESCAPE = '\033'
    if args[0] == ESCAPE:
        glutDestroyWindow(window)
        sys.exit()

def activeMotion(*args):
    def rotation3D(axis, degree):
        angleRad = degree * pi / 180.0
        c = cos(angleRad)
        s = sin(angleRad)
        t = 1.0 - c
        axis = axis / norm(axis)
        return matrix([ [t*axis[0]*axis[0]+c, 
                  t*axis[0]*axis[1]-s*axis[2],
                  t*axis[0]*axis[2]+s*axis[1],
                  0],
                 [t*axis[0]*axis[1]+s*axis[2],
                  t*axis[1]*axis[1]+c,
                  t*axis[1]*axis[2]-s*axis[0],
                  0],
                 [t*axis[0]*axis[2]-s*axis[1],
                  t*axis[1]*axis[2]+s*axis[0],
                  t*axis[2]*axis[2]+c,
                  0],
                 [0,0,0,1] ])

    newMouse = array([float(args[0])/float(viewport.w), 
        float(args[1])/float(viewport.h)])
    diff = newMouse - viewport.mousePos
    viewport.mousePos = newMouse
    length = norm(diff)
    if length > 0.001:
        axis = array([diff[1]/length, diff[0]/length, 0])
        viewport.orientation = (viewport.orientation * 
                rotation3D(axis, -180*length))
        glutPostRedisplay()

def passiveMotion(*args):
    viewport.mousePos = array([float(args[0])/float(viewport.w),
        float(args[1])/float(viewport.h)])

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

    #from NeHe
    glBegin(GL_TRIANGLES) # Start Drawing The Pyramid
    glColor3f(1,0,0)			# Red
    glVertex3f(0,1,0)		# Top Of Triangle (Front)
    glColor3f(0,1,0)			# Green
    glVertex3f(-1,-1,1)		# Left Of Triangle (Front)
    glColor3f(0,0,1)			# Blue
    glVertex3f(1,-1,1)

    glColor3f(1,0,0)			# Red
    glVertex3f(0,1,0)		# Top Of Triangle (Right)
    glColor3f(0,0,1)			# Blue
    glVertex3f(1,-1,1)		# Left Of Triangle (Right)
    glColor3f(0,1,0)			# Green
    glVertex3f(1,-1,-1)		# Right 

    glColor3f(1,0,0)			# Red
    glVertex3f(0,1,0)		# Top Of Triangle (Back)
    glColor3f(0,1,0)			# Green
    glVertex3f(1,-1,-1)		# Left Of Triangle (Back)
    glColor3f(0,0,1)			# Blue
    glVertex3f(-1,-1,-1)		# Right Of 


    glColor3f(1,0,0)			# Red
    glVertex3f(0,1,0)		# Top Of Triangle (Left)
    glColor3f(0,0,1)			# Blue
    glVertex3f(-1,-1,-1)		# Left Of Triangle (Left)
    glColor3f(0,1,0)			# Green
    glVertex3f(-1,-1,1)		# Right Of Triangle (Left)
    glEnd()	

    glutSwapBuffers()

def main():
    global viewport
    global window
    viewport.w = 640
    viewport.h = 480

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH)
    glutInitWindowSize(viewport.w,viewport.h)
    glutInitWindowPosition(0,0)
    window = glutCreateWindow("PyOpenGL test")

    glutDisplayFunc(drawScene)
    glutIdleFunc(drawScene)
    glutKeyboardFunc(keyPressed)
    glutMotionFunc(activeMotion)
    glutPassiveMotionFunc(passiveMotion)

    initGL(viewport.w, viewport.h)
    
    glutMainLoop()

if __name__ == '__main__':
    try:
        GLU_VERSION_1_2
    except:
        print "We require GLU version >= 1.2"
        sys.exit(1)
    main()
