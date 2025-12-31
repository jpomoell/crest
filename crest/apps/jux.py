# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""App for juxtaposing models and imaging observations
"""

import datetime
from typing import List
import numpy as np
import solara

import astropy
import sunpy
import sunpy.map

import crest.components.containers.panel
import crest.components.containers.daccordions
import crest.components.plot.map_sequence.plot
import crest.components.plot.map_sequence.ui

import crest.models.gcs


@solara.component
def DifferenceController(frames,
                         difference_frames,
                         running_difference_offsets,
                         image_modifiers,
                         datetimes,
                         num_frames,
                         active_plot):
    
    idx = active_plot.value
    
    mode = image_modifiers[idx]

    # Image modification options
    solara.Select(
        label="Image modifier",
        value=mode,
        values=["None", "Fixed difference", "Running difference"],        
    )

    if mode.value != "None":

        # Slider to select the difference image
        solara.SliderInt(
            label="Difference frame",
            value=difference_frames[idx],
            min=0,
            max=num_frames[idx] - 1,
            disabled=running_difference_offsets[idx].value != 0
        )

        # Display the time of the difference image (unless disabled)
        if difference_frames[idx].value >= 0:
            
            _datetime = datetimes[idx][difference_frames[idx].value]

            solara.Markdown(f"Diff. frame time: {_datetime.replace(microsecond=0).isoformat().replace("T", " ")}",
                            style={"color" : "hsla(0, 0%, 100%, .7)"})
                

    if mode.value == "None":
        
        # Set the running difference offset to 0 (i.e. off)
        running_difference_offsets[idx].set(0)
        
        # Set the difference frame to -1 (i.e. no difference frame) 
        if difference_frames[idx].value != -1:
            difference_frames[idx].set(-1)
    
    elif "Fixed" in mode.value:

        # Set the running difference offset to 0 (i.e. off)
        running_difference_offsets[idx].set(0)
        
    else:

        # Default offset for running difference
        if running_difference_offsets[idx].value == 0:
            running_difference_offsets[idx].set(1)

        solara.InputInt(label="Offset from current image", 
                        value=running_difference_offsets[idx].value,
                        on_value=lambda v, r=running_difference_offsets[idx]: r.set(v),
                        continuous_update=True,
                        #dense=True, 
                        style={"maxWidth": "150px"},
                        )
        
        # The offset from the current image: difference = image[current] - image[current + offset]
        offset = running_difference_offsets[idx].value
        
        target = frames[idx].value + offset     
        target = max(0, min(target, num_frames[idx] - 1))

        # Update reference frame only when needed
        if difference_frames[idx].value != target:
            difference_frames[idx].set(target)



class ImagesAndModels:

    def __init__(self, 
                 map_sequences: List[sunpy.map.MapSequence], 
                 columns: int=2):

        # Data sources == sequence of MapSequence objects
        self.sources = map_sequences

        # The models that are to be included in the menu
        self.model_types \
            = {"GCS" : crest.models.gcs.GraduatedCylindricalShell}

        # Reactive map of instantiated models
        self.models = solara.reactive({})


        # Colormap options
        cmap_options = ["gray", "bwr", "RdBu", "RdGy", "bone", "twilight", "coolwarm", "seismic", "viridis", "magma", "inferno", "jet"]
        cmap_options.sort(key=str.lower)
        cmap_options.insert(0, "default")

        # Number of plots to be created == number of data sources
        num_plots = len(self.sources)

        # Datetime objects of each map of each source
        datetimes = list()
        for source in self.sources:
            datetimes.append(np.array([m.date.datetime for m in source.maps]))

        # Get min and max of data for each source
        data_min = list()
        data_max = list()
        
        for source in self.sources:
            data_min.append(np.min([np.min(m.data) for m in source.maps]))
            data_max.append(np.max([np.max(m.data) for m in source.maps]))
                
        # Get units of the data in each map
        map_units = list()
        for source in self.sources:
            map_units.append(source.maps[0].unit)
        
        # Number of frames (maps) in each source
        num_frames = [len(source) for source in self.sources]


        _debug = False

        @solara.component
        def ui():
            
            # Helper functions
            def get_date_of_map(m):
                return m.date.datetime.date()

            def get_time_of_map(m):
                return m.date.datetime.time().replace(microsecond=0)    
            
            def str_from_date_and_time(date, time):
                return datetime.datetime.combine(date, time).isoformat().replace("T", " ")

            
            # Create a plot container for each map sequence
            plot_containers = solara.use_memo(
                lambda: [crest.components.plot.map_sequence.plot.MapSequencePlotContainer(self.sources[idx]) for idx in range(num_plots)], 
                dependencies=[])
            
            # The currently active plot
            active_plot = solara.use_reactive(0)

            # The current frame in each plot            
            frames = [solara.use_reactive(0) for _ in range(num_plots)]
            
            # Sync plots to be as close as possible in time?
            sync_plots = solara.use_reactive(False)

                        
            # The difference frame of each plot            
            difference_frames = [solara.use_reactive(-1) for _ in range(num_plots)]
            
            # The offset used in constructing running difference images
            running_difference_offsets = [solara.use_reactive(0) for _ in range(num_plots)]

            # Which image modifier is active
            image_modifiers = [solara.use_reactive("None") for _ in range(num_plots)]

            # Colorbar min of each plot
            vmins = [solara.use_reactive(data_min[_i]) for _i in range(num_plots)]
            
            # Colorbar max of each plot
            vmaxs = [solara.use_reactive(data_max[_i]) for _i in range(num_plots)]

            # Colormap of each plot
            cmaps = [solara.use_reactive("default") for _ in range(num_plots)]

            # The active date
            active_date = solara.use_reactive(get_date_of_map(self.sources[0].maps[0]))

            # The active time            
            active_time = solara.use_reactive(get_time_of_map(self.sources[0].maps[0]))


            # Reactive dict keeping track of all the created models
            models = self.models

          
            # Handle frame change
            def on_frame_change(frame, idx_of_plot):
                
                # Only when plot synchronization is on do frame changes need to
                # be taken care of explicitly
                if sync_plots.value:

                    # If the plot from which the frame change is coming from
                    # is not the active plot, nothing is done
                    if idx_of_plot != active_plot.value:
                        return

                    # The target date is the date of the current frame of the active plot
                    target = datetimes[active_plot.value][frame]

                    if frame != frames[active_plot.value].value:
                        raise RuntimeWarning(f"frame not equal to expected frame")

                    # Set the frame of the other plots
                    for pidx in range(num_plots):
                        
                        if pidx == active_plot.value:
                            continue

                        # Find closest frame in time for this plot
                        closest_frame = np.abs((datetimes[pidx] - target)).argmin()

                        # Set the frame
                        frames[pidx].set(closest_frame)

                        # Set also difference frame if running diff is on
                        if running_difference_offsets[pidx].value != 0:

                            target = closest_frame + running_difference_offsets[pidx].value
                            target = max(0, min(target, num_frames[pidx] - 1))

                            difference_frames[pidx].set(target)

            # Handle overlays on the images
            def plot_overlays():
               
                model_points = {}
                model_curves = {}
                model_colors = {}

                for name, model in models.value.items():

                    # Default value: None
                    model_points[name] = None
                    model_curves[name] = None
                    model_colors[name] = model.color                    
                    
                    if model.is_visible and model.do_plot_points:
                        
                        # Create SkyCoords from the model data
                        # NOTE: This assumes that all models are defined in Stonyhurst
                        pts = astropy.coordinates.SkyCoord(
                            *model.points().T,
                            frame=sunpy.coordinates.frames.HeliographicStonyhurst,
                            obstime=datetime.datetime.combine(active_date.value, active_time.value),
                            representation_type='cartesian')
                        
                        model_points[name] = pts

                    if model.is_visible and model.do_plot_curves:
                        
                        skycoord_line_segments = list()

                        for curve in model.curves():

                            skycoord_line_segments.append(
                                astropy.coordinates.SkyCoord(
                                    *curve.T,
                                    frame=sunpy.coordinates.frames.HeliographicStonyhurst,
                                    obstime=datetime.datetime.combine(active_date.value, active_time.value),
                                    representation_type='cartesian')
                            )
                                                
                        model_curves[name] = skycoord_line_segments
                    

                # Plot the points
                for pc in plot_containers:
                    pc.update_overlays(model_points,
                                       model_curves,
                                       model_colors)
            
            _deps = []
            for m in models.value.values():
                _deps.append(m._has_changed.value)
                _deps.append(m.is_visible)
                _deps.append(m.do_plot_points)
                _deps.append(m.do_plot_curves)
                _deps.append(m.color)
                         
            solara.use_effect(plot_overlays, 
                              dependencies=_deps)
           

            with solara.AppLayout():

                with solara.AppBarTitle():
                    solara.Text("Model time: " + str_from_date_and_time(active_date.value, active_time.value),
                                style={"font-size" : "1.2rem", "font-weight" : 500})
                    
                    # Button for toggling dark/light mode
                    # This is currently disabled as this would require to also 
                    # toggle the plt dark/light mode switch which requires a refresh of the axes to take effect
                    #solara.lab.ThemeToggle(enable_auto=False)
                
                # The controllers are placed in the sidebar
                with solara.Sidebar():

                    # Menu for setting the active date and time
                    with solara.Column(gap="0px"):
                        
                        _panel_header_style = "font-weight:500; font-size: 1.15rem; letter-spacing: .0125em; padding:8px"

                        with crest.components.containers.panel.Panel(title="Time", header_style_=_panel_header_style):

                            solara.lab.InputDate(active_date, label="Pick the active date")
                            solara.lab.InputTime(active_time, use_seconds=True, label="Pick the active time")
                        
                            def set_current_plot_time_as_active():
                                
                                # Plot index of the currently active plot
                                plot_idx = active_plot.value

                                # The frame index in the active plot
                                frame_idx = frames[plot_idx].value

                                # Get the map of the currently active plot
                                m = plot_containers[plot_idx].map_sequence[frame_idx]

                                active_date.set(get_date_of_map(m))
                                active_time.set(get_time_of_map(m))
                            
                            solara.Button(label="Reset time to active plot",
                                        on_click=lambda: set_current_plot_time_as_active()
                                        )
                    
                    # Menu for controlling models
                    with solara.Column():
                        with crest.components.containers.panel.Panel(title="Models", header_style_=_panel_header_style):
                            crest.components.containers.daccordions.ModelDynamicAccordion(
                                models, type_map=self.model_types, model_date=active_date, model_time=active_time)
                        

                    # Menu for controlling the active plot
                    with solara.Column():
                        with crest.components.containers.panel.Panel(title="Plot settings", header_style_=_panel_header_style):

                            if _debug:
                                solara.Info("Active plot : " + str(active_plot.value))
                                                
                            # Plot colormap / value limits settings
                            with solara.Row():
                                solara.InputFloat("vmin", 
                                                value=vmins[active_plot.value].value,
                                                on_value=lambda v, r=vmins[active_plot.value]: r.set(v),
                                                continuous_update=True, 
                                                optional=True) 
                                
                                solara.InputFloat("vmax", 
                                                value=vmaxs[active_plot.value].value, 
                                                on_value=lambda v, r=vmaxs[active_plot.value]: r.set(v),                                              
                                                continuous_update=True, 
                                                optional=True)
                                
                            solara.Select(label="Colormap", 
                                            value=cmaps[active_plot.value], 
                                            values=cmap_options)

                    # Menu for controlling the displayed image data
                    with solara.Column():
                        with crest.components.containers.panel.Panel(title="Image data settings", header_style_=_panel_header_style):

                            solara.Checkbox(label="Synchronize images in time", 
                                            value=sync_plots,
                                            on_value=lambda v: on_frame_change(frames[active_plot.value].value, active_plot.value))
                        
                            
                            # Image modifiers and their settings
                            DifferenceController(frames, 
                                                difference_frames, 
                                                running_difference_offsets,
                                                image_modifiers,
                                                datetimes, num_frames, active_plot)
                            
                            if _debug:
                                with solara.Column():
                                    for _idx in range(num_plots):
                                        solara.Markdown(f"Plot {_idx} min = {vmins[_idx].value} max = {vmaxs[_idx].value}")
                        
                
                # Main plot window
                with solara.Column():
                                        
                    # Organize plots in a grid
                    with solara.GridFixed(columns=columns, column_gap='5px', row_gap='5px'):

                        for idx in range(num_plots):
                            
                            # Is this the active plot?
                            is_active = active_plot.value == idx

                            # Allow this plot to change its frame?
                            allow_frame_change = False if (sync_plots.value and not is_active) else True

                            # The plot and associated ui                           
                            crest.components.plot.map_sequence.ui.MapSequencePlotUIWithFrame(
                                plot_containers[idx],
                                frames[idx],
                                difference_frames[idx],
                                vmin=vmins[idx],
                                vmax=vmaxs[idx],
                                cmap=cmaps[idx],
                                on_activate=lambda _idx=idx: active_plot.set(_idx),
                                is_active=is_active,
                                allow_frame_change=allow_frame_change,
                                on_frame_change=lambda v, _idx=idx: on_frame_change(v, _idx)
                            )
                           
                # Fitting parameters
                with solara.Column():
                    
                    for model_name, model in models.value.items():
                        
                        with solara.Details(summary=model_name):

                            with solara.Row():
                                #solara.Markdown(model.param_records.value.to_markdown())
                                solara.DataFrame(model.param_records.value, items_per_page=5, scrollable=True)

                                file_object = model.param_records.value.to_csv(index=False)

                                solara.FileDownload(file_object,
                                                    filename=f"{model_name}.csv", 
                                                    label="Save record", 
                                                    icon_name="mdi-download", 
                                                    mime_type="application/vnd.ms-excel")

        self.ui = ui

    
    def launch(self):
        return solara.display(self.ui())