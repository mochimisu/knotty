from numpy import *
from numpy.linalg import *

def ortho_proj(vec4):
    if len(vec4) == 4:
        return (vec4/vec4[3])[:-1]
    return vec4

def ortho_extend(vec3,w):
    return array([vec3[0], vec3[1], vec3[2], w])

def rotation2D(center, angle_deg):
    angle_rad = angle_deg * pi / 180.0
    c = cos(angle_rad)
    s = sin(angle_rad)

    return matrix([ [c, -s, center[0] * (1.0 - c) + center[1] * s],
                    [s, c, center[1] * (1.0 - c) - center[0] * s],
                    [0, 0, 1] ])

def identity3D():
    return matrix([ [1,0,0,0],
                    [0,1,0,0],
                    [0,0,1,0],
                    [0,0,0,1]])

def rotation3D(axis, degree):
    angle_rad = degree * pi / 180.0
    c = cos(angle_rad)
    s = sin(angle_rad)
    t = 1.0 - c
    axis = axis / norm(axis)
    return matrix([ [t*axis[0]*axis[0]+c, 
              t*axis[0]*axis[1]-s*axis[2],
              t*axis[0]*axis[2]+s*axis[1],
              0],
             [t*axis[0]*axis[1]+s*axis[2],
              t*axis[1]*axis[1]+c,
              t*axis[1]*axis[2]-s*axis[0],
              0], 
             [t*axis[0]*axis[2]-s*axis[1],
              t*axis[1]*axis[2]+s*axis[0],
              t*axis[2]*axis[2]+c,
              0],
             [0,0,0,1] ])

def scaling3D(scale_vector):
    return matrix([ [scale_vector[0], 0, 0, 0],
                    [0, scale_vector[1], 0 ,0],
                    [0, 0, scale_vector[2], 0],
                    [0, 0, 0, 1] ])

def translation3D(trans_vec):
    return matrix([ [1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [0, 0, 1, 0],
                    [trans_vec[0], trans_vec[1], trans_vec[2], 1] ])
