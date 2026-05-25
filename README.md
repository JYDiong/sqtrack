# sqtrack
A Python pipeline for contour detection, object tracking, and geometry classification of convective systems using Xarray and GeoPandas.
# SQTrack

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Spatiotemporal tracking and morphological classification of squall systems from gridded precipitation data.

`sqtrack` is a Python-based pipeline built for atmospheric scientists, meteorologists, and GIS data analysts to isolate storm clusters from gridded precipitation datasets, project their trajectories over time, and mathematically classify their structural geometry (e.g., distinguishing squall lines from non-squall systems).

It leverages a powerful cloud-native and geospatial Python stack consisting of `Xarray`, `GeoPandas`, `Shapely`, and `Scikit-Image`.

---

## Features

* **Contour Identification:** Automated tracking of localized rainfall intensity boundaries using multi-dimensional image labeling techniques (`ndimage` & `skimage`).
* **Spatiotemporal Object Tracking:** Advection projection and temporal overlapping analysis to maintain consistent, persistent identity tags (`id`) for moving storm cells across time steps.
* **Morphological Classification:** High-fidelity convex hull parsing and ellipse modeling to calculate system eccentricity, isolating severe linear convective features (squall lines).
* **Geospatial Native:** Built natively to ingest multi-file gridded NetCDF arrays via `Xarray` / `Dask` and output clean, analysis-ready `GeoDataFrames`.

---

##  Installation

### Option 1: Using Conda (Recommended for Geospatial Libraries)
Geospatial dependencies (`geopandas`, `shapely`) install most reliably via pre-compiled binary packages. Create and activate the provided standalone environment:

```bash
# Clone the repository
git clone [https://github.com/JYDiong/sqtrack.git](https://github.com/JYDiong/sqtrack.git)
cd sqtrack

# Create and activate environment
conda env create -f environment.yml
conda activate sqtrack

# Install the package in editable/development mode
pip install -e .
