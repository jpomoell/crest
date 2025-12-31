# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""Map sequence plotter class
"""

from typing import Optional
import dataclasses
import copy

import numpy as np

import matplotlib
matplotlib.use("module://ipympl.backend_nbagg")

import matplotlib.pyplot
matplotlib.style.use("dark_background")

import astropy
import sunpy.map

import solara


import crest.utils.image.difference



@dataclasses.dataclass
class ColorbarState:
    cmap: Optional[str] = "default"
    vmin: Optional[float] = None
    vmax: Optional[float] = None


class MapSequencePlotContainer:
    """Class that manages a SunPy MapSequence and the figure associated with the map
    """
    
    def __init__(self, map_sequence):
        
        if isinstance(map_sequence, sunpy.map.MapSequence):
            self.map_sequence = map_sequence
        elif isinstance(map_sequence, list):
            self.map_sequence = sunpy.map.MapSequence(map_sequence)
        else:
            raise ValueError("Expected MapSequence or list of Maps")
        
        
        # Plot elements
        self.fig = None
        self.ax = None
        self.im = None
        self.cbar = None

        # Overlay of points
        self.point_overlays = dict()

        # Overlay of curves
        self.curve_overlays = dict()

        # State of the colorbar
        self.colorbar_state = ColorbarState()

        # Index of the map in the sequence that is currently displayed
        self.current_frame_index = 0

        # Image modifier pipeline
        self.modifiers = [
            crest.utils.image.difference.DifferenceImageModifier()
        ]

    @property
    def maps(self):
        return self.map_sequence

    @property
    def num_frames(self):
        """Number of frames in the sequence
        """
        return len(self.map_sequence)

    def get_map_data(self, frame_index):
        """Run map through modifier pipeline.
        """

        # Map meta and image data. 
        # Currently the meta-data is ignored, i.e. modifications are done without regard 
        # to coordinates, units etc!
        map_meta = None
        map_data = np.copy(self.map_sequence[frame_index].data)

        # Run the map data through the modifiers
        for modifier in self.modifiers:
            map_data = modifier(map_meta, map_data, self)
        
        return map_data
    
    def create(self, width=5.0):
        """Create the plot

        width
            Width of figure in inches
        """
        
        # Avoid recreating the figure on component redraws 
        if self.fig is not None:
            return self.fig, self.ax, self.im, self.cbar

        # Get the map to plot, by default starts from index 0
        m = self.map_sequence[self.current_frame_index]
        

        fig = matplotlib.pyplot.figure(figsize=(width, 0.9*width),
                                       facecolor='none',
                                       frameon=False)
        
        # Adjust figure in attempt to minmize surrounding whitespace
        fig.subplots_adjust(left=0.1, right=1.0, bottom=0.1, top=0.99)
        
        # Create figure axes using the axes of the given map
        ax = fig.add_subplot(1, 1, 1, projection=m.wcs)
    
        # Plot the map using the SunPy plotter
        m.plot(axes=ax, title=None)

        # Capture the image created by map.plot
        im = ax.images[-1]

        cbar = fig.colorbar(im, ax=ax, shrink=0.8)
        cbar.ax.tick_params(labelsize=8)
        
        # Initialize overlays
        self.point_overlays = {}
        self.curve_overlays = {}

        #
        # Set various properties of the plot
        #

        #  No grid
        ax.coords.grid(False)

        #   Color behind/around the plot
        ax.set_facecolor('none')
        ax.set_autoscale_on(False)

        #  Reduce fonts
        for d in (0, 1):
            ax.coords[d].set_ticklabel(size=8)
            ax.coords[d].set_axislabel(ax.coords[d].get_axislabel(), size=8)

        ax.margins(0)

        #   Remove the header and footer info provided by ipympl
        fig.canvas.header_visible = False
        fig.canvas.footer_visible = False
        
        #   Set canvas properties to maximally fill the element
        canvas = fig.canvas
        canvas.layout.width = "100%"
        canvas.layout.height = "100%"
        canvas.layout.min_width = "0px"
        canvas.layout.min_height = "0px"
        #canvas.layout.border = '1px solid rgba(70, 70, 70, 0.5)'
        
        # Register figure
        self.fig = fig
        self.ax = ax
        self.im = im
        self.cbar = cbar
        
        # Capture and modify home button action
        self.original_home_action = self.fig.canvas.toolbar.home
        self.fig.canvas.toolbar.home = self.custom_home_action

        return fig, ax, im, cbar

    def custom_home_action(self, *args, **kwargs):
        self.original_home_action(*args, **kwargs)
        self.update_to_frame(self.current_frame_index)

    def ensure_point_overlay_plot_exists(self, name, color='yellow'):
        
        # If a plot for the point overlay with this name does not exist, create it
        if name not in self.point_overlays:
        
            self.point_overlays[name] \
                = self.ax.scatter(
                    [], [], s=20, edgecolor="none", facecolor=color, zorder=3)

    def ensure_curve_overlay_plot_exists(self, name):
        
        # If a curve overlay plot for this name does not exist, create it
        if name not in self.curve_overlays:
        
            curve = self.ax.add_collection(
                matplotlib.collections.LineCollection([], linewidths=1.5)
                )

            self.curve_overlays[name] = curve

    def update_to_frame(self, frame_index: int):
        """Updates the plot to correspond to the given frame
        """
        
        # Ensure frame is in acceptable range
        frame = int(np.clip(frame_index, 0, self.num_frames - 1))

        # Get data to display
        data = self.get_map_data(frame)

        # Update image data
        self.im.set_data(data)

        # Colorbar spec
        cs = self.colorbar_state

        if cs.cmap == "default":
            self.im.set_cmap(self.map_sequence[self.current_frame_index].cmap)
        else:
            self.im.set_cmap(cs.cmap)
       
        self.im.set_clim(cs.vmin, cs.vmax)


        # Adjust axes face color
        border_pixels = np.concatenate([data[0, :], data[-1, :], data[:, 0], data[:, -1]])

        # Convert to RGBA
        rgba = self.im.cmap(self.im.norm(border_pixels))

        # Representative color (median should be fine in most cases)
        facecolor = np.median(rgba, axis=0)

        self.ax.set_facecolor(facecolor)


        # Update the colorbar to match new data and limits
        if self.cbar is not None:
            self.cbar.update_normal(self.im)


        # Update frame index container
        self.current_frame_index = frame

        # Draw
        self.fig.canvas.draw_idle()

    def update_point_overlay_plot(self, 
                             name, 
                             coordinates: astropy.coordinates.SkyCoord,
                             color):
        """
        Accept skycoords (Astropy SkyCoord) in any frame.
        Transform to this widget's map frame and draw the points.
        """

        # Make sure that the plot for this collection of
        # points exists        
        self.ensure_point_overlay_plot_exists(name, color)

        # Get the point data plot for this model
        scatter_plot = self.point_overlays[name]

        # Remove existing points from the plot if no points given
        if coordinates is None or len(coordinates) == 0:
            scatter_plot.set_offsets(np.empty((0, 2)))
            return

        m = self.map_sequence[self.current_frame_index]
        
        # Cull points that are inside the sun
        r = np.linalg.norm(coordinates.cartesian.xyz.si.value.T, axis=1)            
        mask = (r >= astropy.constants.R_sun.si.value)
        
        coordinates = coordinates[mask]
        
        if len(coordinates) == 0:
            scatter_plot.set_offsets(np.empty((0, 2)))
            return


        # Transform to map coordinate frame
        coords_in_map_frame = coordinates.transform_to(m.coordinate_frame)

        # Coordinate of the observer
        observer = m.coordinate_frame.observer.transform_to(m.coordinate_frame)
        
        # Distance of each point to the observer
        dist = np.linalg.norm(coords_in_map_frame.cartesian.xyz.si.value.T - observer.cartesian.xyz.si.value, axis=1)

        # Depth sort
        if True:
            order = np.argsort(dist)[::-1]
            coords_in_map_frame = coords_in_map_frame[order]
            dist = dist[order]

        # Get the pixel coordinates for this map
        px, py = m.wcs.world_to_pixel(coords_in_map_frame)
        

        # Set colors, size and transparency of the points based on distance to observer        
        norm = matplotlib.colors.Normalize(vmin=dist.min(), vmax=dist.max())
        normed_dist = norm(dist).data

        colors = matplotlib.cm.gray(1.0 - normed_dist)
        alphas = np.maximum(0.1, 1.0 - normed_dist)
        sizes = 2.0*(4.0 - 3.0*normed_dist)

        # Draw
        if px.size == 0:
            offsets = np.empty((0, 2))
        else:
            offsets = np.column_stack([px, py])

        scatter_plot.set_offsets(offsets)
        scatter_plot.set_color(color)
        
        #scatt.set_color(colors)
        scatter_plot.set_alpha(alphas)
        scatter_plot.set_sizes(sizes)

    def update_curve_overlay_plot(self, 
                                name, 
                                segments,
                                color):
        
        self.ensure_curve_overlay_plot_exists(name)

        m = self.map_sequence[self.current_frame_index]

        # Coordinate of the observer
        observer = m.coordinate_frame.observer.transform_to(m.coordinate_frame)
        
        # Coordinates of segments in map frame
        coords_in_map_frame = list()
        distances = list()
        for segment in segments:

            # Remove existing points from the plot if no points given
            if segment is None or len(segment) == 0:
                continue
       
            # Transform to map coordinate frame
            coords = segment.transform_to(m.coordinate_frame)
            
            # Distance of each point to the observer   
            distances.append(np.linalg.norm(coords.cartesian.xyz.si.value.T - observer.cartesian.xyz.si.value, axis=1))

            coords_in_map_frame.append(coords)


        # Global norm
        #norm = matplotlib.colors.Normalize(vmin=np.vstack(distances).min(), 
        #                                   vmax=np.vstack(distances).max())
        

        line_segments = list()
        line_widths = list()
        line_alphas = list()

        for idx, segment in enumerate(segments):

            # Remove existing points from the plot if no points given
            if segment is None or len(segment) == 0:
                continue
            
            # Transform to map coordinate frame
            #coords_in_map_frame = segment.transform_to(m.coordinate_frame)
            coords = coords_in_map_frame[idx]

            # Cull
            #  segment points that are inside the sun
            #r = np.linalg.norm(segment.cartesian.xyz.si.value.T, axis=1)

            #if np.all(r < astropy.constants.R_sun.si.value):
            #    continue
            
            #mask = (r >= astropy.constants.R_sun.si.value)
          

            # Distance of each point to the observer   
            #dist = np.linalg.norm(coords_in_map_frame.cartesian.xyz.si.value.T - observer.cartesian.xyz.si.value, axis=1)

            # Get the pixel coordinates for this map
            px, py = m.wcs.world_to_pixel(coords)

            #print(px.shape, py.shape)
            #norm = matplotlib.colors.Normalize(vmin=dist.min(), vmax=dist.max())
            #normed_dist = norm(dist).data
            

            #avg_dist = np.average(distances[idx])

            #line_widths.append(2.0 - 0.5*norm(avg_dist))
            #line_alphas.append(np.maximum(0.1, 1.0 - 0.5*norm(avg_dist)))

            line_widths.append(2.0)
            line_alphas.append(1.0)


            #            alpha=1.0 - 0.85*norm(avg_dist)
        
            #line.set_data(px, py)
            #line.set_color(color)
            #line.set_linewidth(2.0 - 0.85*norm(avg_dist))
            
            #self.curve_overlays[name].append(ln)
            
            #segments_x_pts.append(np.asarray(px))
            #segments_y_pts.append(np.asarray(py))

            line_segments.append(np.column_stack((px, py)))

            #max_len = max(max_len, len(px))

        
        #self.curve_overlays[name].set_data(x, y)
        overlay = self.curve_overlays[name]

        overlay.set_segments(line_segments)
        overlay.set_linewidths(line_widths)
        overlay.set_alpha(line_alphas)
        overlay.set_colors(color)

    def update_overlays(self,
                        point_overlays,
                        curve_overlays,
                        overlay_colors,
                        ):
        """Update all overlays
        """

        # Clean stale point overlays
        stale_points = set(self.point_overlays) - set(point_overlays)

        for name in stale_points:
            self.point_overlays[name].remove()
            del self.point_overlays[name]

        # Update point overlay plots
        for name, points in point_overlays.items():

            if points is not None:

                self.update_point_overlay_plot(
                    name,
                    points,
                    color = overlay_colors.get(name, 'yellow')
                    )
                    
            else:
                # This plot id exists, but has no data (e.g. not visible)
                # Then, draw nothing
                if name in self.point_overlays:
                    self.point_overlays[name].set_offsets(np.empty((0, 2)))


        # Remove stale curve overlays
        stale_curves = set(self.curve_overlays) - set(curve_overlays)
        
        for name in stale_curves:
            
            self.curve_overlays[name].remove()
            
            del self.curve_overlays[name]


        # Update curve overlay plots
        for name, segments in curve_overlays.items():

            if segments is not None:
                
                self.update_curve_overlay_plot(
                    name,
                    segments, 
                    color = overlay_colors.get(name, 'yellow')
                    )
                
            else:

                # If this overlay name exists in the object, but has no data (e.g. not visible)
                # Then, draw nothing                
                if name in self.curve_overlays:
                    self.curve_overlays[name].set_segments([])
            
        # Draw
        self.fig.canvas.draw_idle()


