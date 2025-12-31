# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""Geometric primitives
"""

import numpy as np


def circle(center, normal, radius, num_points=32, end_point=True, perp=None, toffset=0):
    """Generate points approximating a 3D circle.

    Parameters
    ----------
    center : array_like, shape (3,)
        Cartesian coordinates of the circle center.
    normal : array_like, shape (3,)
        Vector normal to the plane of the circle. Need not be unit length; it
        will be normalized internally.
    radius : float
        Radius of the circle.
    num_points : int, optional
        Number of points used to approximate the circle. Default is 32.
    end_point : bool, optional
        If True (default), the returned point sequence includes the start point
        again at the end (closed loop). 

    Returns
    -------
    points : ndarray, shape (num_points, 3)
        Ordered sequence of 3D points lying on the circle.

    Notes
    -----
    The function constructs an orthonormal basis in the plane orthogonal to `normal`. 
    If `normal` is (near) zero, behavior is undefined and the caller should provide a valid normal.
    """

    # In a e_1, e_2, e_3 basis where n = e_1 and the origin is at center, 
    # the coordinates of the unit circle are given by cos(t) e_2 + sin(t) e_3

    # Determine orthonormal basis
    e_1 = np.asarray(normal)
    e_1 *= 1.0/np.linalg.norm(e_1)
        
    # A second vector can be obtained as the cross product 
    # between e_1 = (x, y, z) and a test vector chosen as u = (1, 0, 0)
    # with the result e_2 = (0, z, -y). If u = (0, 1, 0) then e_2 = (-z, 0, x)
    # which is used if e_1 is collinear with (1, 0, 0)
    if perp is None:
        if np.abs(e_1[0]) > 0.9:
            e_2 = np.array((-e_1[2], 0.0, e_1[0]))
        else:
            e_2 = np.array((0.0, e_1[2], -e_1[1]))
    else:
        e_2 = np.asarray(perp)

    e_2 *= 1.0/np.linalg.norm(e_2)
    
    e_3 = np.cross(e_1, e_2)

    # Angles
    theta = toffset + np.linspace(0.0, 2.0*np.pi, num_points, endpoint=end_point)
    
    return center + np.outer(radius*np.cos(theta), e_2) + np.outer(radius*np.sin(theta), e_3)