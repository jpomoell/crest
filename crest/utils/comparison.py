# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""Utilities for comparing various objects
"""

import math
import datetime


def dicts_equal(d1, d2, comparators=None):
    comparators = comparators or {}

    if d1.keys() != d2.keys():
        return False

    for k in d1:
        v1, v2 = d1[k], d2[k]
        cmp_fn = comparators.get(type(v1))

        if cmp_fn:
            if not cmp_fn(v1, v2):
                return False
        else:
            if v1 != v2:
                return False

    return True
