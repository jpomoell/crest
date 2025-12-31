# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""Helioviewer data source query and downloader
"""

import math
import datetime

from typing import List, Optional, Dict
import pandas as pd
import solara

import crest.utils.comparison

from . import ds
from .ds_tree import DataSourceTree
from .ds_browser import DataSourceBrowser



class DataSourceQueryAndDownload:

    def __init__(self, data_sources: Dict = None, download_dir = "data/hv"):

        if data_sources is None:
            data_sources = ds.get_data_sources()

        self._source_tree = DataSourceTree(data_sources)
        
        self._browser = DataSourceBrowser(self._source_tree)


        date_now = datetime.datetime.now().date()
        time_now = datetime.datetime.now().time().replace(microsecond=0)
        
        # Time range of the data
        self._beg_date = solara.reactive(date_now - datetime.timedelta(days=1))
        self._beg_time = solara.reactive(time_now)

        self._end_date = solara.reactive(date_now)
        self._end_time = solara.reactive(time_now)


        # The cadence of the data
        self._cadence = solara.reactive(4.0*60.0*60.0)

        # Download directory
        self._download_dir = download_dir 

        # Result of the query
        self._query_result = solara.reactive(
            pd.DataFrame(columns=["Observatory", "Instrument", "Detector", "Measurement", "Time"]))

        # The query that produced the result
        self._active_query = solara.reactive(None)

        # Result of download
        self._download_result = solara.reactive([])        

        # Whether querying is on-going
        self._querying = solara.reactive(False)

        # Whether downloading is on-going
        self._downloading = solara.reactive(False)
        
        
        @solara.component
        def ui():

            query_summary_text = solara.use_reactive("")

            with solara.Column():           
                solara.ProgressLinear(self._querying.value or self._downloading.value)

            with solara.ColumnsResponsive([4, 8]):
                
                self._browser.ui()

                with solara.Column():

                    min_date = self.measurement.start.isoformat() if self.measurement is not None else None
                    max_date = self.measurement.end.isoformat() if self.measurement is not None else None
                    
                    # Sanitize date selection
                    if self.measurement is not None:

                        if self._beg_date.value < self.measurement.start.date():
                            self._beg_date.set(self.measurement.start.date())

                        if self._beg_date.value > self.measurement.end.date():
                            self._beg_date.set(self.measurement.end.date())

                        if self._end_date.value < self.measurement.start.date():
                            self._end_date.set(self.measurement.start.date())

                        if self._end_date.value > self.measurement.end.date():
                            self._end_date.set(self.measurement.end.date())


                    with solara.Row():
                        solara.lab.InputDate(self._beg_date, 
                                             label="Start date", 
                                             min_date=min_date,
                                             max_date=max_date, 
                                             optional=False)
                        
                        solara.lab.InputTime(self._beg_time, use_seconds=True, label="Start time")
                
                    with solara.Row():
                        solara.lab.InputDate(self._end_date, 
                                             label="End date",
                                             min_date=min_date,
                                             max_date=max_date, 
                                             optional=False)
                        
                        solara.lab.InputTime(self._end_time, use_seconds=True, label="End time")
                
                    solara.InputFloat(label="Cadence, in seconds", value=self._cadence, style={"width" : "50%"})
                                    
                    #with solara.Column():
                    
                    if not self._redo_query:
                        query_summary_text.set(f"Query returned {len(self.query_result)} results")
                        
                        with solara.Details(summary=query_summary_text.value, expand=False):
                            solara.Markdown(self._query_result.value.to_markdown())
                                    
                    if not self._redo_download:   
                        with solara.Details(summary=f"Downloaded {len(self.downloaded_files)} files",
                                            expand=False):
                            solara.Markdown(pd.DataFrame({"Files": self.downloaded_files}).to_markdown())


                with solara.Column():
                
                    with solara.Row(justify="space-between"):

                        solara.Button(label="Query",
                                    color="red" if self._redo_query else "green",
                                    on_click=lambda: self.query(),
                                    disabled=self.measurement is None,
                                    style={"width":"40%"}
                                    )

                        solara.Button(label="Download",
                                on_click=lambda: self.download(),
                                color="red" if self._redo_download else "green",
                                disabled=(len(self.query_result) == 0 or self._redo_query),
                                style={"width":"50%"}
                                )

        self.ui = ui

    @property
    def _redo_query(self):

        if self._active_query.value is None:
            return True

        if self.measurement is not None:

            query = self._construct_query(self.measurement.source_id)

            are_equal = crest.utils.comparison.dicts_equal(
                self._active_query.value, 
                query,
                comparators={float: lambda a,b : math.isclose(a, b)})
        
            if not are_equal:
                return True
            
        return False

    @property
    def _redo_download(self):
        
        if self._redo_query:
            return True
        else:
            return len(self.downloaded_files) == 0

    @property
    def measurement(self):
        return self._browser.measurement

    @property
    def path(self):
        return self._browser.path

    @property
    def cadence(self):
        return self._cadence.value
    
    @property
    def downloaded_files(self):
        return list(self._download_result.value)

    @property
    def query_result(self):
        return self._query_result.value

    def download(self):

        # Get the timestamps returned by the query
        timestamps = [int(ts.to_pydatetime().timestamp()) for ts in self._query_result.value["Time"]]
        
        # Download files
        self._downloading.set(True)
        
        files = ds.download_image_sequence(
            timestamps,
            source_id=self.measurement.source_id,
            download_dir=self._download_dir)
          
        self._download_result.set(list(files))
        
        self._downloading.set(False)
    
    @property
    def start_datetime(self):
        return datetime.datetime.combine(self._beg_date.value, self._beg_time.value)

    @property
    def end_datetime(self):
        return datetime.datetime.combine(self._end_date.value, self._end_time.value)

    def _construct_query(self, source_id):
        
        return dict(start_time=self.start_datetime,
                    end_time=self.end_datetime,
                    source_id=source_id,
                    cadence=self.cadence)

    def query(self):

        m = self.measurement
       
        if m is None:
            return
            
        if m.source_id is not None:

            # Query the Helioviewer server to available files
            self._querying.set(True)
            
            query = self._construct_query(m.source_id)

            timestamps = ds.get_sequence_timestamps(**query)

            # datetimes of the returned query
            dt_of_stamps = [datetime.datetime.fromtimestamp(stamp) for stamp in timestamps]

            df = self._query_result.value.copy()
            df.drop(df.index, inplace=True)
            
            for idx, dt in enumerate(dt_of_stamps):

                row = {"Observatory" : self.measurement.observatory, 
                       "Instrument" : self.measurement.instrument,
                       "Detector" : self.measurement.detector,
                       "Measurement" : self.measurement.name,                    
                       "Time" : dt}
    
                df.loc[idx] = row

            self._query_result.set(df)

            self._active_query.set(query)

            self._querying.set(False)