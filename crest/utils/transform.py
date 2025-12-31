# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""Transformation utilities
"""

import numpy as np
import numpy.typing


class RotationTransform:

    @staticmethod
    def x(angle: float) -> numpy.typing.NDArray[np.float64]:
        """Creates a 3x3 matrix representing rotation about the x axis.

        Parameters
        ----------
        angle : float 
            Rotation angle, in radians.

        Returns
        -------
        numpy.ndarray
            The 3x3 rotation matrix
        """

        c, s = np.cos(angle), np.sin(angle)

        return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])

    @staticmethod
    def y(angle: float) -> numpy.typing.NDArray[np.float64]:
        """Creates a 3x3 matrix representing rotation about the y axis.

        Parameters
        ----------
        angle : float 
            Rotation angle, in radians.

        Returns
        -------
        numpy.ndarray
            The 3x3 rotation matrix
        """

        c, s = np.cos(angle), np.sin(angle)

        return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])
    
    @staticmethod
    def z(angle: float) -> numpy.typing.NDArray[np.float64]:
        """Creates a 3x3 matrix representing rotation about the z axis.

        Parameters
        ----------
        angle : float 
            Rotation angle, in radians.

        Returns
        -------
        numpy.ndarray
            The 3x3 rotation matrix
        """

        c, s = np.cos(angle), np.sin(angle)

        return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])