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
            self.open_loops[seq[-1]] = loop
        else:
            if seq[0] == seq[-1]:
                self.closed_loops.append(seq)
            else:
                self.open_loops[seq[0]] = seq
                self.open_loops[seq[-1]] = seq
