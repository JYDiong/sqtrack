<<<<<<< HEAD
# SQTrack: Mesoscale Squall Line Feature Tracker

`sqtrack` is an installable Python package designed to detect, segment, and track tropical squall lines using satellite precipitation data (such as GPM IMERG). 

It implements a **parent-inheritance tracking algorithm** to accurately resolve multi-parent merging events, eliminating track fragmentation and ID over-counting.

---

## Key Features

* **Multi-Parent Merge Handling:** Assigns primary track IDs based on the largest surface area parent, tagging secondary merged tracks for complete lineage tracking.
* **Two-Tier Filtering:** Supports pre-filtering ($1,000\text{ km}^2$) and post-filtering ($5,000\text{ km}^2$) to distinguish organized mesoscale systems from convective noise.
* **Geometrical Shape Analysis:** Integrated `EllipseModel` eccentricity filter to isolate linear squall bands ($eccentricity > 0.8$).

---

## Installation

You can install `sqtrack` directly from GitHub using `pip`:

```bash
pip install git+[https://github.com/JYDiong/sqtrack.git](https://github.com/JYDiong/sqtrack.git)

## Example:

import xarray as xr
from sqtrack import (
    consolidate_track_categories,
    detect_features_time_series,
    evaluate_squall_eccentricity,
    track_squalls_graph,
)

# 1. Load satellite precipitation
ds = xr.open_mfdataset("3B-HHR.MS.MRG.3IMERG.*.nc4")

# 2. Extract contours and track features
contour_sets = detect_features_time_series(
    ds["precipitation"], size_filter=True, rf_threshold=1.0
)
ce, G = track_squalls_graph(
    contour_sets, ds.time, overlap_threshold=0.5
)
ce = ce.reset_index(drop=True)

# 3. Shape evaluation and major squall filtering
rsize = ce[ce.groupby("id")["itime"].transform("count") >= 2]

output_file = "output.txt"
evaluate_squall_eccentricity(rsize, output_file)

with open("output.txt") as f:
    List = [item.strip() for item in f]

gdf = rsize.assign(category=List)
if os.path.exists("output.txt"):
    os.remove("output.txt")

# Consolidate squall categories per individual track ID
final_gdf = consolidate_track_categories(gdf, id_col="id")
gdf1 = final_gdf.merge(gdf, on="id", how="left")

# Filter for tracks that are classified as squalls
filtered = gdf1[gdf1["final_category"] == "squall"]

# PRUNING STEP: Require each specific track ID to independently hit >= 5000 km2
# This drops any small split branch that never reaches 5000 km2 on its own
valid_track_ids = filtered.loc[filtered["area_km2"] >= 5000, "id"].unique()
final_gdf = filtered[filtered["id"].isin(valid_track_ids)].reset_index(
    drop=True
)

# Optional: Print summary of remaining tracks vs families
print(f"Remaining Major Squall Tracks (IDs): {final_gdf['id'].nunique()}")
print(
    f"Associated Parent Storm Families (Family IDs): {final_gdf['family_id'].nunique()}"
)

#=======
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
>>>>>>> 0c2c92289d095ec030d15b03c03bafe776d05182
