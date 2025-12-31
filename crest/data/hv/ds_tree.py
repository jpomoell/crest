# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""Helioviewer data source metadata container
"""

import dataclasses
import datetime
from typing import Dict, List, Optional


@dataclasses.dataclass(frozen=True)
class Measurement:
    """Immutable container representing metadata on the origin of a measurement.

    Attributes
    ----------
    source_id : int
        Unique identifier for the data in the Helioviewer database.
    nickname : str
        Short name for the measurement.
    start : datetime.datetime
        Timestamp of the start of the measurement interval.
    end : datetime.datetime
        Timestamp of the end of the measurement interval.
    observatory : str
        Name of the observatory that produced the measurement.
    instrument : Optional[str]
        Instrument name used to acquire the measurement, or None if unknown/not applicable.
    detector : Optional[str]
        Detector name, or None if unknown/not applicable.
    measurement : str
        Semantic label providing information on the type of the measurement.
    """
    source_id: int
    nickname: str
    start: datetime.datetime
    end: datetime.datetime
    
    observatory: str    
    instrument: Optional[str]
    detector: Optional[str]
    measurement: str

    @property
    def name(self):
        return self.measurement
    

class DataSourceTree:
    """Parses and provides access to the data source structure returned by Helioviewer.

    The input dict is expected to be a nested mapping with at most three levels
    (observatory -> instrument -> detector -> measurement) where measurement leaf nodes
    are dicts containing at least the keys: "sourceId", "nickname", "start", "end".
    This class normalizes the input into an internal nested dictionary:

        _tree[observatory][instrument][detector][measurement] -> Measurement

    Notes
    -----
    - Instruments and detectors may be None.
    - The class provides a read-only view: it returns Measurement instances
      directly and provides convenience lookup and filtering methods.
    """

    def __init__(self, data_sources: Dict):
        """Initialize the class by parsing raw Helioviewer metadata on data sources.

        Parameters
        ----------
        data_sources : Dict
            Nested mapping produced by Helioviewer describing observatories,
            instruments, detectors and measurement leaf nodes. Leaf node dicts
            must include "sourceId", "nickname", "start", and "end".
        """

        self._tree: Dict[str, Dict] = {}

        self._parse(data_sources)

    def _parse(self, data_sources: Dict) -> None:
        """Parser that iterates over the observatories and all nested data.
        
        Parameters
        ----------
        data_sources : Dict
            Raw nested input to parse into the internal _tree structure.
        """

        for observatory, obs_data in data_sources.items():
            
            self._tree.setdefault(observatory, {})

            self._traverse(
                node=obs_data,
                observatory=observatory,
                instrument=None,
                detector=None,
            )

    def _traverse(self, 
                  node: Dict, 
                  observatory: str,
                  instrument: Optional[str],
                  detector: Optional[str]) -> None:
        """Recursively traverses a node in the raw data tree and populates self._tree.

        Parameters
        ----------
        node : Dict
            Current subtree being traversed.
        observatory : str
            Current observatory name (top-level key).
        instrument : Optional[str]
            Current instrument name, or None if not determined.
        detector : Optional[str]
            Current detector name, or None if not determined.

        Behavior
        --------
        - If a child value is a dict containing "sourceId", it is treated as a
          measurement leaf and converted to a Measurement instance stored in _tree.
        - Otherwise the function descends one level, assigning the first unlabeled
          intermediate level to `instrument`, the next to `detector`.
        """

        for key, value in node.items():
            
            if isinstance(value, dict) and "sourceId" in value:
                
                # We are at a leaf node, i.e. a measurement
                measurement = key
                
                m = Measurement(
                    source_id=value["sourceId"],
                    nickname=value["nickname"],
                    start=self._parse_time(value["start"]),
                    end=self._parse_time(value["end"]),
                    observatory=observatory,
                    instrument=instrument,
                    detector=detector,
                    measurement=measurement,
                )

                self._tree \
                    .setdefault(observatory, {}) \
                    .setdefault(instrument, {}) \
                    .setdefault(detector, {})[measurement] = m
                
            else:

                # Intermediate node: continue traversing until a leaf is reached
                if instrument is None:
                    self._traverse(value, observatory, instrument=key, detector=None)
                elif detector is None:
                    self._traverse(value, observatory, instrument=instrument, detector=key)
                else:
                    # Extra depth beyond detector
                    raise ValueError("Data source tree deeper than expected")
                    #self._traverse(value, observatory, instrument=instrument, detector=detector)

    @staticmethod
    def _parse_time(value: str) -> datetime:
        """Parse a timestamp string from the raw data into a datetime.datetime.

        Parameters
        ----------
        value : str
            Timestamp in the format "%Y-%m-%d %H:%M:%S".

        Returns
        -------
        datetime.datetime
            Parsed naive datetime
        """
        return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

    def observatories(self) -> List[str]:
        """Returns a list of the names of available observatories.

        Returns
        -------
        List[str]
            Names of the available observatories.
        """
        return sorted(self._tree.keys())

    def instruments(self, observatory: str) -> Optional[List[str]]:
        """Returns a list of the names of the instruments of an observatory.

        Parameters
        ----------
        observatory : str
            Observatory name to query.

        Returns
        -------
        Optional[List[str]]
            Available instrument names, or None if the observatory is not present
            or has no named instruments.
        """

        obs = self._tree.get(observatory)
        if not obs:
            return None

        instruments = [i for i in obs.keys() if i is not None]

        return sorted(instruments) or None

    def detectors(self, observatory: str, instrument: str) -> Optional[List[str]]:
        """Returns a list of detectors for a given observatory and instrument.

        Parameters
        ----------
        observatory : str
            Observatory name.
        instrument : str
            Instrument name.

        Returns
        -------
        Optional[List[str]]
            Detector names, or None if not present.
        """
        inst = self._tree.get(observatory, {}).get(instrument)
        if not inst:
            return None
        
        detectors = [d for d in inst.keys() if d is not None]

        return sorted(detectors) or None

    def measurements(self,
                     observatory: str,
                     instrument: Optional[str],
                     detector: Optional[str]) -> Optional[List[str]]:
        """Returns a list of measurement names under the specified path.

        Parameters
        ----------
        observatory : str
            Observatory name.
        instrument : Optional[str]
            Instrument name or None.
        detector : Optional[str]
            Detector name or None.

        Returns
        -------
        Optional[List[str]]
            Names of the available measurements, or None if the path does not exist.
        """
        det = self._tree.get(observatory, {}).get(instrument, {}).get(detector)
        if not det:
            return None
        
        return sorted(det.keys())

    def get_measurement(self,
                        observatory: str,
                        instrument: Optional[str],
                        detector: Optional[str],
                        measurement: str) -> Optional[Measurement]:
        """Retrieve a Measurement object for the specified path.

        Parameters
        ----------
        observatory : str
            Observatory name.
        instrument : Optional[str]
            Instrument name or None.
        detector : Optional[str]
            Detector name or None.
        measurement : str
            Measurement identifier/name.

        Returns
        -------
        Optional[Measurement]
            The Measurement instance if found, otherwise None.
        """
        return (self._tree
                .get(observatory, {})
                .get(instrument, {})
                .get(detector, {})
                .get(measurement)
                )

    def filtered_by_time(self, start: datetime.datetime, end: datetime.datetime):
        """Produce a new DataSourceTree containing only measurements that exist in the time interval [start, end].

        Parameters
        ----------
        start : datetime.datetime
            Interval start.
        end : datetime.datetime
            Interval end.

        Returns
        -------
        DataSourceTree
            New DataSourceTree instance whose internal _tree contains only
            measurements with m.start <= end and m.end >= start.

        Notes
        -----
        - The returned object is a shallow copy in the sense that it reuses
          the same Measurement instances from the original tree.
        """
    
        new_tree = DataSourceTree.__new__(DataSourceTree)
        new_tree._tree = {}

        for obs, insts in self._tree.items():
            for inst, dets in insts.items():
                for det, meas in dets.items():
                    for m in meas.values():
                        if m.start <= end and m.end >= start:
                            new_tree._tree \
                                .setdefault(obs, {}) \
                                .setdefault(inst, {}) \
                                .setdefault(det, {})[m.measurement] = m

        return new_tree