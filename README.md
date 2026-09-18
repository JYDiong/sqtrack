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
    track_squalls_parent_inheritance,
)

# 1. Load satellite precipitation
ds = xr.open_mfdataset("3B-HHR.MS.MRG.3IMERG.*.nc4")

# 2. Extract contours and track features
contour_sets = detect_features_time_series(
    ds["precipitation"], size_filter=True, rf_threshold=1.0
)
ce = track_squalls_parent_inheritance(
    contour_sets, ds.time, overlap_threshold=0.5
)

# 3. Shape evaluation and major squall filtering
rsize = ce[ce.groupby("id")["itime"].transform("count") >= 2]
rsize = rsize.assign(category=evaluate_squall_eccentricity(rsize))

final_gdf = consolidate_track_categories(rsize)
filtered = final_gdf.merge(rsize, on="id", how="left")
major_squalls = filtered[
    (filtered["final_category"] == "squall") & (filtered["area_km2"] >= 5000)
]

print(f"Identified Squall Tracks: {major_squalls['id'].unique()}")