from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from numpy import *
from numpy.linalg import *
from primitives import *
from aabb import *
from Queue import Queue
from consts import *
from gllists import *
import sys


class ObjLoader(object):
    obj_class_id = 1
    def __init__(self):
        self.faces = []
        self.obj_id = ObjLoader.obj_class_id
        self.polygon_list = None
        self.voxel_list = None
        self.use_boundaries = False
        self.voxelized = {}
        self.aabb = None
        self.use_xor = False
        self.voxel_zero = array([0,0,0])
        self.voxel_dimension = 1
        ObjLoader.obj_class_id = ObjLoader.obj_class_id + 1

        self.vox_version = VOXEL_FILE_VERSION

    def saveVox(self, filename):
        dimensions = [len(self.voxelized),
                      len(self.voxelized[0]),
                      len(self.voxelized[0][0])]
        with open(filename,"w") as f:
            f.write("knottyvox version "+str(self.vox_version)+"\n")
            f.write(str(dimensions[0])+","+
                    str(dimensions[1])+","+
                    str(dimensions[2])+","+
                    str(self.voxel_dimension)+","+
                    str(self.voxel_zero[0])+","+
                    str(self.voxel_zero[1])+","+
                    str(self.voxel_zero[2])+"\n")
            for i in xrange(len(self.voxelized)):
                for j in xrange(len(self.voxelized[i])):
                    for k in xrange(len(self.voxelized[i][j])):
                        cur_vox = self.voxelized[i][j][k]
                        if cur_vox.exists:
                            f.write("1")
                        else:
                            f.write("0")
            f.write("\n")
            f.close()
        print(filename + " saved successfully!")

    def loadVoxCheckMeta(self, filename, resolution):
        try:
            with open(filename) as f:
                version_line = f.readline().rstrip("\n")
                meta_line = f.readline().rstrip("\n")
                f.close()
                version_split = version_line.split(" ")
                meta_split = meta_line.split(",")
                if (version_split[0] != "knottyvox" or
                    version_split[1] != "version" or
                    version_split[2] != str(self.vox_version)):
                    print "Invalid file"
                    return False

                dimensions = [int(meta_split[0]),
                              int(meta_split[1]),
                              int(meta_split[2])]
                #+/- 1 for extra voxel given by rounding error
                if abs(max(dimensions)-resolution) > 1:
                    print "Different resolutions, remaking file"
                    return False
                return True
        except IOError as e:
            print "Voxel file not cached yet"
            return False

    def loadVox(self, filename):
        with open(filename) as f:
            version_line = f.readline().rstrip("\n")
            meta_line = f.readline().rstrip("\n")
            vox = f.readline().rstrip("\n")
            f.close()

            version_split = version_line.split(" ")
            meta_split = meta_line.split(",")

            if (version_split[0] != "knottyvox" or
                version_split[1] != "version" or
                version_split[2] != "1"):
                print "Invalid file"
                return

            dimensions = [int(meta_split[0]),
                          int(meta_split[1]),
                          int(meta_split[2])]
            voxel_size = float(meta_split[3])
            voxel_zero = [float(meta_split[4]),
                          float(meta_split[5]),
                          float(meta_split[6])]

            self.voxel_dimension = array(voxel_size)
            self.voxel_zero = array(voxel_zero)

            self.voxelized = {}

            count = 0
            for i in xrange(dimensions[0]):
                if i not in self.voxelized:
                    self.voxelized[i] = {}
                for j in xrange(dimensions[1]):
                    if j not in self.voxelized[i]:
                        self.voxelized[i][j] = {}
                    for k in xrange(dimensions[2]):
                        if k not in self.voxelized[i][j]:
                            self.voxelized[i][j][k] = Voxel()
                            self.voxelized[i][j][k].pos = array([i,j,k])
                        self.voxelized[i][j][k].exists = (vox[count] == "1")
                        count += 1
            print(filename + " loaded successfully!")

    def loadObj(self, filename):
        self.filename = filename
        vertices = {}
        with open(filename) as f:
            #vertices first, vertices indexed by 1
            cur_vert = 1
            for line in f:
                values = line.rstrip("\n").split(" ")
                if values[0] == "v":
                    vertices[cur_vert] = Vertex()
                    vertices[cur_vert].position = array([float(values[1]),
                                                         float(values[2]),
                                                         float(values[3])])
                    cur_vert += 1
        with open(filename) as f:
            cur_vert_n = 1
            normals = {}
            for line in f:
                values = line.rstrip("\n").split(" ")
                #ignore comments
                if values[0] == "#":
                    continue
                #vertex texture coord
                elif values[0] == "vt":
                    #ignore textures for now
                    continue
                #vertex normal
                elif values[0] == "vn":
                    normals[cur_vert_n] = array([float(values[1]),
                                                 float(values[2]),
                                                 float(values[3])])
                    cur_vert_n += 1
                #face
                elif values[0] == "f":
                    vtn = map(lambda v: v.split("/"),
                              [values[1], values[2], values[3]])
                    cur_face = Face()
                    face_vertices = [vertices[int(vtn[0][0])],
                                     vertices[int(vtn[1][0])],
                                     vertices[int(vtn[2][0])]]
                    if len(vtn[0]) > 1:
                        #we have normal information
                        for i in xrange(0,3):
                            face_vertices[i].normal = normals[int(vtn[i][2])]
                            #note that we dont want to calculate normals
                            #through interpolation lter
                            face_vertices[i].normal_samples = -1
                    for v in face_vertices:
                        v.face = cur_face
                    cur_face.vertices.extend(face_vertices)
                    self.faces.append(cur_face)
        #if no normal was specified, determine normal from order of vertices
        for face in self.faces:
            for v in face.vertices:
                if v.normal is None:
                    v.normal = array([0, 0, 0])
                if v.normal_samples >= 0:
                    t = face.vertices[1].position - face.vertices[0].position
                    bt = face.vertices[2].position - face.vertices[0].position
                    n = cross(t,bt)
                    n = n/norm(n)
                    v.normal = v.normal + n
                    v.normal_samples = v.normal_samples + 1
        for face in self.faces:
            face.normal = reduce(lambda x,y: x+y,
                    map(lambda v: v.position, face.vertices))/3
        #average the face contribution
        for v in face.vertices:
            v.normal /= v.normal_samples
        print str(len(self.faces))+" faces loaded"

    def createAABBTree(self):
        #now create acceleration structure for voxelization
        self.aabb = createAABBTree(self.faces)
        self.aabb.calculateBoundingSides()
        print "AABB Tree created"

    def drawTriangles(self):
        if self.polygon_list is None:
            self.polygon_list = uniqueGlListId()
            glNewList(self.polygon_list, GL_COMPILE)
            glBegin(GL_TRIANGLES)
            for face in self.faces:
                for v in face.vertices:
                    glNormal3f(v.normal[0], v.normal[1], v.normal[2])
                    glVertex3f(v.position[0], v.position[1], v.position[2])
            glEnd()
            glEndList()
        glCallList(self.polygon_list)

    def drawVoxels(self):
        if self.voxel_list is None:
            self.voxel_list = uniqueGlListId()
            glNewList(self.voxel_list, GL_COMPILE)
            glPushMatrix()
            glMultMatrixd(self.voxelTransformation())
            glBegin(GL_QUADS)
            total_iter = (len(self.voxelized) *
                    len(self.voxelized[0]) *
                    len(self.voxelized[0][0]))
            ct = 1
            for i in xrange(len(self.voxelized)):
                for j in xrange(len(self.voxelized[i])):
                    for k in xrange(len(self.voxelized[i][j])):
                        cur_voxel = self.voxelized[i][j][k]
                        if cur_voxel.exists:
                            alpha = 1.0
                            #defining v from the center, and going ccw
                            #for each face starting with the "front" face's
                            #top right vertex
                            v= [ array([i+0.5, j+0.5, k-0.5]),
                                 array([i-0.5, j+0.5, k-0.5]),
                                 array([i-0.5, j-0.5, k-0.5]),
                                 array([i+0.5, j-0.5, k-0.5]),
                                 array([i+0.5, j-0.5, k+0.5]),
                                 array([i+0.5, j+0.5, k+0.5]),
                                 array([i-0.5, j+0.5, k+0.5]),
                                 array([i-0.5, j-0.5, k+0.5]) ]

                            #right face (positive x)
                            glMaterialfv(GL_FRONT_AND_BACK,
                                    GL_AMBIENT_AND_DIFFUSE,
                                    [1.0,0.0,0.0,alpha])
                            glColor4f(1.0,0.0,0.0,alpha)
                            glNormal3f(1,0,0)
                            glVertex3f(v[5][0], v[5][1], v[5][2])
                            glVertex3f(v[0][0], v[0][1], v[0][2])
                            glVertex3f(v[3][0], v[3][1], v[3][2])
                            glVertex3f(v[4][0], v[4][1], v[4][2])

                            #left face (negative x)
                            glColor4f(1.0,0.0,0.0,alpha)
                            glNormal3f(-1,0,0)
                            glVertex3f(v[1][0], v[1][1], v[1][2])
                            glVertex3f(v[6][0], v[6][1], v[6][2])
                            glVertex3f(v[7][0], v[7][1], v[7][2])
                            glVertex3f(v[2][0], v[2][1], v[2][2])

                            #top face (positive y)
                            glMaterialfv(GL_FRONT_AND_BACK,
                                    GL_AMBIENT_AND_DIFFUSE,
                                    [0.0,1.0,0.0,alpha])
                            glColor4f(0.0,1.0,0.0,alpha)
                            glNormal3f(0,1,0)
                            glVertex3f(v[0][0], v[0][1], v[0][2])
                            glVertex3f(v[5][0], v[5][1], v[5][2])
                            glVertex3f(v[6][0], v[6][1], v[6][2])
                            glVertex3f(v[1][0], v[1][1], v[1][2])

                            #bottom face (negative y)
                            glColor4f(0.0,1.0,0.0,alpha)
                            glNormal3f(0,-1,0)
                            glVertex3f(v[3][0], v[3][1], v[3][2])
                            glVertex3f(v[2][0], v[2][1], v[2][2])
                            glVertex3f(v[7][0], v[7][1], v[7][2])
                            glVertex3f(v[4][0], v[4][1], v[4][2])

                            #back face (positive z)
                            glMaterialfv(GL_FRONT_AND_BACK,
                                    GL_AMBIENT_AND_DIFFUSE,
                                    [0.0,0.0,1.0,alpha])
                            glColor4f(0.0,0.0,1.0,alpha)
                            glNormal3f(0,0,1)
                            glVertex3f(v[6][0], v[6][1], v[6][2])
                            glVertex3f(v[5][0], v[5][1], v[5][2])
                            glVertex3f(v[4][0], v[4][1], v[4][2])
                            glVertex3f(v[7][0], v[7][1], v[7][2])

                            #front face (negative z)
                            glColor4f(0.0,0.0,1.0,alpha)
                            glNormal3f(0,0,-1)
                            glVertex3f(v[0][0], v[0][1], v[0][2])
                            glVertex3f(v[1][0], v[1][1], v[1][2])
                            glVertex3f(v[2][0], v[2][1], v[2][2])
                            glVertex3f(v[3][0], v[3][1], v[3][2])
                            """
                            print ("\rDisplay List Creation: "+
                                    str(ct)+"/"+
                                    str(total_iter)),
                            sys.stdout.flush()
                            ct += 1
                            """
            glEnd()
            glPopMatrix()
            glEndList()
        glCallList(self.voxel_list)



    #voxelizes the result into a 3d array, splitting into
    #"resoltion" cubes in its largest dimension
    def voxelize(self, resolution):
        self.voxelized = {}
        min_vertex_pos = array([float("inf"), float("inf"), float("inf")])
        max_vertex_pos = array([-float("inf"), -float("inf"), -float("inf")])

        for p in self.faces:
            for v in p.vertices:
                max_vertex_pos[0] = max(max_vertex_pos[0], v.position[0])
                max_vertex_pos[1] = max(max_vertex_pos[1], v.position[1])
                max_vertex_pos[2] = max(max_vertex_pos[2], v.position[2])

                min_vertex_pos[0] = min(min_vertex_pos[0], v.position[0])
                min_vertex_pos[1] = min(min_vertex_pos[1], v.position[1])
                min_vertex_pos[2] = min(min_vertex_pos[2], v.position[2])


        distance = max_vertex_pos - min_vertex_pos
        max_dist_dim = max(distance[0], distance[1], distance[2])
        cube_dimension = float(max_dist_dim)/resolution
        voxel_span = distance/cube_dimension
        voxel_span = [int(voxel_span[0]+1.5), int(voxel_span[1]+1.5),
                int(voxel_span[2]+1.5)]

        self.voxel_dimension = cube_dimension
        self.voxel_zero = min_vertex_pos

        print ("Creating voxelized object with resolution: ("+
                str(voxel_span[0])+","+str(voxel_span[1])+","+
                str(voxel_span[2])+")")
        if self.use_boundaries:
            self.boundaryVoxelization(voxel_span)
        else:
            self.filledVoxelization(voxel_span)

        print "Created voxelized object!"

    def boundaryVoxelization(self, voxel_span):
        #For each plane in XYZ, shoot rays and make voxels at intersections

        #fill array with nonexistant voxels first
        for i in xrange(0, voxel_span[0]):
            if i not in self.voxelized:
                self.voxelized[i] = {}
            for j in xrange(0, voxel_span[1]):
                if j not in self.voxelized[i]:
                    self.voxelized[i][j] = {}
                for k in xrange(0, voxel_span[2]):
                    if k not in self.voxelized[i][j]:
                        self.voxelized[i][j][k] = {}
                    new_vox = Voxel()
                    new_vox.exists = False
                    new_vox.pos = array([i, j, k])
                    self.voxelized[i][j][k] = new_vox

        total_iterations = (voxel_span[0]*voxel_span[1] +
                            voxel_span[0]*voxel_span[2] +
                            voxel_span[1]*voxel_span[2])
        iter_count = 0


        #XY
        for i in xrange(0, voxel_span[0]):
            for j in xrange(0, voxel_span[1]):
                center = (array([i+0.5, j+0.5, -0.5])*self.voxel_dimension+
                        self.voxel_zero)
                ray_dir = array([0,0,1])
                inter_ray = Ray(center, ray_dir, 0.01)
                for prim in self.aabb.relevantPrimitives(inter_ray):
                    intersection = prim.intersect(inter_ray)
                    if intersection < float("inf"):
                        cur_vox = self.voxelized[i][j][int(intersection/
                                                       self.voxel_dimension)]
                        cur_vox.exists = True
                iter_count += 1
                print ("\rVoxelization: "+
                    str(iter_count)+"/"+
                    str(total_iterations)),
                sys.stdout.flush()

        #XZ
        for i in xrange(0, voxel_span[0]):
            for k in xrange(0, voxel_span[2]):
                center = (array([i+0.5, -0.5, k+0.5])*self.voxel_dimension+
                        self.voxel_zero)
                ray_dir = array([0,1,0])
                inter_ray = Ray(center, ray_dir, 0.01)
                for prim in self.aabb.relevantPrimitives(inter_ray):
                    intersection = prim.intersect(inter_ray)
                    if intersection < float("inf"):
                        cur_vox = self.voxelized[i][int(intersection/
                                                    self.voxel_dimension)][k]
                        cur_vox.exists = True
                iter_count += 1
                print ("\rVoxelization: "+
                    str(iter_count)+"/"+
                    str(total_iterations)),
                sys.stdout.flush()

        #YZ
        for j in xrange(0, voxel_span[1]):
            for k in xrange(0, voxel_span[2]):
                center = (array([-0.5, j+0.5, k+0.5])*self.voxel_dimension+
                        self.voxel_zero)
                ray_dir = array([1,0,0])
                inter_ray = Ray(center, ray_dir, 0.01)
                for prim in self.aabb.relevantPrimitives(inter_ray):
                    intersection = prim.intersect(inter_ray)
                    if intersection < float("inf"):
                        cur_vox = self.voxelized[int(intersection/
                                                 self.voxel_dimension)][j][k]
                        cur_vox.exists = True
                iter_count += 1
                print ("\rVoxelization: "+
                    str(iter_count)+"/"+
                    str(total_iterations)),
                sys.stdout.flush()
        print "... Complete!"

    def filledVoxelization(self, voxel_span):
        #Go through 2D array of x,y and shoot ray in z direction
        total_iterations = voxel_span[0]*voxel_span[1]
        for i in xrange(0, int(voxel_span[0])):
            if i not in self.voxelized:
                self.voxelized[i] = {}
            for j in xrange(0, int(voxel_span[1])):
                if j not in self.voxelized[i]:
                    self.voxelized[i][j] = {}
                center = (array([i+0.5, j+0.5, -0.5])*self.voxel_dimension+
                        self.voxel_zero)
                winding_dir = array([0,0,1])
                winding_ray = Ray(center, winding_dir, 0.01)
                intersections = []
                #for prim in self.faces:
                for prim in self.aabb.relevantPrimitives(winding_ray):
                    intersection = prim.intersect(winding_ray)
                    if intersection < float("inf"):
                        intersections.append((intersection
                            ,dot(prim.normal, winding_dir) < 0))
                intersections = sorted(intersections, key=lambda x:x[0])
                intersections = map(lambda x: (x[0]/self.voxel_dimension,x[1]),
                        intersections)
                if self.use_xor:
                    prev = True
                    for a in xrange(len(intersections)):
                        intersections[a] = (intersections[a][0],prev)
                        prev = not prev
                    if len(intersections)%2 == 1:
                        print ("Using XOR when there are an odd # of "+
                            "intersections... Not good.")
                next_intersection = 0
                winding_number = 0
                prev_winding = None
                for k in xrange(0, int(voxel_span[2])):
                    if k not in self.voxelized[i][j]:
                        self.voxelized[i][j][k] = {}
                    if (next_intersection < len(intersections) and
                            k > intersections[next_intersection][0]):
                        if intersections[next_intersection][1]:
                            winding_number += 1
                        else:
                            winding_number -= 1
                        next_intersection += 1
                    elif (next_intersection >= len(intersections) and
                            winding_number > 0):
                        print ("Something went wrong - winding number > 0"+
                        " after all intersections... Setting it to 0")
                        winding_number = 0
                    new_vox = Voxel()
                    new_vox.exists = (winding_number > 0)
                    new_vox.pos = array([i, j, k])
                    self.voxelized[i][j][k] = new_vox
                    print ("\rVoxelization: "+
                        str(i*voxel_span[1]+j)+"/"+
                        str(total_iterations)),#+
                        #", current winding number: "+
                        #str(winding_number)),
                sys.stdout.flush()
        print ("\rVoxelization: "+
                str(total_iterations)+"/"+
                str(total_iterations)+
                "... Complete!")


    def iterateVoxels(self):
        for i in xrange(len(self.voxelized)):
            for j in xrange(len(self.voxelized[i])):
                for k in xrange(len(self.voxelized[i][j])):
                    yield self.voxelized[i][j][k]

    def voxelTransformation(self):
        trans = identity3D()
        trans = trans * translation3D(array([0.5,0.5,0]))
        trans = trans * scaling3D(array([self.voxel_dimension,
                                         self.voxel_dimension,
                                         self.voxel_dimension]))
        trans = trans * translation3D(self.voxel_zero)
        return trans


