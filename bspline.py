from OpenGL.GL import *
from numpy import *
from numpy.linalg import *
from algebra import *
from consts import *

class SplinePoint(object):
    def __init__(self):
        self.point = None
        self.azimuth = 0
        self.scale = 1
        self.normal = array([1,0.0])

def lerp(a, b, t):
    return (1-t)*a + t*b

def dist2(a,b):
    assert(len(a) == len(b))
    res = 0.0
    for i in xrange(len(a)):
        minus = a[i]-b[i]
        res += minus*minus
    return res

def length2(a):
    res = 0.0
    for i in xrange(len(a)):
        res += a[i]*a[i]
    return res

def clamp(x, mini, maxi):
    if x > maxi:
        x = maxi
    if x < mini:
        x = mini
    return x

def advanceFrame(xi, xi1, ti, si, ri, ti1):
    v1 = xi1 - xi
    c1 = dot(v1, v1)
    if c1 == 0:
        return c1
    ri_l = ri - (2/c1) * (v1*ri) * v1
    ti_l = ti - (2/c1) * (v1*ti) * v1
    v2 = ti1 - ti_l
    c2 = dot(v2, v2)
    if c2 == 0:
        return ri
    return ri_l - (2/c2) * (v2*ri_l) * v2

class BSpline(object):
    def __init__(self,obj_loader=None):
        self.control_points = []
        self.polygon = []
        self.polyline = []
        self.global_twist = 0
        self.global_azimuth = 0
        self.num_samples = 20
        self.closed = False
        self.cross_section = []

        self.vertices = []

        #not sure i like this, maybe keep drawlist id's separate...
        if obj_loader is not None:
            self.obj_id = obj_loader.obj_id
        else:
            self.obj_id = 0

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
        self.polyline = []
        if self.num_samples == 0:
            return

        last_good = None
        for i in xrange(self.num_samples + self.degree):
            loc = i % self.num_samples
            t = loc / float(self.num_samples)
            sp = self.sample(t)
            if (last_good is not None and
                len(self.polyline) > 0 and 
                dist2(sp, last_good) < 0.000001):
                continue
            else:
                new_pt = SplinePoint()
                new_pt.point = array(sp)
                self.polyline.append(new_pt)
                last_good = array(sp)

    def generateSweepShape(self, scale):
        self.vertices = []

        new_slice = []
        old_slice = []
        old_dir = 0
        right = 0
        up = 0

        first_dir = True
        for i in xrange(1,len(self.polyline)-1):
            pts = [0,0,0]
            percent = (float) (i%len(self.polyline)) / (len(self.polyline)-3)
            delta_percent = 1.0 / (float)(len(self.polyline)-3)
            #local points
            for c in xrange(-1,2):
                pts[c+1] = self.polyline[ (i + len(self.polyline) + c) %
                        len(self.polyline) ]
            leg1 = pts[0].point - pts[1].point
            leg2 = pts[2].point - pts[1].point
            leg1 /= norm(leg1)
            leg2 /= norm(leg2)

            direction = leg2 - leg1
            if length2(direction) < 0.0001:
                direction = pts[2].point - pts[1].point
            direction /= norm(direction)

            if first_dir:
                up = self.getFirstUp()
                first_dir = False
            else:
                up = advanceFrame(pts[0].point, pts[1].point,
                                  old_dir, right, up, direction)
            right = cross(direction, up)
            right /= norm(right)
            up = cross(right, direction)
            up /= norm(up)

            rot = percent + pts[1].azimuth #+globazi + globtwist

            bisect = leg1 + leg2
            length = norm(bisect)
            scale_sect = False
            scale_trans = 0

            #only scale if not going straight
            if len < 0.0001:
                scale_sect = True
                bisect = bisect/len
                dotted = -leg1*leg2
                angle = math.acos(clamp(dotted, -1.0, 1.0))
                scale = (float) (1.0)/max(cos(0.5*angle), 0.1)
                scale_trans = scale - 1.0

            for cs in self.cross_section:
                pos2d = dot(rotation2D(array([0,0]), rot),cs).tolist()[0]
                pt = right * pos2d[0] * scale + up * pos2d[1] * scale
                if scale_sect:
                    pt = pt + scale_trans * (pt * bisect) * bisect
                pt *= pts[1].scale
                new_slice.append(pts[1].point + pt)

            if i > 1:
                for v in xrange(len(self.cross_section)):
                    vn = v % len(self.cross_section)

                    new_point0 = SplinePoint()
                    tan0 = (old_slice[(vn+1)%len(self.cross_section)] - 
                            old_slice[vn])
                    tan0 /= norm(tan0)
                    print tan0
                    print old_dir
                    new_point0.normal = -(cross(tan0, old_dir))
                    new_point0.point = old_slice[vn]
                    self.vertices.append(new_point0)

                    new_point1 = SplinePoint()
                    tan1 = (new_slice[(vn+1)%len(self.cross_section)] - 
                            new_slice[vn])
                    tan1 /= norm(tan1)
                    new_point1.normal = -(cross(tan1, direction))
                    new_point1.point = new_slice[vn]
                    self.vertices.append(new_point1)

            old_slice = new_slice
            new_slice = []
            old_dir = direction



    def getFirstUp(self):
        leg1 = self.sampleForwardNonZero(0)
        leg1 /= norm(leg1)
        leg2 = self.sampleForwardNonZero(0,-0.001)
        leg2 /= norm(leg2)
        up = leg1+leg2
        if length2(up) < 0.0001:
            up = cross(leg1,array([0.0,1.0,0.0]))
            if length2(up) < 0.0001:
                up = cross(leg1, array([0.1,1.0,0.0]))
        up /= norm(up)
        return up

    def drawControl(self):
        #glNewList((self.obj_id*GL_LIST_TOTAL) + GL_LIST_CONTROL,
        #        GL_COMPILE)
        glBegin(GL_LINE_STRIP)
        for p in self.control_points:
            glVertex3f(p[0], p[1], p[2])
        glEnd()

    def drawPolyline(self):
        #glNewList((self.obj_id*GL_LIST_TOTAL) + GL_LIST_POLYLINE,
        #        GL_COMPILE)
        glBegin(GL_LINE_STRIP)
        for p in self.polyline:
            pt = p.point
            glVertex3f(pt[0], pt[1], pt[2])
        glEnd()

    def drawSpline(self):
        #add list later
        glBegin(GL_QUAD_STRIP)
        for p in self.vertices:
            pt = p.point
            n = p.normal
            glNormal3f(n[0], n[1], n[2])
            glVertex3f(pt[0], pt[1], pt[2])
        glEnd()


    def sampleForward(self, t, step):
        return self.sample(t+step) - self.sample(t)

    def sampleForwardNonZero(self, t, step=0.01, search_dist=50):
        k = 1
        direct = None
        while(direct is None or (length2(direct) < 0.001 and k < search_dist)):
            direct = self.sampleForward(t,step*k)
            k += 1
        return direct

