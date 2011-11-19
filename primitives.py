from numpy import *
from algebra import *
from aabb import *

class Directions(object):
    POSSIBLE=6
    POSX = 0
    POSY = 1
    POSZ = 2
    NEGX = 3
    NEGY = 4
    NEGZ = 5

class Voxel(object):
    def __init__(self):
        self.exists = False
        self.connections = []
        for i in xrange(Directions.POSSIBLE):
            self.connections.append(None)
        self.connected = False
        self.pos = array([0,0,0])

class Vertex(object):
    def __init__(self):
        self.position = None
        self.normal = None
        self.face = None
        self.normal_samples = 0

class Face(object):
    def __init__(self):
        self.vertices = []
        self.world_to_object = matrix([ [1,0,0,0],
                                        [0,1,0,0],
                                        [0,0,1,0],
                                        [0,0,0,1] ])
        self.object_to_world = matrix([ [1,0,0,0],
                                        [0,1,0,0],
                                        [0,0,1,0],
                                        [0,0,0,1] ])
        self.normal = None
    def objBoundingBox(self):
        bb = BoundingBox()
        for v in self.vertices:
            bb.addPoint(array(v.position))
        return bb

    def worldBoundingBox(self):
        bb = BoundingBox()
        for v in self.vertices:
            #sigh, fix this later
            bb.addPoint(array(v.position))
            #bb.addPoint(ortho_proj(
            #    self.object_to_world * ortho_extend(v.position,1)))
        return bb

    def center(self):
        #overloaded + does not work in sum()
        sum_vert = reduce(lambda x,y: x+y,
                map(lambda v: v.position, self.vertices))
        return sum_vert/float(3)

    def intersect(self,ray):
        v0 = self.vertices[0].position
        v1 = self.vertices[1].position
        v2 = self.vertices[2].position
        e1 = self.vertices[1].position - self.vertices[0].position
        e2 = self.vertices[2].position - self.vertices[0].position
        p=ray.start
        d=ray.direction

        h = cross(d,e2)
        a = dot(e1,h)
        if a > -0.00001 and a < 0.00001:
            return float("inf")
        f = float(1)/a
        s=p-v0
        u=f*dot(s,h)
        if u<0 or u>1:
            return float("inf")
        q = cross(s,e1)
        v = f*dot(d,q)
        if v<0 or (u+v) > 1:
            return float("inf")
        t = f*dot(e2,q)
        if t<ray.min_t:
            return float("inf")
        return t
     
class Ray(object):
    def __init__(self, start, direction, min_t):
        self.start = start
        self.direction = direction
        self.min_t = min_t
