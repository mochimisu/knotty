from OpenGL.GL import * 
from OpenGL.GLUT import *
from OpenGL.GLU import *
from numpy import *
from numpy.linalg import *
from primitives import *
from aabb import *
import sys

class ObjLoader(object):
    obj_class_id = 1
    def __init__(self):
        self.faces = []
        self.obj_id = ObjLoader.obj_class_id
        self.polygon_list = False
        self.voxel_list = False
        self.voxelized = {}
        self.aabb = None
        self.use_xor = False
        ObjLoader.obj_class_id = ObjLoader.obj_class_id + 1

    def load(self, filename):
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

        #now create acceleration structure for voxelization
        self.aabb = createAABBTree(self.faces)
        self.aabb.calculateBoundingSides()
        print "AABB Tree created"

    def drawTriangles(self):
        if not self.polygon_list:
            glNewList((self.obj_id*10)+0, GL_COMPILE)
            glBegin(GL_TRIANGLES)
            for face in self.faces:
                for v in face.vertices:
                    glNormal3f(v.normal[0], v.normal[1], v.normal[2])
                    glVertex3f(v.position[0], v.position[1], v.position[2])
            glEnd()
            glEndList()
            self.polygon_list = True
        glCallList(self.obj_id*10 + 0)

    def drawVoxels(self):
        if not self.voxel_list:
            glNewList((self.obj_id*10)+1, GL_COMPILE)
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
                            #scale the coordinates to the voxel dimensions
                            #and appropriately offset the shape
                            for vert in xrange(len(v)):
                                v[vert] = (((v[vert]+array([0.5,0.5,0]))*
                                            self.voxel_dimension)+
                                           self.voxel_zero)

                            #right face (positive x)
                            glNormal3f(1,0,0)
                            glVertex3f(v[5][0], v[5][1], v[5][2])
                            glVertex3f(v[0][0], v[0][1], v[0][2])
                            glVertex3f(v[3][0], v[3][1], v[3][2])
                            glVertex3f(v[4][0], v[4][1], v[4][2])

                            #left face (negative x)
                            glNormal3f(-1,0,0)
                            glVertex3f(v[1][0], v[1][1], v[1][2])
                            glVertex3f(v[6][0], v[6][1], v[6][2])
                            glVertex3f(v[7][0], v[7][1], v[7][2])
                            glVertex3f(v[2][0], v[2][1], v[2][2])

                            #top face (positive y)
                            glNormal3f(0,1,0)
                            glVertex3f(v[0][0], v[0][1], v[0][2])
                            glVertex3f(v[5][0], v[5][1], v[5][2])
                            glVertex3f(v[6][0], v[6][1], v[6][2])
                            glVertex3f(v[1][0], v[1][1], v[1][2])

                            #bottom face (negative y)
                            glNormal3f(0,-1,0)
                            glVertex3f(v[3][0], v[3][1], v[3][2])
                            glVertex3f(v[2][0], v[2][1], v[2][2])
                            glVertex3f(v[7][0], v[7][1], v[7][2])
                            glVertex3f(v[4][0], v[4][1], v[4][2])

                            #back face (positive z)
                            glNormal3f(0,0,1)
                            glVertex3f(v[6][0], v[6][1], v[6][2])
                            glVertex3f(v[5][0], v[5][1], v[5][2])
                            glVertex3f(v[4][0], v[4][1], v[4][2])
                            glVertex3f(v[7][0], v[7][1], v[7][2])

                            #front face (negative z)
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
            glEndList()
            self.voxel_list = True
        glCallList(self.obj_id*10 + 1)




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
        voxel_span = [int(voxel_span[0]+0.5), int(voxel_span[1]+0.5), 
                int(voxel_span[2]+0.5)]

        self.voxel_dimension = cube_dimension
        self.voxel_zero = min_vertex_pos

        print ("Creating voxelized object with resolution: ("+
                str(voxel_span[0])+","+str(voxel_span[1])+","+
                str(voxel_span[2])+")")

        #Go through 2D array of x,y and shoot ray in z direction
        total_iterations = voxel_span[0]*voxel_span[1]
        for i in xrange(0, int(voxel_span[0])):
            if i not in self.voxelized:
                self.voxelized[i] = {}
            for j in xrange(0, int(voxel_span[1])):
                if j not in self.voxelized[i]:
                    self.voxelized[i][j] = {}
                center = (array([i+0.5, j+0.5, -0.5])*cube_dimension+
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
                intersections = map(lambda x: (x[0]/cube_dimension,x[1]), 
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
                        print ("Something went wrong - winding number > 0 "+
                        "after all intersections... Setting it to 0")
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
        print "Created voxelized object!"

    def removeInnerVoxels(self):
        #Tag the outside voxels, then run modified Kruskal's 
        #to find tree spanning all tagged voxels, traversing paths of least
        #cost through untagged voxels, if need be.
        #Essentially, we want to create an outer shell of voxels.
        print "unimplemented"

    def findConnections(self):
        #Loop through voxels then create pointers from each voxel to its
        #neighbors
        print "unimplemented"