import math
from pyglet.gl import *
from math import sin, cos
from past.builtins import xrange
from src.game_config import *


def cube_vertices(x, y, z, n):
    """ Return the vertices of the cube at position x, y, z with size 2*n.

    """
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n,  # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n,  # bottom
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n,  # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n,  # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n,  # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n,  # back
    ]


def get_int_from_float(float_nr):
    return int(math.modf(float_nr)[1])


def tex_coord(x, y, n=4):
    """ Return the bounding vertices of the texture square.

    """
    m = 1.0 / n
    dx = x * m
    dy = y * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m


def tex_coords(top, bottom, side):
    """ Return a list of the texture squares for the top, bottom and side.

    """
    top = tex_coord(*top)
    bottom = tex_coord(*bottom)
    side = tex_coord(*side)
    result = []
    result.extend(top)
    result.extend(bottom)
    result.extend(side * 4)
    return result

def normalize(position):
    """ Accepts `position` of arbitrary precision and returns the block
    containing that position.

    Parameters
    ----------
    position : tuple of len 3

    Returns
    -------
    block_position : tuple of ints of len 3

    """
    x, y, z = position
    x, y, z = (int(round(x)), int(round(y)), int(round(z)))
    return x, y, z


def sectorize(position):
    """ Returns a tuple representing the sector for the given `position`.

    Parameters
    ----------
    position : tuple of len 3

    Returns
    -------
    sector : tuple of len 3

    """
    x, y, z = normalize(position)
    x, y, z = x // SECTOR_SIZE, y // SECTOR_SIZE, z // SECTOR_SIZE
    return x, 0, z


def is_starting_position(x, z, field_size):
    field_size = field_size / 2

    if x in (-field_size + 1, field_size - 1) and z in (-field_size + 1, field_size - 1):
        return True
    if x in (-field_size + 2, field_size - 1) and z in (-field_size + 1, field_size - 1):
        return True
    if x in (-field_size + 1, field_size - 2) and z in (-field_size + 1, field_size - 1):
        return True
    if x in (-field_size + 1, field_size - 1) and z in (-field_size + 2, field_size - 1):
        return True
    if x in (-field_size + 1, field_size - 1) and z in (-field_size + 1, field_size - 2):
        return True

    return False


def get_starting_positions(field_size):
    field_size /= 2
    field_size -= 1

    return [(field_size, -field_size), (-field_size, field_size), (-field_size, -field_size), (field_size, field_size)]


def pythagoras_get_c(a, b):
    return math.sqrt(a ^ 2 + b ^ 2)


def rotate(origin, point, angle):
    """
    Rotate a point by a given angle around a given origin.

    The angle should be given in radians.
    """
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)

    return qx, qy


def get_positions_list():
    n = HALF_OF_FIELD_SIZE
    s = 1  # step size
    y = 0  # initial y height

    result = []

    for x in xrange(-n, n + 1, s):
        for z in xrange(-n, n + 1, s):
            result.append((x, y, z))

    return result


M3D_PI = 3.14159265358979323846
M3D_PI_DIV_180 = M3D_PI / 180.0
M3D_INV_PI_DIV_180 = 57.2957795130823229

M3DVector2f = GLfloat * 2
M3DVector3f = GLfloat * 3  # Vector of three floats (x, y, z)
M3DVector4f = GLfloat * 4
M3DMatrix44f = GLfloat * 16  # A 4 X 4 matrix, column major (floats) - OpenGL style


def m3d_transform_vector3(vOut, v, m):
    vOut[0] = m[0] * v[0] + m[4] * v[1] + m[8] * v[2] + m[12]
    vOut[1] = m[1] * v[0] + m[5] * v[1] + m[9] * v[2] + m[13]
    vOut[2] = m[2] * v[0] + m[6] * v[1] + m[10] * v[2] + m[14]


def m3d_load_identity44(m):
    m[0] = m[5] = m[10] = m[15] = 1.0
    m[1] = m[2] = m[3] = m[4] = 0.0
    m[6] = m[7] = m[8] = m[9] = 0.0
    m[11] = m[12] = m[13] = m[14] = 0.0


# Translate matrix. Only 4x4 matrices supported
def m3d_translate_matrix44(m, x, y, z):
    m[12] += x
    m[13] += y
    m[14] += z


# Scale matrix. Only 4x4 matrices supported
def m3d_scale_matrix44(m, x, y, z):
    m[0] *= x
    m[5] *= y
    m[10] *= z


# Creates a 4x4 rotation matrix, takes radians NOT degrees
def m3d_rotation_matrix44(m, angle, x, y, z):
    s = sin(angle)
    c = cos(angle)
    mag = float((x * x + y * y + z * z) ** 0.5)

    if mag == 0.0:
        # m3dLoadIdentity(m)
        return

    x /= mag
    y /= mag
    z /= mag

    xx = x * x
    yy = y * y
    zz = z * z
    xy = x * y
    yz = y * z
    zx = z * x
    xs = x * s
    ys = y * s
    zs = z * s
    one_c = 1.0 - c

    m[0] = (one_c * xx) + c
    m[1] = (one_c * xy) - zs
    m[2] = (one_c * zx) + ys
    m[3] = 0.0

    m[4] = (one_c * xy) + zs
    m[5] = (one_c * yy) + c
    m[6] = (one_c * yz) - xs
    m[7] = 0.0

    m[8] = (one_c * zx) - ys
    m[9] = (one_c * yz) + xs
    m[10] = (one_c * zz) + c
    m[11] = 0.0

    m[12] = 0.0
    m[13] = 0.0
    m[14] = 0.0
    m[15] = 1.0


# Multiply two 4x4 matricies
def m3d_matrix_multiply44(product, a, b):
    for i in range(0, 4):
        ai0 = a[i]
        ai1 = a[i + (1 << 2)]
        ai2 = a[i + (2 << 2)]
        ai3 = a[i + (3 << 2)]

        product[i] = ai0 * b[0] + ai1 * b[1] + ai2 * b[2] + ai3 * b[3]
        product[i + (1 << 2)] = ai0 * b[0 + (1 << 2)] + ai1 * b[1 + (1 << 2)] + ai2 * b[2 + (1 << 2)] + ai3 * b[
            3 + (1 << 2)]
        product[i + (2 << 2)] = ai0 * b[0 + (2 << 2)] + ai1 * b[1 + (2 << 2)] + ai2 * b[2 + (2 << 2)] + ai3 * b[
            3 + (2 << 2)]
        product[i + (3 << 2)] = ai0 * b[0 + (3 << 2)] + ai1 * b[1 + (3 << 2)] + ai2 * b[2 + (3 << 2)] + ai3 * b[
            3 + (3 << 2)]


# Transpose/Invert - Only 4x4 matricies supported
def m3d_transpose_matrix44(dst, src):
    for j in range(0, 4):
        for i in range(0, 4):
            dst[(j * 4) + i] = src[(i * 4) + j]


def m3d_deg_to_rad(num):
    return (num * M3D_PI_DIV_180)


def m3d_rad_to_deg(num):
    return (num * M3D_INV_PI_DIV_180)


###########################################################
# Cross Product
# u x v = result
# We only need one version for floats, and one version for doubles. A 3 component
# vector fits in a 4 component vector. If  M3DVector4d or M3DVector4f are passed
# we will be OK because 4th component is not used.
def m3d_cross_product(u, v):
    result = M3DVector3f()
    result[0] = u[1] * v[2] - v[1] * u[2]
    result[1] = -u[0] * v[2] + v[0] * u[2]
    result[2] = u[0] * v[1] - v[0] * u[1]
    return result


# Calculates the normal of a triangle specified by the three points
# p1, p2, and p3. Each pointer points to an array of three floats. The
# triangle is assumed to be wound counter clockwise.
def m3d_find_normal(point1, point2, point3):
    # Temporary vectors
    v1 = M3DVector3f()
    v2 = M3DVector3f()

    # Calculate two vectors from the three points. Assumes counter clockwise
    # winding!
    v1[0] = point1[0] - point2[0]
    v1[1] = point1[1] - point2[1]
    v1[2] = point1[2] - point2[2]

    v2[0] = point2[0] - point3[0]
    v2[1] = point2[1] - point3[1]
    v2[2] = point2[2] - point3[2]

    # Take the cross product of the two vectors to get
    # the normal vector.
    return (m3d_cross_product(v1, v2))


def m3d_set_matrix_column44(dst, src, col):
    dst[col * 4] = src[0]
    dst[col * 4 + 1] = src[1]
    dst[col * 4 + 2] = src[2]


#    dst[col * 4 + 3] = src[3]

# Get Square of a vectors length
# Only for three component vectors
def m3d_get_vector_length_squared(u):
    return (u[0] * u[0] + u[1] * u[1] + u[2] * u[2])


def m3d_scale_vector3(v, scale):
    v[0] *= scale
    v[1] *= scale
    v[2] *= scale


# Get length of vector
# Only for three component vectors.
def m3d_get_vector_length(u):
    return (m3d_get_vector_length_squared(u) ** 0.5)


# Normalize a vector
# Scale a vector to unit length. Easy, just scale the vector by it's length
def m3d_normalize_vector(u):
    m3d_scale_vector3(u, 1.0 / m3d_get_vector_length(u))


# Graceless, but duplicating the one from OpenGL SuperBible would be worse, I think?
# Adds a dependency on numpy, also, which is a bummer.
def m3d_invert_matrix44(dst, src):
    try:
        from numpy import matrix
    except ImportError as e:
        print(e)
        # print "You need Numpy."
        import sys
        sys.exit(1)

    mat = matrix([[src[0], src[1], src[2], src[3]],
                  [src[4], src[5], src[6], src[7]],
                  [src[8], src[9], src[10], src[11]],
                  [src[12], src[13], src[14], src[15]]])
    mat = mat.I.tolist()
    dst[0] = mat[0][0]
    dst[1] = mat[0][1]
    dst[2] = mat[0][2]
    dst[3] = mat[0][3]

    dst[4] = mat[1][0]
    dst[5] = mat[1][1]
    dst[6] = mat[1][2]
    dst[7] = mat[1][3]

    dst[8] = mat[2][0]
    dst[9] = mat[2][1]
    dst[10] = mat[2][2]
    dst[11] = mat[2][3]

    dst[12] = mat[3][0]
    dst[13] = mat[3][1]
    dst[14] = mat[3][2]
    dst[15] = mat[3][3]


# Dot Product, only for three component vectors
# return u dot v
def m3d_dot_product(u, v):
    return (u[0] * v[0] + u[1] * v[1] + u[2] * v[2])


# Get plane equation from three points and a normal
# Calculate the plane equation of the plane that the three specified points lay in. The
# points are given in clockwise winding order, with normal pointing out of clockwise face
# planeEq contains the A,B,C, and D of the plane equation coefficients
def m3d_get_plane_equation(p1, p2, p3):
    planeEq = M3DVector4f()
    (v1, v2) = (M3DVector3f(), M3DVector3f())

    # V1 = p3 - p1
    v1[0] = p3[0] - p1[0]
    v1[1] = p3[1] - p1[1]
    v1[2] = p3[2] - p1[2]

    # V2 = P2 - p1
    v2[0] = p2[0] - p1[0]
    v2[1] = p2[1] - p1[1]
    v2[2] = p2[2] - p1[2]

    # Unit normal to plane - Not sure which is the best way here
    planeEq3 = m3d_cross_product(v1, v2)
    m3d_normalize_vector(planeEq3)

    # Back substitute to get D
    planeEq[0] = planeEq3[0]
    planeEq[1] = planeEq3[1]
    planeEq[2] = planeEq3[2]

    planeEq[3] = -(planeEq[0] * p3[0] + planeEq[1] * p3[1] + planeEq[2] * p3[2])

    return planeEq


# Planar shadow Matrix
# Creae a projection to "squish" an object into the plane.
# Use m3dGetPlaneEquationf( point1, point2, point3)
# to get a plane equation.

def m3d_make_planar_shadow_matrix(planeEq, vLightPos):
    proj = M3DMatrix44f()

    # these make the code below easier to read.
    a = planeEq[0]
    b = planeEq[1]
    c = planeEq[2]
    d = planeEq[3]

    dx = -vLightPos[0]
    dy = -vLightPos[1]
    dz = -vLightPos[2]

    # Now build the projection matrix
    proj[0] = b * dy + c * dz
    proj[1] = -a * dy
    proj[2] = -a * dz
    proj[3] = 0.0

    proj[4] = -b * dx
    proj[5] = a * dx + c * dz
    proj[6] = -b * dz
    proj[7] = 0.0

    proj[8] = -c * dx
    proj[9] = -c * dy
    proj[10] = a * dx + b * dy
    proj[11] = 0.0

    proj[12] = -d * dx
    proj[13] = -d * dy
    proj[14] = -d * dz
    proj[15] = a * dx + b * dy + c * dz
    # Shadow matrix ready
    return proj

