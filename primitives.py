from numpy import *
from algebra import *
from aabb import *

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
            bb.addPoint(v.position)
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
        return sum_vert/3

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

        """
        veca = self.vertices[0].position
        vecb = self.vertices[1].position
        vecc = self.vertices[2].position
        #cast from 4d to 3d
        """
        """
        vecd = ortho_proj(self.world_to_object * array([ray.direction[0],
                                                        ray.direction[1],
                                                        ray.direction[2],
                                                        1]))
        vece = ortho_proj(self.world_to_object *  array([ray.start[0],
                                                         ray.start[1],
                                                         ray.start[2],
                                                         1]))
                                                         """
        """
        vecd = ray.direction
        vece = ray.start

        aminusb = veca - vecb
        aminusc = veca - vecc
        aminuse = veca - vece

        cm = [aminusb, aminusc, vecd]

        eiminushf = (cm[1][1] * cm[2][2]) - (cm[2][1] * cm[1][2])
        gfminusdi = (cm[2][0] * cm[1][2]) - (cm[1][0] * cm[2][2])
        dhminuseg = (cm[1][0] * cm[2][1]) - (cm[1][1] * cm[2][0])

        akminusjb = (cm[0][0] * aminuse[1]) - (aminuse[0] * cm[0][1])
        jcminusal = (aminuse[0] * cm[0][2]) - (cm[0][0] * aminuse[2])
        blminuskc = (cm[0][1] * aminuse[2]) - (aminuse[1] * cm[0][2])

        m = ((cm[0][0] * eiminushf) +
             (cm[0][1] * gfminusdi) + 
             (cm[0][2] * dhminuseg))

        if m == 0:
            print "Error: m=0"
            return float("inf")
        else:
            print "m is ok"

        t = -((cm[1][2] * akminusjb) + 
              (cm[1][1] * jcminusal) +
              (cm[1][0] * blminuskc))/m
        if t < ray.min_t:
            return float("inf")

        gamma = ((cm[2][2] * akminusjb) +
                 (cm[2][1] * jcminusal) +
                 (cm[2][0] * blminuskc))/m
        if gamma < 0 or gamma > 1:
            return float("inf")

        beta = ((aminuse[0] * eiminushf) +
                (aminuse[1] * gfminusdi) +
                (aminuse[2] * dhminuseg))/m
        if beta < 0 or beta > (1 - gamma):
            return float("inf")

        return t
        """

class Ray(object):
    def __init__(self, start, direction, min_t):
        self.start = start
        self.direction = direction
        self.min_t = min_t
