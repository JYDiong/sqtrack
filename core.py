import functools
import logging
import warnings
import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from scipy import ndimage
from shapely.affinity import translate
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from skimage.measure import find_contours

logger = logging.getLogger(__name__)


def sort_features_east_west(
    rad: gpd.GeoDataFrame, reset_index: bool = False
) -> gpd.GeoDataFrame:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        rad = rad.assign(x=rad.geometry.centroid.x)
    rad_sorted = rad.sort_values("x", ascending=False).drop(columns="x")
    if reset_index:
        rad_sorted = rad_sorted.reset_index(drop=True)
    return rad_sorted


def extract_precipitation_contours(rf: xr.DataArray, value: float = 1.0):
    if rf.isnull().all():
        raise ValueError("input array is all null")
    if "lat" in rf.dims and "lon" in rf.dims:
        rf = rf.transpose("lat", "lon")

    rf2 = rf.compute()
    data, lons, lats = rf2.values, rf2.lon.values, rf2.lat.values

    mask = data >= value
    structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
    labeled, num = ndimage.label(mask, structure=structure)

    contours_ll, centroids_ll = [], []
    for lab in range(1, num + 1):
        region = labeled == lab
        if region.sum() < 4:
            continue
        yc, xc = ndimage.center_of_mass(data, labeled, lab)
        if np.isnan(xc) or np.isnan(yc):
            continue

        lon_c = np.interp(xc, np.arange(len(lons)), lons)
        lat_c = np.interp(yc, np.arange(len(lats)), lats)
        centroids_ll.append((lon_c, lat_c))

        cs = find_contours(region.astype(float), 0.5)
        if not cs:
            continue
        c = max(cs, key=lambda a: a.shape[0])
        rr, cc = np.clip(c[:, 0], 0, len(lats) - 1), np.clip(
            c[:, 1], 0, len(lons) - 1
        )

        lon = np.interp(cc, np.arange(len(lons)), lons)
        lat = np.interp(rr, np.arange(len(lats)), lats)
        coords = np.column_stack([lon, lat])
        coords = coords[~np.isnan(coords).any(axis=1)]

        if coords.shape[0] >= 4:
            contours_ll.append(coords)

    return contours_ll, centroids_ll


def convert_contours_to_geodataframe(contours_ll, centroids):
    polys, clons, clats = [], [], []
    for coords, (lon_c, lat_c) in zip(contours_ll, centroids):
        if coords.shape[0] < 4:
            continue
        try:
            poly = Polygon(coords)
            if poly.is_valid and poly.area > 0:
                polys.append(orient(poly))
                clons.append(lon_c)
                clats.append(lat_c)
        except Exception as e:
            logger.warning(f"Polygon construction failed: {e}")

    gdf = gpd.GeoDataFrame(
        {"centroid_lon": clons, "centroid_lat": clats, "geometry": polys},
        crs="EPSG:4326",
    )
    if not gdf.empty:
        gdf["area_km2"] = gdf.to_crs("EPSG:32663").area / 10**6
    else:
        gdf["area_km2"] = []
    return gdf


def filter_features_by_area(
    radar: gpd.GeoDataFrame, threshold: float = 1000.0
) -> gpd.GeoDataFrame:
    if "area_km2" not in radar.columns:
        radar["area_km2"] = radar.to_crs("EPSG:32663").area / 10**6
    return radar[radar["area_km2"] >= threshold].reset_index(drop=True)


def detect_features_single_frame(
    rf: xr.DataArray, size_filter: bool = True, rf_threshold: float = 1.0
) -> gpd.GeoDataFrame:
    contours_ll, centroids = extract_precipitation_contours(rf, rf_threshold)
    radar = convert_contours_to_geodataframe(contours_ll, centroids)
    if not radar.empty:
        radar = sort_features_east_west(radar).reset_index(drop=True)
        if size_filter:
            radar = filter_features_by_area(radar)
    return radar


def detect_features_time_series(
    rf: xr.DataArray, size_filter: bool = True, rf_threshold: float = 1.0
) -> list:
    f = functools.partial(
        detect_features_single_frame,
        size_filter=size_filter,
        rf_threshold=rf_threshold,
    )
    if len(rf.dims) == 2:
        return [f(rf)]
    elif len(rf.dims) == 3 and "time" in rf.dims:
        return [f(rf.isel(time=i)) for i in range(rf.time.size)]


def translate_geoseries(s: gpd.GeoSeries, dx: float) -> gpd.GeoSeries:
    original_crs = s.crs
    projected = s.to_crs("EPSG:32663")
    translated = projected.apply(lambda geom: translate(geom, xoff=dx))
    return translated.to_crs(original_crs)


def project_forward_in_time(
    df: gpd.GeoDataFrame, dt: float = 1800
) -> gpd.GeoDataFrame:
    dx = (dt / 3600.0) * 1.0
    new_geometry = translate_geoseries(df.geometry, dx=dx)
    return df.assign(geometry=new_geometry)


def compute_spatial_overlap_matrix(
    r1: gpd.GeoDataFrame, r2: gpd.GeoDataFrame
) -> dict:
    r1_projected = r1.to_crs("EPSG:32663")
    r1_area = r1_projected.area
    res = {}
    for i, r1_i in r1_projected.iterrows():
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            inter = r2.to_crs("EPSG:32663").intersection(r1_i.geometry)
        inter = inter[~inter.is_empty]
        overlap_areas = inter.area / r1_area.iloc[i]
        res[i] = overlap_areas.to_dict()
    return res


def track_squalls_parent_inheritance(
    contour_sets, Time, overlap_threshold: float = 0.5
):
    times = pd.DatetimeIndex(Time)
    itimes = list(range(times.size))
    dt = times[1:] - times[:-1]
    dt = dt.insert(len(dt), dt[-1])

    css, next_track_id = [], 0

    cs_0 = contour_sets[0].copy()
    cs_0["time"], cs_0["itime"], cs_0["dtime"] = times[0], 0, dt[0]
    n_0 = len(cs_0)
    cs_0["id"] = list(range(next_track_id, next_track_id + n_0))
    cs_0["parent_id"] = -1
    next_track_id += n_0
    css.append(cs_0)

    for i in itimes[1:]:
        cs_i = contour_sets[i].copy()
        cs_i["time"], cs_i["itime"], cs_i["dtime"] = times[i], i, dt[i]

        cs_im1 = css[-1]
        dt_im1_s = dt[i - 1].total_seconds()

        if cs_i.empty or cs_im1.empty:
            n_i = len(cs_i)
            cs_i["id"] = list(range(next_track_id, next_track_id + n_i))
            cs_i["parent_id"] = -1
            next_track_id += n_i
            css.append(cs_i)
            continue

        ovs = compute_spatial_overlap_matrix(
            cs_i, project_forward_in_time(cs_im1, dt=dt_im1_s)
        )

        assigned_ids, absorbed_parent_ids = [], []

        for curr_idx, overlaps in ovs.items():
            valid_parents = {
                prev_idx: frac
                for prev_idx, frac in overlaps.items()
                if frac >= overlap_threshold
            }

            if not valid_parents:
                assigned_ids.append(next_track_id)
                absorbed_parent_ids.append(-1)
                next_track_id += 1
            elif len(valid_parents) == 1:
                parent_idx = list(valid_parents.keys())[0]
                assigned_ids.append(cs_im1.loc[parent_idx, "id"])
                absorbed_parent_ids.append(-1)
            else:
                dominant_parent_idx = max(
                    valid_parents, key=lambda k: cs_im1.loc[k, "area_km2"]
                )
                primary_id = cs_im1.loc[dominant_parent_idx, "id"]
                assigned_ids.append(primary_id)

                secondary_parents = [
                    cs_im1.loc[k, "id"]
                    for k in valid_parents
                    if k != dominant_parent_idx
                ]
                absorbed_parent_ids.append(
                    secondary_parents[0] if secondary_parents else -1
                )

        cs_i["id"] = assigned_ids
        cs_i["parent_id"] = absorbed_parent_ids
        css.append(cs_i)

    return pd.concat(css, ignore_index=True)