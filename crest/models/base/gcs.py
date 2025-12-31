# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""The graduated cylindrical shell (GCS) model
"""

from typing import Optional

import numpy as np
from astropy import units
from astropy.units import Quantity

from crest.utils.transform import RotationTransform



class GCSGeometry:
    """Geometry implementation of the graduated cylindrical shell (GCS) model.
    
    Implements the basic geometry of the GCS model as described by 
    A. Thernisien ApJS 194, 2011 (https://doi.org/10.1088/0067-0049/194/2/33). 
    The model is constructed in the coordinate system of T11 (see, e.g., Figure 1)
    with the generating circle in the z=0 plane and the leading edge (apex) of the 
    shell at (x,y,z) = (0, OH, 0).
    
    Attributes:
    -----------
    half_angle
        Angle between the line to the front and the center of the leg.
                       Equivalent to angle alpha in Figure 1 of T11.
    aspect_ratio
        The rate of lateral expansion wrt height of the shell geometry.        
    cone_length
        Height of the leg cone. Equivalent to the distance OD in Figure 1.
    """

    @units.quantity_input
    def __init__(self,
                 half_angle: Quantity[units.rad], 
                 aspect_ratio: Quantity[units.dimensionless_unscaled],
                 *,
                 leading_edge: Optional[Quantity[units.m]] = None, 
                 cone_height: Optional[Quantity[units.m]] = None):
        """Initialize the geometry
        """
        
        # Set half angle
        self._half_angle = half_angle.to(units.rad)

        # Set aspect ratio
        if isinstance(aspect_ratio, Quantity):
            self._aspect_ratio = aspect_ratio.value
        else:
            self._aspect_ratio = aspect_ratio

        if (leading_edge is None) and (cone_height is None):
            raise ValueError("Leading edge or cone height need to be provided")

        if (leading_edge is not None) and (cone_height is not None):
            raise ValueError("Leading edge or cone height need to be provided")

        # Set leading edge and cone height using the setters
        if leading_edge is None:

            # Set cone height and leading edge using the provided value 
            # of the cone height
            self.cone_height = cone_height            
        
        else:

            # Set the leading edge height and cone height using the provided
            # value of the leading edge
            self.leading_edge = leading_edge
        

    @staticmethod
    @units.quantity_input
    def compute_cone_height(half_angle: Quantity[units.rad], 
                            aspect_ratio: float,
                            leading_edge: Quantity[units.m]):

        _alpha = half_angle.to_value(units.rad)
        
        return leading_edge*np.cos(_alpha)*(1.0 - aspect_ratio)/(1.0 + np.sin(_alpha))

    @staticmethod
    @units.quantity_input
    def compute_leading_edge(half_angle: Quantity[units.rad], 
                             aspect_ratio: float,
                             cone_height: Quantity[units.m]):

        _alpha = half_angle.to_value(units.rad)
        
        return cone_height*(1.0 + np.sin(_alpha))/(np.cos(_alpha)*(1.0 - aspect_ratio))
    
    @property
    def half_angle(self) -> Quantity[units.rad]:
        """The half angle of the model
        """
        return self._half_angle
    
    @half_angle.setter
    @units.quantity_input
    def half_angle(self, value: Quantity[units.rad]):

        self._half_angle = value

        # To maintain the leading edge, reset the leading edge
        self.leading_edge = self._leading_edge

    @property
    def aspect_ratio(self) -> float:
        """The aspect ratio of the model
        """
        return self._aspect_ratio
    
    @aspect_ratio.setter
    @units.quantity_input
    def aspect_ratio(self, value: Quantity[units.dimensionless_unscaled]):

        # Set the aspect ratio as a pure float
        if isinstance(value, Quantity):
            self._aspect_ratio = value.value
        else:
            self._aspect_ratio = value
   
        # To maintain the leading edge, reset the leading edge
        self.leading_edge = self._leading_edge

    @property
    def cone_height(self) -> Quantity[units.m]:
        """Height of the conical leg 
        """
        return self._cone_height

    @cone_height.setter
    @units.quantity_input
    def cone_height(self, value: Quantity[units.m]):

        # Set the new value
        self._cone_height = value

        # Compute and set the new leading edge value
        self._leading_edge \
            = GCSGeometry.compute_leading_edge(self.half_angle, self.aspect_ratio, cone_height=value)

    @property 
    def leading_edge(self) -> Quantity[units.m]:
        """Leading edge height
        """
        return self._leading_edge
    
    @leading_edge.setter
    @units.quantity_input
    def leading_edge(self, value: Quantity[units.m]):

        # Set the new leading edge value
        self._leading_edge = value
        
        # Compute and set the new cone height
        self._cone_height \
            = GCSGeometry.compute_cone_height(self.half_angle, self.aspect_ratio, leading_edge=value)

    @property
    def h(self) -> Quantity[units.m]:
        """Height of the conical leg
        """
        return self._cone_height
    
    @property
    def rho(self) -> Quantity[units.m]:
        """Radius of the generating circle, Eq. 6 in T11
        """
        return self.h*np.tan(self.half_angle.to_value(units.rad))

    @property
    def b(self) -> Quantity[units.m]:
        """The y-coordinate of the center-point of the generating circle, Eq. 4 in T11
        """
        return self.h/np.cos(self.half_angle.to_value(units.rad))

    @property
    def delta(self) -> Quantity[units.rad]:
        """The cone opening angle, Eq. 1 in T11
        """
        return np.arcsin(self.aspect_ratio)*units.rad

    @property
    def OC1(self) -> Quantity[units.m]:
        """Distance of the apex center, Eq. 28 in T11
        """
        return (self.b + self.rho)/(1.0 - self.aspect_ratio**2)

    @property
    def OH(self) -> Quantity[units.m]:
        """Leading edge height
        """
        return self.leading_edge
    
    @units.quantity_input
    def X0(self, beta: Quantity[units.rad]) -> Quantity[units.m]:
        """Coordinate x of the origin of the local circle, Eq. 18 in T11
        """
        k_sqr = self.aspect_ratio**2

        return (self.rho + self.b*k_sqr*np.sin(beta.to_value(units.rad)))/(1.0 - k_sqr)

    @units.quantity_input
    def R(self, beta: Quantity[units.rad]) -> Quantity[units.m]:
        """Radius of the local circle, Eq. 19 in T11
        """

        b, X0, rho, k_sqr = self.b, self.X0(beta), self.rho, self.aspect_ratio**2
        
        R_sqr = X0**2 + (k_sqr*b*b - rho*rho)/(1.0 - k_sqr)

        return np.sqrt(R_sqr)

    @units.quantity_input
    def cross_section_circle(self, beta: Quantity[units.rad]):
        
        _beta = beta.to_value(units.rad)
        _hang = self.half_angle.to_value(units.rad)

        # In the RHS leg?
        in_rhs_leg = (_beta >= -0.5*np.pi) and (_beta <= -_hang)
        
        # In the LHS leg?
        in_lhs_leg = (_beta >= (np.pi + _hang) and (_beta <= 3.0*np.pi/2.0))

        # In the curved art?
        in_curved_section = (_beta > -_hang) and (_beta < (np.pi + _hang))

        
        center = np.zeros(3)*units.m
        normal = np.zeros(3)
        
        if in_rhs_leg:

            OQ = self.h - self.rho*np.tan(-(_beta + _hang))

            radius = OQ*np.tan(self.delta.to_value(units.rad))

            center[0] = OQ*np.sin(_hang)
            center[1] = OQ*np.cos(_hang)
            
            normal[0] = np.sin(_hang)
            normal[1] = np.cos(_hang)

        elif in_lhs_leg:

            OQ = self.h - self.rho*np.tan(_beta -_hang - np.pi)

            radius = OQ*np.tan(self.delta)

            center[0] = -OQ*np.sin(_hang)
            center[1] = OQ*np.cos(_hang)
            
            normal[0] = np.sin(_hang)
            normal[1] = -np.cos(_hang)

        elif in_curved_section:

            radius = self.R(beta)

            center[0] = self.X0(beta)*np.cos(_beta)
            center[1] = self.X0(beta)*np.sin(_beta) + self.b

            normal[0] = -np.sin(_beta)
            normal[1] =  np.cos(_beta)

        else:
            raise ValueError(f"Unexpected beta angle {beta.to_value(units.deg)}")
        
        return center, radius, normal



class GCSModel(GCSGeometry):

    @units.quantity_input
    def __init__(self,
                 half_angle: Quantity[units.rad], 
                 aspect_ratio: Quantity[units.dimensionless_unscaled],
                 leading_edge: Optional[Quantity[units.m]],
                 longitude: Quantity[units.rad] = 0*units.rad,
                 latitude: Quantity[units.rad] = 0*units.rad,
                 tilt: Quantity[units.rad] = 0*units.rad):
                 
        super().__init__(half_angle, aspect_ratio, leading_edge=leading_edge)

        self.longitude = longitude
        self.latitude = latitude
        self.tilt = tilt        
        
    @property
    def longitude(self) -> Quantity[units.rad]:
        return self._longitude

    @property
    def lon(self) -> Quantity[units.rad]:
        return self.longitude
    
    @longitude.setter
    @units.quantity_input
    def longitude(self, value: Quantity[units.rad]):

        # Set longitude value        
        self._longitude = value.to(units.rad)

        # Rotation transform associated with longitude
        self._rot_z = RotationTransform.z(-0.5*np.pi*units.rad + self._longitude)

    @property
    def latitude(self) -> Quantity[units.rad]:
        return self._latitude
    
    @property
    def lat(self) -> Quantity[units.rad]:
        return self.latitude
    
    @property
    def colatitude(self) -> Quantity[units.rad]:
        return 0.5*np.pi*units.rad - self.lat.to(units.rad)
    
    @property
    def clt(self) -> Quantity[units.rad]:
        return self.colatitude
    
    @latitude.setter
    @units.quantity_input
    def latitude(self, value: Quantity[units.rad]):
        
        # Set new latitude value
        self._latitude = value.to(units.rad)

        # Rotation transform associated with latitude
        self._rot_x = RotationTransform.x(self._latitude)

    @property
    def tilt(self) -> Quantity[units.rad]:
        return self._tilt
    
    @tilt.setter
    @units.quantity_input
    def tilt(self, value: Quantity[units.rad]):
        
        # Set new tilt value
        self._tilt = value.to(units.rad)

        # Rotation transform associated with the tilt
        self._rot_y = RotationTransform.y(self._tilt)

    @property
    def tmatrix(self):
        return np.dot(self._rot_z, np.dot(self._rot_y, self._rot_x))