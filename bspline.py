from OpenGL.GL import *
from numpy import *
from consts import *

def lerp(a, b, t):
    return (1-t)*a + t*b

def dist2(a,b):
    assert(len(a) == len(b))
    res = 0.0
    for i in xrange(len(a)):
        minus = a[i]-b[i]
        res += minus*minus
    return minus

class BSpline(object):
    def __init__(self,obj_loader):
        self.control_points = []
        self.sweep_shape = []
        self.polygon = []
        self.polyline = []
        self.global_twist = 0
        self.global_azimuth = 0
        self.num_samples = 20
        self.closed = False

        #not sure i like this, maybe keep drawlist id's separate...
        self.obj_id = obj_loader.obj_id

        #cubic bezier
        self.degree = 3

    def sample(self, t):
        if len(self.control_points) == 0:
            return

        #Range 0..1
        if t > 1 or t < 0:
            t = t%1
        #adjust degree down as needed to get a curve, if too few control points
        num_control_points = len(self.control_points)
        if self.closed:
            num_control_points += self.degree

        #rescale t
        t = (1-t)*self.degree + t*num_control_points

        #list of bases
        bases = []
        k = int(t)

        for i in xrange(0,self.degree+1):
            bases.append(self.control_points[(k-self.degree+i) % 
                len(self.control_points)])

        #de casteljau
        for power in xrange(1,self.degree+1):
            for i in xrange(self.degree-power+1):
                knot = k - self.degree + power + i
                u_i = float(knot)
                u_ipr = float(knot + self.degree - power + 1)
                a = (t - u_i) / (u_ipr - u_i)
                lerped_pos = lerp(bases[i], bases[i+1], a)
                bases[i] = lerped_pos

        return bases[0]

    def generatePolyline(self):
        if self.num_samples == 0:
            return

        last_good = None
        for i in xrange(self.num_samples + self.degree):
            loc = i % self.num_samples
            t = loc / float(self.num_samples)
            sp = self.sample(t)
            if (last_good is not None and
                len(self.polyline)>0 and 
                dist2(sp, last_good) < 0.01):
                continue
            else:
                self.polyline.append(sp)
                last_good = sp

    def drawControl(self):
        glNewList((self.obj_id*GL_LIST_TOTAL) + GL_LIST_CONTROL, 
                GL_COMPILE)
        glBegin(GL_LINE_STRIP)
        for p in self.control_points:
            glVertex3f(p[0], p[1], p[2])
        glEnd()

    def drawPolyline(self):
        glNewList((self.obj_id*GL_LIST_TOTAL) + GL_LIST_POLYLINE, 
                GL_COMPILE)
        glBegin(GL_LINE_STRIP)
        for p in self.polyline:
            glVertex3f(p[0], p[1], p[2])
        glEnd()

    def sampleForward(self, t, step):
        return self.sample(t+step).pos - sample(t).pos
