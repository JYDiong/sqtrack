from setuptools import find_packages, setup

setup(
    name="sqtrack",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "xarray",
        "geopandas",
        "shapely",
        "scikit-image",
        "scipy",
        "matplotlib",
        "networkx",
    ],
)
