from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from objloader import *
from primitives import *
from knots import *
from numpy import *
import math

class OuterSurface(object):       
    
    def __init__(self, objloader):
        self.voxels = objloader.voxelized
        self.root_face = None
        self.surface_faces = {}
        self.obj_id = objloader.obj_id
        self.surface_list = None
        self.knots1_list = None
        self.knot = None
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
