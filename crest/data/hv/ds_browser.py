# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""Helioviewer data source browser
"""

from typing import List, Optional
import pandas as pd
import solara

from .ds_tree import DataSourceTree, Measurement


class DataSourceBrowser:
    """UI for browsing DataSourceTree objects.

    This class wraps an instance of DataSourceTree and provides 
    reactive selection state for observatory, instrument, detector,
    and measurement. It also constructs a Solara component (self.ui) that 
    provides a UI for interactively browsing the tree.
    """

    def __init__(self, source_tree: DataSourceTree, *, show_measurement: bool=False):
        """Initialize the menu with a data-source provider.

        Parameters
        ----------
        source_tree : DataSourceTree
            Metadata tree object providing the available data sources
        show_measurement : bool
            Whether to display measurement metadata in the menu
        """

        # Store the available data source tree
        self._source_tree = source_tree

        # The selected observatory
        self._observatory = solara.reactive(None)

        # The selected instrument
        self._instrument = solara.reactive(None)

        # The selected detector
        self._detector = solara.reactive(None)

        # The selected measurement
        self._measurement = solara.reactive(None)


        self._show_measurement = show_measurement
        

        @solara.component
        def ui():
            """Solara UI component for browsing the data source tree.
            """
            with solara.Column():
                solara.Select(label="Observatory", value=self._observatory, values=self.observatories)
                
                solara.Select(label="Instrument",
                              value=self._instrument,
                              values=self.instruments,
                              on_value=self._set_instrument(),
                              disabled=(len(self.instruments) == 1 if self.instruments is not None else True) 
                             )

                solara.Select(label="Detector", 
                              value=self._detector, 
                              values=self.detectors, 
                              on_value=self._set_detector(),
                              disabled=(len(self.detectors) == 1 if self.detectors is not None else True) 
                             )

                solara.Select(label="Measurement", 
                              value=self._measurement, 
                              values=self.measurements,
                              on_value=self._set_measurement(),
                              disabled=(len(self.measurements) == 1 if self.measurements is not None else True)
                             )

                if self._show_measurement and self.measurement is not None:                    
                    df = pd.DataFrame.from_dict(self.measurement.__dict__, orient='index').T
                    solara.Markdown(df.to_markdown())

        self.ui = ui

        
    def _set_instrument(self):

        if self.instruments is None and self.instrument is not None:
            self._instrument.set(None)

        if self.instruments is not None:
            if len(self.instruments) == 1:
                self._instrument.set(self.instruments[0])

    def _set_detector(self):

        if self.detectors is None and self.detector is not None:
            self._detector.set(None)

        if self.detectors is not None:
            if len(self.detectors) == 1:
                self._detector.set(self.detectors[0])

    def _set_measurement(self):

        if self.measurements is not None:
            if len(self.measurements) == 1:
                self._measurement.set(self.measurements[0])
    
    @property
    def observatory(self) -> Optional[str]:
        """The currently selected observatory.

        Returns
        -------
        Optional[str]
            Selected observatory name or None.
        """
        return self._observatory.value

    @property
    def instrument(self) -> Optional[str]:
        """The currently selected instrument.

        Returns
        -------
        Optional[str]
            Selected instrument name or None.
        """
        return self._instrument.value

    @property
    def detector(self) -> Optional[str]:
        """The currently selected detector.

        Returns
        -------
        Optional[str]
            Selected detector name or None.
        """
        return self._detector.value

    @property
    def measurement(self) -> Optional[Measurement]:
        """Returns the metadata associated with the currently selected measurement.
        
        Returns
        -------
        Optional[Measurement]
            Measurement object selected by the current observatory/instrument/detector
            and measurement selection, or None if not found.
        """
        return self._source_tree.get_measurement(self.observatory, 
                                                 self.instrument, 
                                                 self.detector, 
                                                 self._measurement.value)

    @property
    def observatories(self) -> List[str]:
        """Returns the list of available observatories from the underlying sources.

        Returns
        -------
        List[str]
            Observatory names.
        """      
        return self._source_tree.observatories()

    @property
    def instruments(self) -> Optional[List[str]]:
        """Returns the list of available instruments of the selected observatory.

        Returns
        -------
        Optional[List[str]]
            Instrument names, or None if no instruments are available.
        """
        return self._source_tree.instruments(self.observatory)

    @property
    def detectors(self) -> Optional[List[str]]:
        """Returns the list of available detectors for the selected observatory and instrument.

        Returns
        -------
        Optional[List[str]]
            Detector names, or None if none are available.
        """
        return self._source_tree.detectors(self.observatory, self.instrument)

    @property
    def measurements(self) -> Optional[List[str]]:
        """Returns the list of available measurements for the current selection path.

        Returns
        -------
        Optional[List[str]]
            Measurement names, or None if none are available.
        """
        return self._source_tree.measurements(self.observatory, self.instrument, self.detector)

    @property
    def path(self):
        return self.observatory, self.instrument, self.detector, self._measurement.value