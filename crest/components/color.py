# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""Color-related components
"""

import solara


@solara.component
def ColorPicker(color):
    """ColorPicker component
    
    A simple UI component that displays and allows to choose from a small palette of colors.

    Parameters
    ----------
    color : solara.reactive 
        A solara reactive object. The component reads the current color from color and calls 
        set when the user selects a color.
    """
    
    colors = [
        ('red', '#F44336'),
        ('pink', '#E91E63'),
        ('purple', '#9C27B0'),
        ('deep-purple', '#673AB7'),
        ('indigo', '#3F51B5'),
        ('blue', '#2196F3'),
        ('light-blue', '#03A9F4'),
        ('cyan', '#00BCD4'),
        ('teal', '#009688'),
        ('green', '#4CAF50'),
        ('light-green', '#8BC34A'),
        ('lime', '#CDDC39'),
        ('yellow', '#FFEB3B'),
        ('amber', '#FFC107'),
        ('orange', '#FF9800'),
        ('deep-orange', '#FF5722'),
        ('brown', '#795548'),
        ('blue-grey', '#607D8B'),
        ('grey', '#9E9E9E')]
    
    with solara.Column(gap='0px'):
    
        for color_name, color_value in colors:
            
            is_selected = (color.value == color_value)
    
            border = "4px solid rgba(255, 255, 255, 0.5)" if is_selected else "0px solid #FFFFFF"

            solara.Button(
                label=color_name,
                text=True,
                ripple=False,
                on_click=lambda value=color_value: color.set(value),
                style={"background": color_value, "color" : 'rgba(25, 25, 25, 0.65)', "border" : border})
    