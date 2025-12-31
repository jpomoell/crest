# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""Image modifiers base class
"""


import sunpy.map


class ImageModifierBase:
    """Base class for map modifiers. Not required but useful."""
    name = "BaseModifier"

    def __init__(self):
        self._is_enabled = False

    def __call__(self, m: sunpy.map.Map, container):
        raise NotImplementedError

    @property
    def is_enabled(self):
        return self._is_enabled

    @is_enabled.setter
    def is_enabled(self, value):
        self._is_enabled = bool(value)