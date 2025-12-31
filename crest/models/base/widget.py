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


class ModelWidgetBase:
    """Base class for all model widgets
    """

    def __init__(self):

        # The color of the model
        self._color = solara.reactive('#9E9E9E')

        # Is the model visible?
        self._is_visible = solara.reactive(True)

        # Plot overlays
        self._do_plot_curves = solara.reactive(False)
        self._do_plot_points = solara.reactive(False)

        # Has the model changed?
        self._has_changed = solara.reactive(0)

    @property
    def color(self):
        return self._color.value
    
    @property
    def is_visible(self):
        return self._is_visible.value
    
    @property
    def do_plot_points(self):
        return self._do_plot_points.value
        
    @property
    def do_plot_curves(self):
        return self._do_plot_curves.value
    
    def notify_has_changed(self):
        """Setter indicating that the model has changed/has been updated
        """
        self._has_changed.set(self._has_changed.value + 1)