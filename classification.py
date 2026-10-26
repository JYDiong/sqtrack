import geopandas as gpd
import numpy as np
import pandas as pd
from skimage.measure import EllipseModel


def evaluate_squall_eccentricity(rsize: gpd.GeoDataFrame) -> list:
    categories = []
    for geom in rsize.geometry:
        hull = geom.convex_hull
        xyarray1 = np.asarray(hull.exterior.coords)

        m = EllipseModel()
        if not m.estimate(xyarray1):
            categories.append("Non_ellipse")
            continue

        xc, yc, a, b, theta = m.params
        major, minor = (a, b) if a > b else (b, a)
        eccentricity = np.sqrt(1 - (minor / major) ** 2)

        if eccentricity > 0.8:
            categories.append("squall")
        else:
            categories.append("Non_squall")

    return categories


def consolidate_track_categories(
    df: gpd.GeoDataFrame, id_col: str = "id", category_col: str = "category"
) -> pd.DataFrame:
    def decide(group):
        valid = group[category_col].isin(["squall", "Non_squall"])
        n_total = valid.sum()
        if n_total == 0:
            return "Non_ellipse"
        n_squall = (group.loc[valid, category_col] == "squall").sum()
        return "squall" if n_squall >= 0.5 * n_total else "Non_squall"

    return (
        df.groupby(id_col)
        .apply(decide)
        .rename("final_category")
        .reset_index()
    )