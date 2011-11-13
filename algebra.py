from numpy import *

def ortho_proj(vec4):
    if len(vec4) == 4:
        return (vec4/vec4[3])[:-1]
    return vec4

