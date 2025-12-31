# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""The model widget base class
"""

import dataclasses

from astropy import units

import solara



@dataclasses.dataclass
class NumericParameter:
    """Specification of a numeric model parameter.

    Container for representing the metadata of a numeric model parameter.

    Attributes
    ----------
    label : str
        Descriptive name for the parameter.
    default : float 
        Default numeric value for the parameter.
    min : float 
        Minimum allowed value.
    max : float
        Maximum allowed value.
    step : float 
        Increment step for adjustments (e.g., for sliders or spinboxes).
    unit : astropy.Quantity or astropy.UnitBase 
        Unit associated with the parameter.
    """
    label: str
    default: float
    min: float
    max: float
    step: float
    unit: units.Quantity | units.UnitBase
