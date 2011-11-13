from OpenGL.GL import * 
from OpenGL.GLUT import *
from OpenGL.GLU import *
from numpy import *
from numpy.linalg import *
from primitives import *
from aabb import *



class ObjLoader(object):
    obj_class_id = 1
    def __init__(self):
        self.faces = []
        self.obj_id = ObjLoader.obj_class_id
        self.polygon_list = False
        self.voxel_list = False
        self.voxelized = {}
        self.aabb = None
        ObjLoader.obj_class_id = ObjLoader.obj_class_id + 1

    def load(self, filename):
        self.filename = filename
        with open(filename) as f:
            #vertices first, vertices indexed by 1
            cur_vert = 1
            vertices = {}
            for line in f:
                values = line.rstrip("\n").split(" ")
                if values[0] == "v":
                    vertices[cur_vert] = Vertex()
                    vertices[cur_vert].position = array([float(values[1]), 
                                                         float(values[2]), 
                                                         float(values[3])])
                cur_vert = cur_vert + 1
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
                            face_vertices[i].normal = normals[vtn[i][2]]
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

        #now create acceleration structure for voxelization
        self.aabb = createAABBTree(self.faces)

    def drawTriangles(self):
        if not self.polygon_list:
            glNewList(self.obj_id, GL_COMPILE)
            glBegin(GL_TRIANGLES)
            for face in self.faces:
                for v in face.vertices:
                    glNormal3f(v.normal[0], v.normal[1], v.normal[2])
                    glVertex3f(v.position[0], v.position[1], v.position[2])
            glEnd()
            glEndList()
            self.polygon_list = True
        glCallList(self.obj_id)

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

        print max_vertex_pos
        print min_vertex_pos

        distance = max_vertex_pos - min_vertex_pos
        max_dist_dim = max(distance[0], distance[1], distance[2])
        cube_dimension = float(max_dist_dim)/resolution
        voxel_span = distance/cube_dimension

        #winding number reference point
        #here is a point defined to be outside the object
        reference = array(max_vertex_pos+array([1,1,1]))

        for i in xrange(0, int(voxel_span[0])):
            for j in xrange(0, int(voxel_span[1])):
                for k in xrange(0, int(voxel_span[2])):
                    if i not in self.voxelized:
                        self.voxelized[i] = {}
                    if j not in self.voxelized[i]:
                        self.voxelized[i][j] = {}
                    if k not in self.voxelized[i][j]:
                        self.voxelized[i][j][k] = {}
                    #sample at the center of each voxel
                    center = array([i,j,k])+array([cube_dimension/2])
                    winding_dir = reference-center
                    winding_number = 0
                    winding_ray = Ray(center, winding_dir, 0.01)
                    for prim in self.aabb.relevantPrimitives(winding_ray):
                        if prim.intersect(winding_ray) < float("inf"):
                            if dot(winding_ray.direction, prim.normal) > 0:
                                winding_number += 1
                            else:
                                winding_number -= 1
                    if winding_number >= 0:
                        self.voxelized[i][j][k] = 1
                    else:
                        self.voxelized[i][j][k] = 0
                    
        



