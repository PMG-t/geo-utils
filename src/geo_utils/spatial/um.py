import os
import math
from osgeo import osr

from .import sref


class UMType():
    """
    Class to handle unit measures in geographic and projected coordinate systems.
    
    Attributes:
        DG (str): Unit measure for degrees.
        M (str): Unit measure for meters.
    """
    DG = 'dg'
    M = 'm'


def m2dg(m: float, lat: float | None = None) -> float:
    """
    Convert meters to degrees.
    
    Args:
        m (float): Distance in meters.
        lat (float, optional): Latitude in degrees. If provided, the conversion will be more accurate.
        lon (float, optional): Longitude in degrees. Not used in this function.
        
    Returns:
        float: Distance in degrees.
    """
    if lat is not None:
        return m / (111320 * abs(math.cos(lat * (3.141592653589793 / 180))))
    else:
        return m / 111320  # Default conversion without latitude consideration
    
    
def dg2m(dg: float, lat: float | None = None) -> float:
    """
    Convert degrees to meters.
    
    Args:
        dg (float): Distance in degrees.
        lat (float, optional): Latitude in degrees. If provided, the conversion will be more accurate.
        
    Returns:
        float: Distance in meters.
    """
    if lat is not None:
        return dg * (111320 * abs(math.cos(lat * (3.141592653589793 / 180))))
    else:
        return dg * 111320  # Default conversion without latitude consideration


def crs_um(crs: str | osr.SpatialReference) -> str:
    """
    Get the unit measure of a Coordinate Reference System (CRS).
    
    Args:
        crs (str | osr.SpatialReference): Coordinate Reference System.
        
    Returns:
        str: Unit measure of the CRS ('dg' for degrees or 'm' for meters).
    """
    crs = sref.load_crs(crs)
    
    if crs.is_geographic():
        return UMType.DG
    else:
        return UMType.M

    
def m2crs_um(crs: str | osr.SpatialReference, m: float = 1.0, lat: float | None = None) -> float:
    """
    Convert meters based into CRS unit measures (dg or m).
    
    Args:
        crs (str | osr.SpatialReference): Coordinate Reference System.
        m (float): Distance in meters. Default is 1.0.
        lat (float, optional): Latitude in degrees. If provided, the conversion will be more accurate.
        
    Returns:
        float: Distance in the CRS unit (degrees or meters).
    """
    crs = sref.load_crs(crs)
    
    if crs_um(crs) == UMType.DG:
        return m2dg(m, lat)
    else:
        return m
    

def dg2crs_um(crs: str | osr.SpatialReference, dg: float = 1.0, lat: float | None = None) -> float:
    """
    Convert degrees based into CRS unit measures (dg or m).
    
    Args:
        crs (str | osr.SpatialReference): Coordinate Reference System.
        dg (float): Distance in degrees. Default is 1.0.
        lat (float, optional): Latitude in degrees. If provided, the conversion will be more accurate.
        
    Returns:
        float: Distance in the CRS unit (degrees or meters).
    """
    crs = sref.load_crs(crs)
    
    if crs_um(crs) == UMType.M:
        return dg2m(dg, lat)
    else:
        return dg