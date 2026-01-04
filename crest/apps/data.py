# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""Imaging data download app
"""

import pandas as pd
import solara
import sunpy.map

import crest.data.hv.ds
import crest.data.hv.ds_dlmenu
import crest.components.containers.daccordions


class ImagingDataSelection:

    def __init__(self, data_download_dir="data/"):

        self._sources = solara.reactive({})
        self._database = solara.reactive(pd.DataFrame())

        # Get the available Helioviewer sources
        helioviewer_ds = crest.data.hv.ds.get_data_sources()

        # Helper to create a Helioviewer downloader instance
        def HelioviewerMenu():
            return crest.data.hv.ds_dlmenu.DataSourceQueryAndDownload(helioviewer_ds, 
                                                                      download_dir=data_download_dir + "hv")
        

        @solara.component
        def ui():

            _deps = []
            for source in self._sources.value.values():               
                _deps.append(source.path)
                _deps.append(source._redo_query)
                _deps.append(source._redo_download)
                _deps.append(source.cadence)
                _deps.append(source.start_datetime)
                _deps.append(source.end_datetime)
                        
            solara.use_effect(self.update_dataframe, dependencies=_deps)
        

            with solara.Column():
                    
                crest.components.containers.daccordions.DataSourceDynamicAccordion(
                    self._sources,
                    type_map = {"Helioviewer" : HelioviewerMenu}
                )
                
                with solara.Card():
                    with solara.Row(justify="center"):
                        solara.Markdown(self._database.value.to_markdown())

        self.ui = ui

    
    def update_dataframe(self):
    
        rows = list()
        
        for idx, source in enumerate(self._sources.value.values()):
    
            obs, ins, det, measurement = source.path
            
            frames = None
            status = None
        
            if measurement is None:
                status = "Selection incomplete"
            else:
                status = "Selection done"
                
            if not source._redo_query:
                status = "Query complete" 
            
            if not source._redo_download:
                status = "Download complete" 
                frames = len(source.downloaded_files)
    
            row = dict([("Provider", "Helioviewer"),
                        ("Observatory", obs), ("Instrument", ins), 
                        ("Detector", det), ("Measurement", measurement),
                        ("Start time", source.start_datetime), ("End time", source.end_datetime),
                        ("Cadence", source.cadence), ("Frames", frames),
                        ("Status", status)])

            rows.append(row)

        self._database.set(pd.DataFrame.from_dict(rows))

    def _observer(self, m):
        return sunpy.coordinates.get_horizons_coord(m.meta.get('TELESCOP'), m.date)

    def _map_from_file(self, file):

        m = sunpy.map.Map(file)

        # Observer
        obs = None

        # Fix metadata
        if not m.meta.has_key('HGLN_OBS'):
            
            if obs is None:
                obs = self._observer(m)
                
            m.meta['HGLN_OBS'] = obs.lon.to('deg').value
            m.meta['HGLT_OBS'] = obs.lat.to('deg').value
            
            #m.meta['HGLN_OBS'] = obs.lon.to('deg').value
            #m.meta['HGLT_OBS'] = obs.lat.to('deg').value
            
        if not m.meta.has_key('DSUN_OBS'):

            if obs is None:
                obs = self._observer(m)

            m.meta['DSUN_OBS'] = obs.radius.to('m').value

        #if not m.meta.has_key('RSUN'):

        return m

    def get_map_sequences(self):

        #files = list()
        #for source in self._sources.value.values():
        #    if len(source.downloaded_files) > 0:
        #        files.append(source.downloaded_files)
        #
        #
        #return [sunpy.map.Map(_files, sequence=True) for _files in files]

        sequences = list()
        
        for source in self._sources.value.values():
            if len(source.downloaded_files) > 0:
                sequences.append(
                    sunpy.map.MapSequence([self._map_from_file(_file) for _file in source.downloaded_files])
                )
                
        return sequences
