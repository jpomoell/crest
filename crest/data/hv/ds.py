# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""Helioviewer data source
"""

import os
import datetime
import tempfile

import hvpy


def get_data_sources():
    return hvpy.getDataSources()


def get_sequence_timestamps(start_time, end_time, source_id, cadence=None):

    # Get sequence of image timestamps using the JPX metadata
    jpx_response = hvpy.getJPX(
        startTime=start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        endTime=end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        sourceId=source_id,
        verbose=True,
        jpip=True,
        cadence=cadence
    )

    # Validate response
    if not jpx_response or "frames" not in jpx_response:
        raise RuntimeError("Failed to retrieve frame timestamps from getJPX")

    # The timestamps of the images
    timestamps = jpx_response["frames"]

    return timestamps


def download_image_sequence(timestamps, source_id, download_dir):

    # Ensure that the output directory exists
    os.makedirs(download_dir, exist_ok=True)

    files = list()
    
    for timestamp in timestamps:

        # Request the JP2 image
        image_data = hvpy.getJP2Image(
            sourceId=source_id,
            date=datetime.datetime.fromtimestamp(timestamp))

        # The name of the file
        fname = os.path.join(download_dir, f"{timestamp}.jp2")

        # Write
        with open(fname, "wb") as f:
            f.write(image_data)

        files.append(fname)
        
        # Save to a temporary file
        #tmp_file = tempfile.NamedTemporaryFile(delete=True, delete_on_close=False, suffix=".jp2")
        #tmp_file.write(image_data)
        #tmp_file.close()
    
        #files.append(tmp_file.name)

    return files