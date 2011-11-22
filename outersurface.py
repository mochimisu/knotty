from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from objloader import *
from primitives import *

class OuterSurface(object):       
    
    def __init__(self, objloader):
        self.voxels = objloader.voxelized
        self.root_face = None
        self.surface_faces = {}
        self.obj_id = objloader.obj_id
        self.surface_list = False
        self.knots1_list = False
        self.obj_loader = objloader
    
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
        
    def drawSurface(self):
        if not self.surface_list:
            direction_dict = {Directions.POSX: (1, 0, 0),
                              Directions.POSY: (0, 1, 0),
                              Directions.POSZ: (0, 0, 1),
                              Directions.NEGX: (-1, 0, 0),
                              Directions.NEGY: (0, -1, 0),
                              Directions.NEGZ: (0, 0, -1),
                              }
            
            glNewList((self.obj_id * GL_LIST_TOTAL) + GL_LIST_OUTER_SURFACE,
                      GL_COMPILE)
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
            self.surface_list = True
        glCallList(self.obj_id * GL_LIST_TOTAL + GL_LIST_OUTER_SURFACE)
        
    def drawKnots1(self):
        if not self.knots1_list:
            direction_dict = {Directions.POSX: (1, 0, 0),
                              Directions.POSY: (0, 1, 0),
                              Directions.POSZ: (0, 0, 1),
                              Directions.NEGX: (-1, 0, 0),
                              Directions.NEGY: (0, -1, 0),
                              Directions.NEGZ: (0, 0, -1),
                              }
            
            glNewList((self.obj_id * GL_LIST_TOTAL) + GL_LIST_KNOTS_1,
                      GL_COMPILE)
            glPushMatrix()
            glMultMatrixd(self.obj_loader.voxelTransformation())
            
            glBegin(GL_LINES)
            
            for face, dir in self.surface_faces.items():
                dir = direction_dict[dir]
                glNormal3f(dir[0], dir[1], dir[2])
                
                x, y, z = face
                
                if type(x) == float:
                    x = int(x - dir[0]*0.5)
                    sign = 0.2 * (((x + y + z) % 2) - 0.5)
                    
                    glVertex3f(x + (0.5 + sign)*dir[0], y, z)
                    glVertex3f(x + 0.5*dir[0], y-0.5, z)
                    glVertex3f(x + (0.5 + sign)*dir[0] + sign*0.1, y, z)
                    glVertex3f(x + 0.5*dir[0] + sign*0.1, y+0.5, z)
                    
                    glVertex3f(x + (0.5 - sign)*dir[0], y, z)
                    glVertex3f(x + 0.5*dir[0], y, z-0.5)
                    glVertex3f(x + (0.5 - sign)*dir[0], y, z)
                    glVertex3f(x + 0.5*dir[0], y, z+0.5)
                elif type(y) == float:
                    y = int(y - dir[1]*0.5)
                    sign = 0.2 * (((x + y + z) % 2) - 0.5)
                    
                    glVertex3f(x, y + (0.5 + sign)*dir[1], z)
                    glVertex3f(x, y + 0.5*dir[1], z-0.5)
                    glVertex3f(x, y + (0.5 + sign)*dir[1], z)
                    glVertex3f(x, y + 0.5*dir[1], z+0.5)
                    
                    glVertex3f(x, y + (0.5 - sign)*dir[1], z)
                    glVertex3f(x-0.5, y + 0.5*dir[1], z)
                    glVertex3f(x, y + (0.5 - sign)*dir[1], z)
                    glVertex3f(x+0.5, y + 0.5*dir[1], z)
                else:
                    z = int(z - dir[2]*0.5)
                    sign = 0.2 * (((x + y + z) % 2) - 0.5)
                    
                    glVertex3f(x, y, z + (0.5 + sign)*dir[2])
                    glVertex3f(x-0.5, y, z + 0.5*dir[2])
                    glVertex3f(x, y, z + (0.5 + sign)*dir[2])
                    glVertex3f(x+0.5, y, z + 0.5*dir[2])
                    
                    glVertex3f(x, y, z + (0.5 - sign)*dir[2])
                    glVertex3f(x, y-0.5, z + 0.5*dir[2])
                    glVertex3f(x, y, z + (0.5 - sign)*dir[2])
                    glVertex3f(x, y+0.5, z + 0.5*dir[2])
            
            glEnd()
            
            glPopMatrix()
            glEndList()
            self.knots1_list = True
        glCallList(self.obj_id * GL_LIST_TOTAL + GL_LIST_KNOTS_1)
