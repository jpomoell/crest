# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""Map sequence plot user interface components
"""

import solara

from .plot import MapSequencePlotContainer



@solara.component
def MapSequencePlotUIWithFrame(plot: MapSequencePlotContainer, 
                               frame: solara.Reactive[int],
                               difference_frame: solara.Reactive[int],
                               vmin: solara.Reactive[float | None],
                               vmax: solara.Reactive[float | None],
                               cmap: solara.Reactive[str],
                               on_activate,
                               is_active: bool,
                               allow_frame_change: bool,
                               on_frame_change                        
                               ):
    

    # Create the figure only once
    fig, ax, im, cbar = solara.use_memo(plot.create, dependencies=[])
    
    # Update the plot when the frame is changed
    def update():
        if len(plot.modifiers) > 1:
            raise ValueError("Currently only a single modifier is supported")
        
        plot.modifiers[0].is_enabled = (difference_frame.value >= 0)
        plot.modifiers[0].reference_frame = difference_frame.value
        
        plot.colorbar_state.cmap = cmap.value
        plot.colorbar_state.vmin = vmin.value
        plot.colorbar_state.vmax = vmax.value

        plot.update_to_frame(frame.value)

    #update()

    solara.use_effect(update,
                      dependencies=[frame.value, 
                                    difference_frame.value,
                                    vmin.value, vmax.value, 
                                    cmap.value
                                    ])
   

    # Use a different border color depending on if this plot is active or not
    border_color = "rgba(245, 40, 145, 0.75)" if is_active else "rgba(32, 150, 243, 0.25)"

    with solara.Column(style={"border" : f"3px solid {border_color}", 
                              "borderRadius": "4px", 
                              "padding": "6px", 
                              #"maxHeight" : "800px" # 80% of screen height
                              }):
        
        # Button to make this plot the active plot
        solara.Button(label=plot.map_sequence[frame.value].name, 
                      text=True, ripple=False,
                      style={"justifyContent": "flex-start", "textAlign": "left", "padding": "0px"},
                      on_click=lambda: on_activate())
        
        # Slider to change the frame
        solara.SliderInt(label="Frame",
                         value=frame, 
                         min=0, max=plot.num_frames-1, 
                         disabled=not allow_frame_change,
                         on_value=on_frame_change
                         )
        
        # The figure itself
        solara.Column(style={"padding": "0px", "margin": "0px", "width": "100%", "height": "100%", "overflow": "auto"}, 
                      children=[fig.canvas])
