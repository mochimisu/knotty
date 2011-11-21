from primitives import *
from OpenGL.GL import *

#knot primitive class,
class KnotPrim(object):
    def __init__(self):
        self.connections = []
        self.pos = array([0,0,0])
        for i in xrange(Directions.POSSIBLE):
            self.connections.append(None)
    def valence(self):
        return len(self.connections)
    def draw(self,center):
        print "unimplemented"

class BarKnot(KnotPrim):
    def draw(self,center,radius):
        glBegin(GL_LINES)
        for d in xrange(Directions.POSSIBLE):
            if self.connections[d] is not None:
                if d == Directions.POSX:
                    glVertex3f(center[0], center[1], center[2])
                    glVertex3f(center[0]+radius, center[1], center[2])
                elif d == Directions.POSY:
                    glVertex3f(center[0], center[1], center[2])
                    glVertex3f(center[0], center[1]+radius, center[2])
                elif d == Directions.POSZ:
                    glVertex3f(center[0], center[1], center[2])
                    glVertex3f(center[0], center[1], center[2]+radius)
                elif d == Directions.NEGX:
                    glVertex3f(center[0], center[1], center[2])
                    glVertex3f(center[0]-radius, center[1], center[2])
                elif d == Directions.NEGY:
                    glVertex3f(center[0], center[1], center[2])
                    glVertex3f(center[0], center[1]-radius, center[2])
                elif d == Directions.NEGZ:
                    glVertex3f(center[0], center[1], center[2])
                    glVertex3f(center[0], center[1], center[2]-radius)
        glEnd()
            
        
