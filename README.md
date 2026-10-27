# sqtrack

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub](https://img.shields.io/badge/GitHub-JYDiong%2Fsqtrack-181717?logo=github)](https://github.com/JYDiong/sqtrack)
[![DOI](https://img.shields.io/badge/DOI-10.1002%2Fqj.70143-blue)](https://doi.org/10.1002/qj.70143)

Spatiotemporal tracking and morphological classification of squall systems from gridded precipitation data.

`sqtrack` is a Python-based pipeline engineered for atmospheric scientists, meteorologists, and GIS data analysts. It isolates storm clusters from gridded precipitation datasets, reconstructs cell trajectories across timesteps using directed graph analysis, and mathematically categorizes structural morphology (e.g., separating linear squall lines from non-squall systems using ellipse eccentricity modeling).

---

## Key Features

- **Contour & Feature Identification:** Segment rain clusters using topological border extraction and component labeling (`scipy.ndimage`, `skimage.measure.find_contours`).
- **Graph-Based Cell Tracking:** Project advected centroids forward in time and map spatial overlaps into directed graphs (`networkx`), explicitly resolving merges, splits, and births.
- **Morphological Geometry Classification:** Fit planar convex hulls to `skimage.measure.EllipseModel` to compute eccentricity indices ($e > 0.8$), isolating linear convective squall lines from disorganized systems.
- **Geospatial-Native Integration:** Ingest spatiotemporal `xarray.DataArray` grids and output projected, attribute-rich `geopandas.GeoDataFrame` objects.

---

## Installation

### Prerequisites

Geospatial libraries (`geopandas`, `shapely`) often depend on system-level C libraries (`GEOS`, `PROJ`, `GDAL`). Installing via `conda` or standard virtual environments (`venv`) is recommended.

### Option 1: Conda Environment (Recommended)

```bash
# Clone the repository
git clone https://github.com/JYDiong/sqtrack.git
cd sqtrack

# Create and activate environment
conda create -n sqtrack python=3.10 -y
conda activate sqtrack

# Install dependencies and sqtrack in editable mode
pip install -e .
```

### Option 2: Standard pip / Virtual Environment

```bash
# Clone the repository
git clone https://github.com/JYDiong/sqtrack.git
cd sqtrack

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install editable package
pip install -e .
```

---

## Quickstart

```python
import xarray as xr
from sqtrack import (
    detect_features_time_series,
    track_squalls_graph,
    evaluate_squall_eccentricity,
    consolidate_track_categories,
)

# 1. Load gridded radar/satellite precipitation data
ds = xr.open_dataset("sample_precipitation.nc")
precip_da = ds["rainfall"]  # Expected dims: (time, lat, lon)

# 2. Extract storm contours over each time frame
contour_sets = detect_features_time_series(
    precip_da, 
    size_filter=True, 
    rf_threshold=1.0  # Intensity threshold
)

# 3. Track storm cells across the time series using graph tracking
tracked_df, track_graph = track_squalls_graph(
    contour_sets, 
    precip_da.time.values, 
    overlap_threshold=0.5
)

# 4. Classify morphology (eccentricity)
tracked_df["category"] = evaluate_squall_eccentricity(tracked_df)

# 5. Consolidate majority track categorization over full lifespan
summary_df = consolidate_track_categories(
    tracked_df, 
    id_col="id", 
    category_col="category"
)

print(summary_df.head())
```

---

## Repository Structure

```text
sqtrack/
├── pyproject.toml               # Build configuration & metadata
├── setup.py                     # Setuptools compatibility shim
├── README.md                    # Project documentation
├── .gitignore                   # Ignored files & cache tracking
└── sqtrack/                     # Core package
    ├── __init__.py              # Public API exports
    ├── core.py                  # Feature extraction & graph tracking logic
    └── classification.py        # Ellipse fitting & morphological classification
```

---

## Methodological Summary

1. **Extraction:** Precipitation fields are thresholded, labeled via structured connectivity arrays, and mapped into closed contours converted to polygon geometries on EPSG:4326.
2. **Kinematic Projection:** Storm polygons are projected along metric spatial coordinates (`EPSG:32663`) to estimate intersection area fractions at $t + \Delta t$.
3. **Graph Trajectory:** Overlap fractions $\ge \text{threshold}$ form directed edges $(u_t \to v_{t+1})$. Connected components and predecessor/successor topologies resolve splits (divergent branches) and merges (convergent branches).
4. **Eccentricity Classification:** Planar coordinates along convex hulls are fitted to standard Cartesian ellipse equations:
   $$\frac{(x-x_c)^2}{a^2} + \frac{(y-y_c)^2}{b^2} = 1, \quad e = \sqrt{1 - \left(\frac{b}{a}\right)^2}$$
   Features with $e > 0.8$ are classified as candidate squall lines.

---

## Citation

If you use `sqtrack` in your research or operational workflows, please cite the underlying methodology:

> Diong, J.-Y., Xavier, P., Abdullah, M. F. A., & Schwendike, J. (2026). The characteristics of squall lines in the Southeast Asia region. *Quarterly Journal of the Royal Meteorological Society*, e70143. https://doi.org/10.1002/qj.70143

### BibTeX

```bibtex
@article{diong2026characteristics,
  author    = {Diong, Jeong-Yik and Xavier, Prince and Abdullah, M. F. A. and Schwendike, Juliane},
  title     = {The characteristics of squall lines in the Southeast Asia region},
  journal   = {Quarterly Journal of the Royal Meteorological Society},
  year      = {2026},
  doi       = {10.1002/qj.70143},
  url       = {[https://doi.org/10.1002/qj.70143](https://doi.org/10.1002/qj.70143)}
}

## License

This project is licensed under the [MIT License](LICENSE).
