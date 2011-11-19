from primitives import *

#knot primitive class,
class KnotPrim(object):
    def __init__(self):
        self.connections = []
        for i in xrange(Directions.POSSIBLE):
            self.connections.append(None)
        self.control_points = []
        
