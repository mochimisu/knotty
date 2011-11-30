from primitives import *
from OpenGL.GL import *

class Knot(object):
    def __init__(self):
        self.open_loops = {}
        self.closed_loops = []

    def addSequence(self, seq):
        if not seq:
            return

        seq = list(seq)
        if seq[0] in self.open_loops and seq[-1] in self.open_loops:
            loop1 = self.open_loops[seq[0]]
            loop2 = self.open_loops[seq[-1]]
            
            if loop1 == loop2:
                if seq[0] == loop1[0]:
                    seq.reverse()
                loop1.extend(seq[1:])
                self.closed_loops.append(loop1)
                del self.open_loops[seq[0]]
                del self.open_loops[seq[-1]]
            else:
                if loop1[0] == seq[0]:
                    loop1.reverse()
                if loop2[-1] == seq[-1]:
                    loop2.reverse()
                loop1.extend(seq[1:])
                loop1.extend(loop2[1:])
                del self.open_loops[seq[0]]
                del self.open_loops[seq[-1]]
                self.open_loops[loop1[-1]] = loop1
        elif seq[0] in self.open_loops or seq[-1] in self.open_loops:
            if seq[-1] in self.open_loops:
                seq.reverse()
            loop = self.open_loops[seq[0]]
            if loop[0] == seq[0]:
                loop.reverse()
            del self.open_loops[seq[0]]
            loop.extend(seq[1:])
            '''
            if loop[0] == loop[-1]:
                del self.open_loops[loop[0]]
                self.closed_loops.append(loop)
            else:
                self.open_loops[seq[-1]] = loop
            '''
            self.open_loops[seq[-1]] = loop
        else:
            if seq[0] == seq[-1]:
                self.closed_loops.append(seq)
            else:
                self.open_loops[seq[0]] = seq
                self.open_loops[seq[-1]] = seq

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
            
        
