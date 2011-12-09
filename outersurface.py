from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from objloader import *
from primitives import *
from knots import *
from numpy import *
from bspline import *
import math
import cPickle as pickle

class OuterSurface(object):

    def __init__(self, objloader):
        self.voxels = objloader.voxelized
        self.root_face = None
        self.surface_faces = {}
        self.obj_id = objloader.obj_id
        self.surface_list = None
        self.knots1_list = None
        self.knots_spline_list = None
        self.knots_spline_polyline_list = None
        self.knots_spline_control_list = None
        self.knots_spline_triangle_list = None
        self.knot = None
        self.splines = []
        self.obj_loader = objloader
        self.num_samples = 1
        self.cs_scale = 1

        #serialization check
        self.version = OUTER_SURFACE_FILE_VERSION

    def updateVoxels(self):
        self.voxels = self.obj_loader.voxelized

    def generate(self):
        """
        First find an outer face.
        """

        starting_face = None
        face_dir = {}

        for x in xrange(len(self.voxels)):
            for y in xrange(len(self.voxels[0])):
                for z in xrange(len(self.voxels[0][0])):
                    voxel = self.voxels[x][y][z]
                    if voxel.exists:
                        if not starting_face:
                            starting_face = (x, y, z-0.5)

                        faces = [((x-0.5, y, z), Directions.NEGX),
                                 ((x+0.5, y, z), Directions.POSX),
                                 ((x, y-0.5, z), Directions.NEGY),
                                 ((x, y+0.5, z), Directions.POSY),
                                 ((x, y, z-0.5), Directions.NEGZ),
                                 ((x, y, z+0.5), Directions.POSZ),
                                 ]
                        for pos, dir in faces:
                            if pos in face_dir:
                                del face_dir[pos]
                            else:
                                face_dir[pos] = dir

        faces_to_crawl = [starting_face]

        def _crawlSurface(face):
            if face in self.surface_faces:
                return

            x, y, z = face
            dir = face_dir[face]
            self.surface_faces[face] = dir

            #print "Added face %s to surface faces" % str(face)

            new_surface_faces = set()

            tests = [None, None, None, None]
            if type(x) == float:
                sign = -1 if dir == Directions.NEGX else 1

                x = int(x - sign*0.5)

                tests[0] = [((x+sign,     y+0.5, z), Directions.NEGY),
                            ((x+sign*0.5, y+1,   z), dir),
                            ((x,          y+0.5, z), Directions.POSY),
                            ]
                tests[1] = [((x+sign,     y-0.5, z), Directions.POSY),
                            ((x+sign*0.5, y-1,   z), dir),
                            ((x,          y-0.5, z), Directions.NEGY),
                            ]
                tests[2] = [((x+sign,     y, z+0.5), Directions.NEGZ),
                            ((x+sign*0.5, y, z+1),   dir),
                            ((x,          y, z+0.5), Directions.POSZ),
                            ]
                tests[3] = [((x+sign,     y, z-0.5), Directions.POSZ),
                            ((x+sign*0.5, y, z-1),   dir),
                            ((x,          y, z-0.5), Directions.NEGZ),
                            ]
            elif type(y) == float:
                sign = -1 if dir == Directions.NEGY else 1

                y = int(y - sign*0.5)

                tests[0] = [((x+0.5, y+sign,     z), Directions.NEGX),
                            ((x+1,   y+sign*0.5, z), dir),
                            ((x+0.5, y,          z), Directions.POSX),
                            ]
                tests[1] = [((x-0.5, y+sign,     z), Directions.POSX),
                            ((x-1,   y+sign*0.5, z), dir),
                            ((x-0.5, y,          z), Directions.NEGX),
                            ]
                tests[2] = [((x, y+sign,     z+0.5), Directions.NEGZ),
                            ((x, y+sign*0.5, z+1),   dir),
                            ((x, y,          z+0.5), Directions.POSZ),
                            ]
                tests[3] = [((x, y+sign,     z-0.5), Directions.POSZ),
                            ((x, y+sign*0.5, z-1),   dir),
                            ((x, y,          z-0.5), Directions.NEGZ),
                            ]
            else:
                sign = -1 if dir == Directions.NEGZ else 1

                z = int(z - sign*0.5)

                tests[0] = [((x+0.5, y, z+sign),     Directions.NEGX),
                            ((x+1,   y, z+sign*0.5), dir),
                            ((x+0.5, y, z),          Directions.POSX),
                            ]
                tests[1] = [((x-0.5, y, z+sign),     Directions.POSX),
                            ((x-1,   y, z+sign*0.5), dir),
                            ((x-0.5, y, z),          Directions.NEGX),
                            ]
                tests[2] = [((x, y+0.5, z+sign),     Directions.NEGY),
                            ((x, y+1,   z+sign*0.5), dir),
                            ((x, y+0.5, z),          Directions.POSY),
                            ]
                tests[3] = [((x, y-0.5, z+sign),     Directions.POSY),
                            ((x, y-1,   z+sign*0.5), dir),
                            ((x, y-0.5, z),          Directions.NEGY),
                            ]

            for test in tests:
                for face, dir in test:
                    if face in face_dir and dir == face_dir[face]:
                        new_surface_faces.add(face)
                        break

            faces_to_crawl.extend(new_surface_faces)

        while faces_to_crawl:
            _crawlSurface(faces_to_crawl.pop())

        print "Finished finding outer surface"

    def applyKnots(self):
        self.knot = Knot()

        direction_dict = {Directions.POSX: (1, 0, 0),
                          Directions.POSY: (0, 1, 0),
                          Directions.POSZ: (0, 0, 1),
                          Directions.NEGX: (-1, 0, 0),
                          Directions.NEGY: (0, -1, 0),
                          Directions.NEGZ: (0, 0, -1),
                          }

        for face, dir in self.surface_faces.items():
            dir = direction_dict[dir]

            x, y, z = face

            if type(x) == float:
                x = int(x - dir[0]*0.5)
                sign = 0.3 * (((x + y + z) % 2) - 0.5)

                seq = [(x + 0.5*dir[0], y-0.5, z),
                       (x + (0.5 + sign)*dir[0], y, z),
                       (x + 0.5*dir[0], y+0.5, z),
                       ]
                self.knot.addSequence(seq)

                seq = [(x + 0.5*dir[0], y, z-0.5),
                       (x + (0.5 - sign)*dir[0], y, z),
                       (x + 0.5*dir[0], y, z+0.5),
                       ]
                self.knot.addSequence(seq)
            elif type(y) == float:
                y = int(y - dir[1]*0.5)
                sign = 0.3 * (((x + y + z) % 2) - 0.5)

                seq = [(x, y + 0.5*dir[1], z-0.5),
                       (x, y + (0.5 + sign)*dir[1], z),
                       (x, y + 0.5*dir[1], z+0.5),
                       ]
                self.knot.addSequence(seq)

                seq = [(x-0.5, y + 0.5*dir[1], z),
                       (x, y + (0.5 - sign)*dir[1], z),
                       (x+0.5, y + 0.5*dir[1], z),
                       ]
                self.knot.addSequence(seq)
            else:
                z = int(z - dir[2]*0.5)
                sign = 0.3 * (((x + y + z) % 2) - 0.5)

                seq = [(x-0.5, y, z + 0.5*dir[2]),
                       (x, y, z + (0.5 + sign)*dir[2]),
                       (x+0.5, y, z + 0.5*dir[2]),
                       ]
                self.knot.addSequence(seq)

                seq = [(x, y-0.5, z + 0.5*dir[2]),
                       (x, y, z + (0.5 - sign)*dir[2]),
                       (x, y+0.5, z + 0.5*dir[2]),
                       ]
                self.knot.addSequence(seq)
        for a, b in self.knot.open_loops.items():
            print a, ':', b

    """
    Right now, this is done through pickle.
    This results in a huge file size. I will make a new file format later...
    """
    def load(self, filename, obj_loader=None):
        try:
            loaded_surface = pickle.load( open(filename, "rb"))
            if (loaded_surface.version == self.version and
                loaded_surface.num_samples >= self.num_samples and
                loaded_surface.cs_scale == self.cs_scale and
                (obj_loader is None or (
                    (loaded_surface.obj_loader.voxel_dimension ==
                        obj_loader.voxel_dimension) and
                    (len(loaded_surface.obj_loader.voxelized) ==
                        len(obj_loader.voxelized))))):
                self.voxels = loaded_surface.voxels
                self.root_face = loaded_surface.root_face
                self.surface_faces = loaded_surface.surface_faces
                self.obj_id = loaded_surface.obj_id
                self.surface_list = None
                self.knots1_list = None
                self.knots_spline_list = None
                self.knots_spline_polyline_list = None
                self.knots_spline_control_list = None
                self.knot = loaded_surface.knot
                self.splines = loaded_surface.splines
                self.obj_loader = loaded_surface.obj_loader
                self.num_samples = loaded_surface.num_samples

                self.obj_loader.polygon_list = None
                self.obj_loader.voxel_list = None
                return True
        except IOError as e:
            print "Spline file not cached yet"
        return False

    def save(self, filename):
        return pickle.dump(self, open(filename, "wb"))

    def drawSurface(self):
        if not self.surface_list:
            self.surface_list = uniqueGlListId()
            direction_dict = {Directions.POSX: (1, 0, 0),
                              Directions.POSY: (0, 1, 0),
                              Directions.POSZ: (0, 0, 1),
                              Directions.NEGX: (-1, 0, 0),
                              Directions.NEGY: (0, -1, 0),
                              Directions.NEGZ: (0, 0, -1),
                              }

            glNewList(self.surface_list, GL_COMPILE)
            glPushMatrix()
            glMultMatrixd(self.obj_loader.voxelTransformation())
            glBegin(GL_QUADS)

            for face, dir in self.surface_faces.items():
                dir = direction_dict[dir]
                glNormal3f(dir[0], dir[1], dir[2])

                x, y, z = face

                if type(x) == float:
                    if dir[0] > 0:
                        glVertex3f(x, y-0.5, z-0.5)
                        glVertex3f(x, y+0.5, z-0.5)
                        glVertex3f(x, y+0.5, z+0.5)
                        glVertex3f(x, y-0.5, z+0.5)
                    else:
                        glVertex3f(x, y-0.5, z+0.5)
                        glVertex3f(x, y+0.5, z+0.5)
                        glVertex3f(x, y+0.5, z-0.5)
                        glVertex3f(x, y-0.5, z-0.5)
                elif type(y) == float:
                    if dir[1] > 0:
                        glVertex3f(x-0.5, y, z-0.5)
                        glVertex3f(x-0.5, y, z+0.5)
                        glVertex3f(x+0.5, y, z+0.5)
                        glVertex3f(x+0.5, y, z-0.5)
                    else:
                        glVertex3f(x+0.5, y, z-0.5)
                        glVertex3f(x+0.5, y, z+0.5)
                        glVertex3f(x-0.5, y, z+0.5)
                        glVertex3f(x-0.5, y, z-0.5)
                else:
                    if dir[2] > 0:
                        glVertex3f(x-0.5, y-0.5, z)
                        glVertex3f(x-0.5, y+0.5, z)
                        glVertex3f(x+0.5, y+0.5, z)
                        glVertex3f(x+0.5, y-0.5, z)
                    else:
                        glVertex3f(x+0.5, y-0.5, z)
                        glVertex3f(x+0.5, y+0.5, z)
                        glVertex3f(x-0.5, y+0.5, z)
                        glVertex3f(x-0.5, y-0.5, z)

            glEnd()
            glPopMatrix()
            glEndList()
        glCallList(self.surface_list)

    def drawKnots1(self):
        if not self.knot:
            return

        if not self.knots1_list:
            self.knots1_list = uniqueGlListId()

            quad = gluNewQuadric()

            def drawCylinder(start, end):
                mid = [float(start[0] + end[0]) / 2,
                       float(start[1] + end[1]) / 2,
                       float(start[2] + end[2]) / 2,
                       ]

                dir = [float(end[0] - start[0]),
                       float(end[1] - start[1]),
                       float(end[2] - start[2]),
                       ]

                height = math.sqrt((dir[0])**2 + (dir[1])**2 + (dir[2])**2)
                axis = cross([0, 0, 1], dir)
                angle = math.acos(dir[2] / height) * 180.0 / math.pi

                glPushMatrix()
                glTranslatef(mid[0], mid[1], mid[2])
                glRotatef(angle, axis[0], axis[1], axis[2])
                glTranslatef(0, 0, -height*1.1/2)
                gluCylinder(quad, 0.1, 0.1, height*1.1, 10, 1)
                glPopMatrix()

            glNewList(self.knots1_list, GL_COMPILE)
            glPushMatrix()
            glMultMatrixd(self.obj_loader.voxelTransformation())

            glColor3f(1.0, 0.0, 0.0)

            for loop in self.knot.closed_loops:
                prev = loop[0]
                for cur in loop[1:]:
                    drawCylinder(prev, cur)
                    prev = cur

            glPopMatrix()
            glEndList()

        glCallList(self.knots1_list)

    def createBezierCurves(self):
        print "Reticulating Splines..."
        if len(self.splines) > 0:
            self.splines = []
        control_spline = BSpline()
        control_spline.control_points = [array([1,1,0]),
                                         array([-1,1,0]),
                                         array([-1,-1,0]),
                                         array([1,-1,0])]
        control_spline.num_samples = 8
        cur_loop_num = 0
        loop_total_num = str(len(self.knot.closed_loops))

        for loop in self.knot.closed_loops:
            loop_spline = BSpline()
            array_control_points = map(lambda x: array(x), loop)
            loop_spline.control_points = array_control_points
            """
            approximating this for now... actually make a better sample rate
            later...

            if num samples = num cp, then it is like taking each control point
            as a sample point
            """
            loop_spline.num_samples = (len(array_control_points)
                                       *self.num_samples)
            loop_spline.generatePolyline()
            #loop_spline.cross_section = control_spline.control_points
            loop_spline.setBsplineCrossSection(control_spline)
            loop_spline.generateSweepShape(self.cs_scale)
            self.splines.append(loop_spline)
            print ("\rSpline Generation: "+
                    str(cur_loop_num)+"/"+
                    loop_total_num),
            sys.stdout.flush()
            cur_loop_num += 1
        print ("\rSpline Generation: "+loop_total_num+"/"+
                loop_total_num+"...complete")

    def saveStl(self, filename):
        try:
            with open(filename,"w") as f:
                f.write("solid knotty\n")
                cur_triangles = 0
                total_vertices = 0
                cur_splines = 0
                max_splines = str(len(self.splines))
                for spline in self.splines:
                    total_vertices += len(spline.vertices)
                    for q in spline.vertices:
                        """
                        NOTE: the 6 is hardcoded from the hardcoded cross section...
                        figure this out later...
                        """
                        for j in xrange(len(q)-6):
                            i = j % len(q)
                            """
                            equal weighting - can weight by angle, but in the end
                            we are just making the normal for the STL files, not rendering
                            """
                            cur_normal = (q[i].normal
                                          + q[(i+1)%len(q)].normal
                                          + q[(i+2)%len(q)].normal)
                            cur_normal /= norm(cur_normal)
                            f.write("facet normal "+str(cur_normal[0])+" "
                                                   +str(cur_normal[1])+" "
                                                   +str(cur_normal[2])+"\n")
                            cur_v = (q[i].point,
                                     q[(i+1)%len(q)].point,
                                     q[(i+2)%len(q)].point)

                            """
                            Determine alignment
                            """

                            dir1 = cur_v[1] - cur_v[0]
                            dir2 = cur_v[2] - cur_v[0]
                            dir_norm = cross(dir1, dir2)
                            vertices = None

                            if dot(dir_norm, cur_normal) > 0:
                                vertices = (cur_v[0], cur_v[1], cur_v[2])
                            else:
                                vertices = (cur_v[2], cur_v[1], cur_v[0])

                            f.write("outer loop\n")
                            for v in cur_v:
                                f.write("vertex "+str(v[0])+" "+str(v[1])+" "
                                        +str(v[2])+"\n")
                            f.write("endloop\n")
                            f.write("endfacet\n")
                            cur_triangles += 1
                    cur_splines += 1
                    print ("\rSaving STL: "+str(cur_splines)+"/"+max_splines),
                    sys.stdout.flush()
                f.write("endsolid knotty\n")
                print "\rSaving STL: "+max_splines+"/"+max_splines
                print (str(filename)+" saved! ("+
                        str(total_vertices)+" vertices, "+
                        str(cur_triangles)+" triangles)")
        except IOError as e:
            print "Could not save STL file: "+str(e)

    def saveObj(self, filename):
        try:
            with open(filename,"w") as f:
                vertices = {}
                normals = {}
                faces = {}

                cur_v = 1
                cur_n = 1
                cur_f = 1

                f.write("# knotty\n")
                cur_triangles = 0
                cur_splines = 0
                max_splines = str(len(self.splines))
                for spline in self.splines:
                    for q in spline.vertices:
                        for i in xrange(len(q)-6):
                            """
                            equal weighting - can weight by angle, but in the end
                            we are just making the normal for the STL files, not
                            rendering
                            """
                            cur_normals = (q[i].normal,
                                           q[i+1].normal,
                                           q[i+2].normal)
                            cur_normal = (cur_normals[0]
                                          + cur_normals[1]
                                          + cur_normals[2])
                            cur_normal /= norm(cur_normal)
                            normals[cur_n] = cur_normals[0]
                            normals[cur_n+1] = cur_normals[1]
                            normals[cur_n+2] = cur_normals[2]

                            cur_vertices = (q[i].point,
                                            q[i+1].point,
                                            q[i+2].point)

                            """
                            Determine alignment
                            """

                            dir1 = cur_vertices[1] - cur_vertices[0]
                            dir2 = cur_vertices[2] - cur_vertices[0]
                            dir_norm = cross(dir1, dir2)
                            cur_vertices_ordered = None

                            if dot(dir_norm, cur_normal) > 0:
                                cur_vertices_ordered = (cur_vertices[0],
                                                        cur_vertices[1],
                                                        cur_vertices[2])
                            else:
                                cur_vertices_ordered = (cur_vertices[2],
                                                        cur_vertices[1],
                                                        cur_vertices[0])

                            vertices[cur_v] = cur_vertices_ordered[0]
                            vertices[cur_v+1] = cur_vertices_ordered[1]
                            vertices[cur_v+2] = cur_vertices_ordered[2]

                            faces[cur_f] = ((cur_v, cur_n),
                                            (cur_v+1, cur_n+1),
                                            (cur_v+2, cur_n+2))

                            cur_v += 3
                            cur_n += 3
                            cur_f += 1

                            cur_triangles += 1
                    cur_splines += 1
                    print ("\rSaving OBJ: Populating arrays "+
                            str(cur_splines)+"/"+max_splines),
                    sys.stdout.flush()
                print ""

                slen_v = str(len(vertices))
                slen_n = str(len(normals))
                slen_fs = str(len(faces))

                print "Saving OBJ: Writing vertices"
                for v in vertices:
                    vt = vertices[v]
                    f.write("v "+str(vt[0])+" "+str(vt[1])+" "+str(vt[2])+"\n")
                    #print "\r Saving OBJ: Writing vertices "+str(v)+"/"+slen_v,
                    #sys.stdout.flush()

                print "Saving OBJ: Writing normals"
                for n in normals:
                    nl = normals[n]
                    f.write("v "+str(nl[0])+" "+str(nl[1])+" "+str(nl[2])+"\n")
                    #print "\r Saving OBJ: Writing normals "+str(n)+"/"+slen_n,
                    #sys.stdout.flush()

                print "Saving OBJ: Writing faces"
                for fs in faces:
                    fc = faces[fs]
                    """
                    We don't have textures
                    """
                    f.write("f "+str(fc[0][0])+"//"+str(fc[0][1])+" "
                                +str(fc[1][0])+"//"+str(fc[1][1])+ " "
                                +str(fc[2][0])+"//"+str(fc[2][1])+"\n")
                    #print "\r Saving OBJ: Writing faces "+str(fs)+"/"+slen_fs,
                    #sys.stdout.flush()



                f.write("endsolid knotty\n")
                print (str(filename)+" saved! ("+
                        str(slen_v)+" vertices, "+
                        str(slen_fs)+" triangles)")
        except IOError as e:
            print "Could not save OBJ file: "+str(e)


    def drawKnotsSpline(self):
        if not self.knot:
            return
        if not self.knots_spline_list:
            if len(self.splines) == 0:
                self.createBezierCurves()
            self.knots_spline_list = uniqueGlListId()

            glNewList(self.knots_spline_list, GL_COMPILE)
            glPushMatrix()
            glMultMatrixd(self.obj_loader.voxelTransformation())

            glColor3f(1.0, 1.0, 1.0)

            print "Compiling splines for GL display"

            cur_spline = 0
            num_splines = str(len(self.splines))
            for spline in self.splines:
                spline.drawSpline()
                print ("\rSpline Compilation: "+str(cur_spline)+"/"+
                        num_splines),
                sys.stdout.flush()
                cur_spline += 1

            print ("\rSpline Compilation: "+num_splines+"/"+
                    num_splines+"...complete")

            glPopMatrix()
            glEndList()

        glCallList(self.knots_spline_list)

    def drawKnotsPolyline(self):
        if not self.knot:
            return
        if not self.knots_spline_polyline_list:
            if len(self.splines) == 0:
                self.createBezierCurves()
            self.knots_spline_polyline_list = uniqueGlListId()

            glNewList(self.knots_spline_polyline_list, GL_COMPILE)
            glPushMatrix()
            glMultMatrixd(self.obj_loader.voxelTransformation())

            glColor3f(1.0, 1.0, 1.0)

            print "Compiling polyline for GL display"

            cur_spline = 0
            num_splines = str(len(self.splines))

            for spline in self.splines:
                spline.drawPolyline()
                print ("\rPolyline Compilation: "+str(cur_spline)+"/"+
                        num_splines),
                sys.stdout.flush()
                cur_spline += 1
            print ("\rPolyline Compilation: "+num_splines+"/"+
                    num_splines+"...complete")

            glPopMatrix()
            glEndList()

        glCallList(self.knots_spline_polyline_list)

    def drawKnotsControl(self):
        if not self.knot:
            return
        if not self.knots_spline_control_list:
            self.knots_spline_control_list = uniqueGlListId()

            glNewList(self.knots_spline_control_list, GL_COMPILE)
            glPushMatrix()
            glMultMatrixd(self.obj_loader.voxelTransformation())

            glColor3f(1.0, 1.0, 1.0)

            print "Compiling control points for GL display"

            cur_spline = 0
            num_splines = str(len(self.splines))

            for spline in self.splines:
                spline.drawControl()
                print ("\rControl Point Compilation: "+str(cur_spline)+"/"+
                        num_splines),
                sys.stdout.flush()
                cur_spline += 1
            print ("\rControl Point Compilation: "+num_splines+"/"+
                    num_splines+"...complete")

            glPopMatrix()
            glEndList()

        glCallList(self.knots_spline_control_list)


    def drawKnotsTriangle(self):
        if not self.knot:
            return
        if not self.knots_spline_triangle_list:
            self.knots_spline_triangle_list = uniqueGlListId()

            glNewList(self.knots_spline_triangle_list, GL_COMPILE)
            glPushMatrix()
            glMultMatrixd(self.obj_loader.voxelTransformation())

            glColor3f(1.0, 1.0, 1.0)

            print "Compiling spline (triangle) for GL display"

            cur_spline = 0
            num_splines = str(len(self.splines))

            for spline in self.splines:
                spline.drawSplineTriangle()
                print ("\rSpline (Triangle) Compilation: "+str(cur_spline)+"/"+
                        num_splines),
                sys.stdout.flush()
                cur_spline += 1
            print ("\rSpline (Triangle) Compilation: "+num_splines+"/"+
                    num_splines+"...complete")

            glPopMatrix()
            glEndList()

        glCallList(self.knots_spline_triangle_list)




