# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""Difference image creators
"""

import copy

from . base import ImageModifierBase


class DifferenceImageModifier(ImageModifierBase):
    """Compute map - reference_map."""
    
    name = "Difference"

    def __init__(self):
        super().__init__()

        self._reference_frame = None

    @property
    def reference_frame(self):
        return self._reference_frame

    @reference_frame.setter
    def reference_frame(self, value):
        self._reference_frame = value

    @property
    def is_valid_reference_frame(self):
        return not (self.reference_frame is None or self.reference_frame < 0)


    def __call__(self, map_meta, map_data, plot_container):

        # Return the map data unchanged if not in a valid state
        if not self.is_enabled or not self.is_valid_reference_frame:
            return map_data

        reference_map = plot_container.map_sequence[self.reference_frame]

        # NOTE: Real-world code may need reprojection here if WCS differ.
        
        return map_data - reference_map.data
        