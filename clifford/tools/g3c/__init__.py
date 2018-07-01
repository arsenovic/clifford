"""
Tools for 3DCGA (g3c)

3DCGA Tools
==========================================================

Generation Methods
--------------------

.. autosummary::
    :toctree: generated/

    generate_dilation_rotor
    generate_translation_rotor
    random_conformal_point

Misc
--------------------

.. autosummary::
    :toctree: generated/
    
    meet
    intersect_line_and_plane_to_point
    normalise_n_minus_1
    quaternion_and_vector_to_rotor
    get_center_from_sphere
    get_radius_from_sphere
    point_pair_to_end_points
    euc_dist
    dorst_norm_val

Root Finding
--------------------

.. autosummary::
    :toctree: generated/
    
    check_sigma_for_positive_root
    check_sigma_for_negative_root
    check_infinite_roots
    positive_root
    negative_root
    pos_twiddle_root
    neg_twiddle_root
"""

import math
import numba
import numpy as np
from clifford.tools.g3 import quaternion_to_rotor, random_euc_mv
from clifford.g3c import *
import clifford as cf
import warnings

# Allow sytactic alternatives to the standard included in the clifford package
ninf = einf
no = -eo

# Define some useful objects
E = ninf ^ (no)
I5 = e12345
I3 = e123
E0 = ninf ^ -no
E0_val = E0.value
I5_val = I5.value
ninf_val = ninf.value
no_val = no.value
I3_val = I3.value

unit_scalar_mv = 1.0 + 0.0*e1

adjoint_func = layout.adjoint_func
gmt_func = layout.gmt_func
omt_func = layout.omt_func
imt_func = layout.imt_func
rightLaInv = layout.rightLaInv_func


@numba.njit
def project_val(val, grade):
    """ fast grade projection """
    output = np.zeros(32)
    if grade == 0:
        output[0] = val[0]
    elif grade == 1:
        output[1:6] = val[1:6]
    elif grade == 2:
        output[6:16] = val[6:16]
    elif grade == 3:
        output[16:26] = val[16:26]
    elif grade == 4:
        output[26:31] = val[26:31]
    elif grade == 5:
        output[31] = val[31]
    return output


def random_conformal_point(l_max=10):
    """
    Creates a random conformal point
    """
    return up(random_euc_mv(l_max=l_max))


def generate_dilation_rotor(scale):
    """
    Generates a rotor that performs dilation about the origin
    """
    if abs(scale - 1.0) < 0.00001:
        u = np.zeros(32)
        u[0] = 1.0
        return cf.MultiVector(layout, u)
    gamma = math.log(scale)
    return math.cosh(gamma/2) + math.sinh(gamma/2)*(ninf^no)


def generate_translation_rotor(euc_vector_a):
    """
    Generates a rotor that translates objects along the euclidean vector euc_vector_a
    """
    return (1 + ninf * euc_vector_a / 2)


def meet(A, B):
    """
    The meet algorithm as described in "A Covariant Approach to Geometry"
    """
    return I5*((I5*A) ^ (I5*B))


def intersect_line_and_plane_to_point(line, plane):
    """
    Returns the point at the intersection of a line and plane
    If there is no intersection it returns None
    """
    bivector = (meet(line, plane)).normal()
    if (bivector*bivector)[0] > 0:
        return bivector | no
    else:
        return None


def normalise_n_minus_1(mv):
    """
    Normalises a conformal point so that it has an inner product of -1 with einf
    """
    scale = (mv|ninf)[0]
    if scale != 0.0:
        return -mv/scale
    else:
        raise ZeroDivisionError('Multivector has 0 einf component')


def quaternion_and_vector_to_rotor(quaternion, vector):
    """
    Takes in a quaternion and a vector and returns a conformal rotor that
    implements the transformation
    """
    rotation = quaternion_to_rotor(quaternion)
    translation = generate_translation_rotor(
        vector[0] * e1 + vector[1] * e2 * vector[3] * e3)
    return translation * rotation


def get_center_from_sphere(sphere):
    """
    Returns the conformal point at the centre of a sphere by reflecting the
    point at infinity
    """
    center = sphere * ninf * sphere
    return center


def get_radius_from_sphere(sphere):
    """
    Returns the radius of a sphere
    """
    dual_sphere = sphere * I5
    dual_sphere = dual_sphere / (-dual_sphere | ninf)
    return math.sqrt(abs(dual_sphere * dual_sphere))


def point_pair_to_end_points(T):
    """
    Extracts the end points of a point pair bivector
    """
    beta = math.sqrt(abs((T * T)[0]))
    F = T / beta
    P = 0.5 * (1 + F)
    P_twiddle = 0.5 * (1 - F)
    A = normalise_n_minus_1(-P_twiddle * (T | ninf))
    B = normalise_n_minus_1(P * (T | ninf))
    return A, B




def euc_dist(conf_mv_a, conf_mv_b):
    """ Returns the distance between two conformal points """
    dot_result = (conf_mv_a|conf_mv_b)[0]
    if dot_result < 0.0:
        return math.sqrt(-2.0*dot_result)
    else:
        return 0.0




def dorst_norm_val(sigma):
    """ Square Root of Rotors - Implements the norm of a rotor"""
    return math.sqrt(sigma[0] ** 2 - (sigma(4) ** 2)[0])


def check_sigma_for_positive_root(sigma):
    """ Square Root of Rotors - Checks for a positive root """
    return sigma[0] + dorst_norm_val(sigma) > 0


def check_sigma_for_negative_root(sigma):
    """ Square Root of Rotors - Checks for a negative root """
    return sigma[0] - dorst_norm_val(sigma) > 0


def check_infinite_roots(sigma):
    """ Square Root of Rotors - Checks for a infinite roots """
    return sigma[0] + dorst_norm_val(sigma) < 0.0000000001


def positive_root(sigma):
    """
    Square Root of Rotors - Evaluates the positive root
    TODO: Dig out the full name of this paper and authors
    """
    norm_s = dorst_norm_val(sigma)
    return (sigma + norm_s) / (math.sqrt(2) * math.sqrt(sigma[0] + norm_s))


def negative_root(sigma):
    """ Square Root of Rotors - Evaluates the negative root """
    norm_s = dorst_norm_val(sigma)
    return (sigma - norm_s) / (math.sqrt(2) * math.sqrt(sigma[0] - norm_s))


def neg_twiddle_root(C):
    """
    Hadfield and Lasenby AGACSE2018
    Return a valid object from the addition result C
    """
    sigma = -(C * ~C)
    if check_sigma_for_positive_root(sigma):
        k = positive_root(sigma)
        C3 = ((1. / k) * C).normal()
        return [C3]
    elif check_sigma_for_negative_root(sigma):
        k = positive_root(sigma)
        C3 = ((1. / k) * C).normal()

        k2 = negative_root(sigma)
        C4 = ((1. / k2) * C).normal()
        return [C3, C4]
    elif check_infinite_roots(sigma):
        #warnings.warn('Infinite roots detected: sigma = ' + str(sigma), RuntimeWarning)
        return [C.normal()]
    else:
        raise ValueError('No root exists')


def pos_twiddle_root(C):
    """
    Hadfield and Lasenby AGACSE2018
    Return a valid rotor from the (1 + C2C1) result C
    """
    sigma = (C * ~C)
    if check_sigma_for_positive_root(sigma):
        k = positive_root(sigma)
        C3 = ((1. / k) * C).normal()
        return [C3]
    elif check_sigma_for_negative_root(sigma):
        k = positive_root(sigma)
        C3 = ((1. / k) * C).normal()

        k2 = negative_root(sigma)
        C4 = ((1. / k2) * C).normal()
        return [C3, C4]
    elif check_infinite_roots(sigma):
        #warnings.warn('Infinite roots detected: sigma = ' + str(sigma), RuntimeWarning)
        return [C.normal()]
    else:
        raise ValueError('No root exists')



def square_roots_of_rotor(R):
    """
    Square Root and Logarithm of Rotors
    in 3D Conformal Geometric Algebra
    Using Polar Decomposition
    Leo Dorst and Robert Valkenburg
    """
    return pos_twiddle_root(1 + R)


def interp_objects_root(C1, C2, alpha):
    """
    Hadfield and Lasenby, Direct Linear Interpolation of Geometric Objects, AGACSE2018
    Directly linearly interpolates conformal objects
    """
    C = alpha * C1 + (1 - alpha) * C2
    return (neg_twiddle_root(C)[0]).normal()


def average_objects(obj_list):
    """
    Hadfield and Lasenby, Direct Linear Interpolation of Geometric Objects, AGACSE2018
    Directly averages conformal objects
    """
    C = sum(obj_list) / len(obj_list)
    return (neg_twiddle_root(C)[0]).normal()


def rotor_between_objects(C1, C2):
    """
    Hadfield and Lasenby AGACSE2018
    For any two conformal objects C1 and C2 this returns a rotor that takes C1 to C2
    """
    if float((C1 * C1)[0]) > 0:
        C = 1 + (C2 * C1)
        R = pos_twiddle_root(C)[0]
        return R
    else:
        return (1 - (C2 * C1)).normal()


def random_bivector():
    """
    Creates a random bivector on the form described by R. Wareham in
    TODO: Dig out the name of the interpolation paper

    $$ B =  ab + c*n_{\inf}$$ where $a, b, c \in \mathcal(R)^3$
    """
    a = random_euc_mv()
    c = random_euc_mv()
    return a * I3 + c * ninf


def random_point_pair():
    """
    Creates a random point pair bivector object
    """
    mv_a = random_euc_mv()
    mv_b = random_euc_mv()
    pp = ((up(mv_a) ^ up(mv_b))).normal()
    return pp


def random_line():
    """
    Creates a random line
    """
    mv_a = random_euc_mv()
    mv_b = random_euc_mv()
    line_a = ((up(mv_a) ^ up(mv_b) ^ ninf)).normal()
    return line_a


def random_circle():
    """
    Creates a random circle
    """
    mv_a = random_euc_mv()
    mv_b = random_euc_mv()
    mv_c = random_euc_mv()
    line_a = ((up(mv_a) ^ up(mv_b) ^ up(mv_c))).normal()
    return line_a


def random_sphere():
    """
    Creates a random sphere
    """
    mv_a = random_euc_mv()
    mv_b = random_euc_mv()
    mv_c = random_euc_mv()
    mv_d = random_euc_mv()
    sphere = ((up(mv_a) ^ up(mv_b) ^ up(mv_c) ^ up(mv_d))).normal()
    return sphere


def random_plane():
    """
    Creates a random plane
    """
    line_a = ((random_circle() ^ ninf)).normal()
    return line_a


@numba.njit
def val_apply_rotor(mv_val, rotor_val):
    """ Applies rotor to multivector in a fast way - JITTED """
    return gmt_func(rotor_val, gmt_func(mv_val, adjoint_func(rotor_val)))

def apply_rotor(mv_in, rotor):
    """ Applies rotor to multivector in a fast way """
    return cf.MultiVector(layout, val_apply_rotor(mv_in.value, rotor.value))


@numba.njit
def mult_with_ninf(mv):
    """ Convenience function for multiplication with ninf """
    return gmt_func(mv, ninf_val)


@numba.njit
def val_exp(B_val):
    """ Fast implementation of the exp function - JITTED"""
    t_val = imt_func(B_val, no_val)

    phiP_val = B_val - mult_with_ninf(t_val)
    phi = np.sqrt(-float(gmt_func(phiP_val, phiP_val)[0]))
    P_val = phiP_val / phi

    P_n_val = gmt_func(P_val, I3_val)
    t_nor_val = gmt_func(imt_func(t_val, P_n_val), P_n_val)
    t_par_val = t_val - t_nor_val

    coef_val = np.sin(phi) * P_val
    coef_val[0] += np.cos(phi)

    R_val = coef_val + gmt_func(coef_val, mult_with_ninf(t_nor_val)) + \
        np.sinc(phi/np.pi) * mult_with_ninf(t_par_val)
    return R_val


def ga_exp(B):
    """
    Fast implementation of the exp function
    """
    if np.sum(np.abs(B.value)) < np.finfo(float).eps:
        return cf.MultiVector(layout, unit_scalar_mv.value)
    return cf.MultiVector(layout, val_exp(B.value))


# def convert_2D_polar_line_to_conformal_line(rho, theta):
#     a = np.cos(theta)
#     b = np.sin(theta)
#     x0 = a * rho
#     y0 = b * rho
#     x1 = int(x0 + 10000 * (-b))
#     y1 = int(y0 + 10000 * (a))
#     x2 = int(x0 - 10000 * (-b))
#     y2 = int(y0 - 10000 * (a))
#     return (convert_2D_point_to_conformal(x1,y1)^convert_2D_point_to_conformal(x2,y2)^ninf).normal()


#@numba.njit
def val_convert_2D_polar_line_to_conformal_line(rho, theta):
    a = np.cos(theta)
    b = np.sin(theta)
    x0 = a * rho
    y0 = b * rho
    x1 = int(x0 + 10000 * (-b))
    y1 = int(y0 + 10000 * (a))
    x2 = int(x0 - 10000 * (-b))
    y2 = int(y0 - 10000 * (a))
    p1_val = val_convert_2D_point_to_conformal(x1,y1)
    p2_val = val_convert_2D_point_to_conformal(x2,y2)
    line_val = omt_func(omt_func(p1_val,p2_val),ninf_val)
    line_val = line_val/abs(cf.MultiVector(layout,line_val))
    return line_val


def convert_2D_polar_line_to_conformal_line(rho, theta):
    line_val = val_convert_2D_polar_line_to_conformal_line(rho, theta)
    return cf.MultiVector(layout, line_val)


@numba.njit
def val_up(mv_val):
    temp = np.zeros(32)
    temp[0] = 0.5
    return mv_val - no_val + omt_func(temp, gmt_func(gmt_func(mv_val, mv_val), ninf_val))


def val_distance_point_to_line(point, line):
    """
    Returns the euclidean distance between a point and a line
    """
    return float(abs( cf.MultiVector(layout, omt_func(point,line) )  ))


@numba.njit
def val_convert_2D_point_to_conformal(x,y):
    mv_val = np.zeros(32)
    mv_val[1] = x
    mv_val[2] = y
    return val_up(mv_val)


def convert_2D_point_to_conformal(x,y):
    return cf.MultiVector(layout,val_convert_2D_point_to_conformal(x,y))


def distance_polar_line_to_euc_point_2d(rho, theta, x, y):
    point = val_convert_2D_point_to_conformal(x, y)
    line = val_convert_2D_polar_line_to_conformal_line(rho, theta)
    return val_distance_point_to_line(point, line)

