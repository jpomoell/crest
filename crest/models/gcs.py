# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""GCS model widget
"""

import datetime
import pandas as pd
import numpy as np

import astropy
from astropy import units

import solara

import crest.utils.geometry
import crest.components.color

from crest.models.base.specs import NumericParameter
from crest.models.base.widget import ModelWidgetBase
import crest.models.base.gcs




class GraduatedCylindricalShell(ModelWidgetBase):
    
    def __init__(self, date, time):

        super().__init__()

        self.date = date
        self.time = time

        # Parameter specification definitions
        self._parameter_specs = {
            "latitude":     NumericParameter("Lat", 0.0, -90,  90,  0.25, units.deg),
            "longitude":    NumericParameter("Lon", 0.0, -180, 180, 0.25, units.deg),
            "tilt":         NumericParameter("Tilt", 0.0, -90,  90,  0.25, units.deg),
            "aspect_ratio": NumericParameter("Aspect ratio", 0.2, 0, 1, 0.02, units.dimensionless_unscaled),
            "half_angle":   NumericParameter("Half angle", 45.0, 0, 90, 0.5, units.deg),
            "leading_edge": NumericParameter("Apex height", 3.0, 0.1, 30.0, 0.1, astropy.constants.R_sun),
        }

        # Reactive model parameters
        self.parameters = {
            name: solara.reactive(spec.default) for name, spec in self._parameter_specs.items()
        }

        # Additional reactive state
        self.param_records = solara.reactive(pd.DataFrame(columns=["type", "time"] + list(self.parameters.keys())))
        
        # The actual model implementation
        self.model = crest.models.base.gcs.GCSModel(
            **{
                name: self.parameters[name].value*self._parameter_specs[name].unit
                for name in self._parameter_specs
            }
        )

        # Subscribe params --> model internal object
        for name, spec in self._parameter_specs.items():
            # Must capture name and spec in default args
            self.parameters[name].subscribe(lambda v, attr=name, unit=spec.unit: setattr(self.model, attr, v*unit))


        # Set initial settings (different from defaults)
        self._do_plot_curves.set(False) 
        self._do_plot_points.set(True)


         # Build the UI component
        self.ui = self._build_ui_component()


    def _build_ui_component(self):

        @solara.component
        def ModelUI():

            _show_color_picker = solara.use_reactive(False)

            with solara.Column(gap="0px", margin=0):
                
                # Create a slider for each numeric parameter
                with solara.Details(summary="Parameters", expand=True):

                    for name, spec in self._parameter_specs.items():
                        solara.Row(children=[
                            solara.SliderFloat(
                                label=spec.label,
                                value=self.parameters[name],
                                min=spec.min,
                                max=spec.max,
                                step=spec.step,
                                tick_labels='end_points'
                            )])
                
                with solara.Details(summary="Appearance"):

                    with solara.Row(justify="space-between"):
                        solara.Checkbox(label="Curves", value=self._do_plot_curves)
                        solara.Checkbox(label="Points", value=self._do_plot_points)
                        solara.Checkbox(label="Visible", value=self._is_visible)
                    
                    with solara.Column(gap="0px", style={"width": "100%"}):
                        
                        solara.Button(
                            icon_name="mdi-palette",
                            label="Show color picker" if not _show_color_picker.value else "Hide color picker", 
                            on_click=lambda: _show_color_picker.set(not _show_color_picker.value)
                            )
                    
                        if _show_color_picker.value:
                            crest.components.color.ColorPicker(self._color)

            # Reactively trigger has_changed whenever any parameter value changes
            solara.use_effect(
                lambda: self.notify_has_changed(),
                dependencies=[
                    self.parameters[name].value
                    for name in self._parameter_specs
                ],
            )

        return ModelUI

    
    def points(self):
        """
        """

        # Get shell coordinates
        points = list()
        
        half_angle_deg = self.model.half_angle.to_value(units.deg)
        xi = (self.model.h - astropy.constants.R_sun)/self.model.rho
        surface_angle_deg = (180.0/np.pi)*np.atan(xi.value) + half_angle_deg

        for beta in np.linspace(-surface_angle_deg, 180.0+surface_angle_deg, 54):
            _center, _radius, _normal = self.model.cross_section_circle(beta*units.deg)
            
            points.append(crest.utils.geometry.circle(_center, _normal, _radius, 
                                                      num_points=38,
                                                      end_point=False, 
                                                      perp=np.array((0.0, 0.0, 1.0))))
        
        pts = np.dot(np.vstack(points), self.model.tmatrix.T)
        
        return pts
        
   
    def outline(self):
        
        half_angle_deg = self.model.half_angle.to_value(units.deg)

        # OQ = self.h - self.rho*np.tan(-(_beta + _hang))
        # (h - OQ)/rho = np.tan(a)
        
        xi = (self.model.h - astropy.constants.R_sun)/self.model.rho
        surface_angle_deg = (180.0/np.pi)*np.atan(xi.value) + half_angle_deg


        curve_count = 64
        circle_point_count = 8

        poloidal = list()
        for beta in np.linspace(-surface_angle_deg, 180.0 + surface_angle_deg, curve_count):
            
            _center, _radius, _normal = self.model.cross_section_circle(beta*units.deg)
            
            _circle = crest.utils.geometry.circle(
                _center, _normal, _radius, end_point=False, num_points=circle_point_count, perp=np.array((0.0, 0.0, 1.0)), toffset=beta*np.pi/180.0
                )
                
            poloidal.append(_circle)
 
        poloidal = np.vstack(poloidal).reshape(curve_count, circle_point_count, 3).transpose(1, 0, 2)
        poloidal = [np.dot(p, self.model.tmatrix.T) for p in poloidal]

        return poloidal
    
    def curves(self):
        return self.outline()
    
    def _curves(self):
        """
        """

        toroidal = list()
        poloidal = list()

        circle_point_count = 20
        curve_count = 25
        
        for beta in np.linspace(-85.0, 265.0, curve_count):
            
            _center, _radius, _normal = self.model.cross_section_circle(beta*units.deg)
            
            _circle = crest.utils.geometry.circle(
                _center, _normal, _radius, num_points=circle_point_count, perp=np.array((0.0, 0.0, 1.0))
                )
    
            toroidal.append(_circle)
            poloidal.append(_circle)
 
        poloidal = np.vstack(poloidal).reshape(curve_count, circle_point_count, 3).transpose(1, 0, 2)
        poloidal = [np.dot(p, self.model.tmatrix.T) for p in poloidal]
               
        toroidal = [np.dot(t, self.model.tmatrix.T) for t in toroidal]
       
        return poloidal + toroidal
    
    def record_parameters(self):
        
        row = {"type" : "GraduatedCylindricalShell", "time" : datetime.datetime.combine(self.date.value, self.time.value)}
        row.update({name: self.parameters[name].value for name in self.parameters.keys()})
        
        df = self.param_records.value.copy()
        df.loc[len(df)] = row

        self.param_records.set(df)