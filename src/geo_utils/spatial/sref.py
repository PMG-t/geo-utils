import os
from enum import Enum
from osgeo import osr

from geo_utils.base import _utils
from geo_utils.spatial import coords



_USE_EXCEPTIONS: bool = True



class CRSType():
    """
    Enum representing different types of Coordinate Reference Systems (CRS).
    """
    EPSG = "EPSG"
    WKT = "WKT"
    PROJ = "PROJ"
    OGC_URN = "OGC_URN"
    OGC_URL = "OGC_URL"
    


def is_epsg(crs: str) -> bool:
    """
    Checks if a given CRS string is a valid EPSG code recognized by GDAL.
    
    Args:
        crs (str): The CRS string to check, e.g., "EPSG:4326" or "4326".
        
    Returns:
        bool: True if the CRS is a valid EPSG code, False otherwise.
    """
    try:
        if crs.upper().startswith("EPSG:"):
            code = int(crs.split(":")[1])
        else:
            code = int(crs)
        srs = osr.SpatialReference()
        return srs.ImportFromEPSG(code) == 0
    except:
        return False
    

def epsg_code(crs: str | osr.SpatialReference) -> int | None:
    """
    Extracts the EPSG code from a CRS string or osr.SpatialReference object.

    Args:
        crs (str | osr.SpatialReference): The CRS string or SpatialReference object.

    Returns:
        int | None: The EPSG code as an integer, or None if not found.
    
    Raises:
        ValueError: If the CRS string is not recognized and module _USE_EXCEPTIONS is True.
    """
    srs = load_crs(crs)
    code = srs.GetAuthorityCode(None)
    if code is None:
        if _USE_EXCEPTIONS:
            raise ValueError(f"EPSG code not found for CRS: {crs}")
        return None
    return int(code)
    
    
def epsg_str(crs: str | osr.SpatialReference) -> str | None:
    """
    Converts a CRS string or osr.SpatialReference object to an EPSG string.

    Args:
        crs (str | osr.SpatialReference): The CRS string or SpatialReference object.

    Returns:
        str | None: The EPSG string in the format "EPSG:<code>", or None if not found.
    
    Raises:
        ValueError: If the CRS string is not recognized and module _USE_EXCEPTIONS is True.
    """
    epsg_string = to_crs_type(crs, "EPSG")
    if epsg_string is None:
        if _USE_EXCEPTIONS:
            raise ValueError(f"EPSG string not found for CRS: {crs}")
        return None
    return epsg_string    
   
    
def is_wkt(crs: str) -> bool:
    """
    Checks if a given CRS string is a valid WKT (Well-Known Text) format recognized by GDAL.
    
    Args:
        crs (str): The CRS string to check, e.g., a WKT representation of a coordinate reference system.
        
    Returns:
        bool: True if the CRS is a valid WKT format, False otherwise.
    """
    srs = osr.SpatialReference()
    return srs.ImportFromWkt(crs) == 0

    
def is_proj4(crs: str) -> bool:
    """
    Checks if a given CRS string is a valid PROJ.4 format recognized by GDAL.
    
    Args:
        crs (str): The CRS string to check, e.g., a PROJ.4 representation of a coordinate reference system.
        
    Returns:
        bool: True if the CRS is a valid PROJ.4 format, False otherwise.
    """
    srs = osr.SpatialReference()
    return srs.ImportFromProj4(crs) == 0


def is_ogc_urn(crs: str) -> bool:
    """
    Checks if a given CRS string is a valid OGC URN format recognized by GDAL.
    
    Args:
        crs (str): The CRS string to check, e.g., "urn:ogc:def:crs:EPSG::4326".
        
    Returns:
        bool: True if the CRS is a valid OGC URN format, False otherwise.
    """
    srs = osr.SpatialReference()
    return srs.SetFromUserInput(crs) == 0 and crs.lower().startswith("urn:ogc:def:crs:")

    
def is_ogc_url(crs: str) -> bool:
    """
    Checks if a given CRS string is a valid OGC URL format recognized by GDAL.
    
    Args:
        crs (str): The CRS string to check, e.g., "http://www.opengis.net/def/crs/EPSG/0/4326".
    
    Returns:
        bool: True if the CRS is a valid OGC URL format, False otherwise.
    """
    srs = osr.SpatialReference()
    return srs.SetFromUserInput(crs) == 0 and crs.lower().startswith("http://www.opengis.net/def/crs/")


def detect_crs_type(crs: str) -> str:
    """
    Detects the type of a given CRS string.
    
    Args:
        crs (str): The CRS string to check, e.g., "EPSG:4326", WKT, PROJ.4, OGC URN, or OGC URL.
    
    Returns:
        str: The type of the CRS string, one of "EPSG", "WKT", "PROJ", "OGC_URN", "OGC_URL".
    """
    
    if is_epsg(crs):
        return CRSType.EPSG
    elif is_wkt(crs):
        return CRSType.WKT
    elif is_proj4(crs):
        return CRSType.PROJ
    elif is_ogc_urn(crs):
        return CRSType.OGC_URN
    elif is_ogc_url(crs):
        return CRSType.OGC_URL
    else:
        if _USE_EXCEPTIONS:
            raise ValueError(f"Unknown CRS type for: {crs}")
        return None
    
    
def from_crs_str(crs: str) -> osr.SpatialReference:
    """
    Converts a CRS string to an osr.SpatialReference object.

    Args:
        crs (str): The CRS string to convert, e.g., "EPSG:4326", WKT, PROJ.4, OGC URN, or OGC URL.

    Returns:
        osr.SpatialReference: The corresponding SpatialReference object.
    
    Raises:
        ValueError: If the CRS string is not recognized and module _USE_EXCEPTIONS is True.
    """
    srs = osr.SpatialReference()
    if srs.SetFromUserInput(crs) != 0:
        if _USE_EXCEPTIONS:
            raise ValueError(f"Invalid CRS string: {crs}")
        return None
    return srs


def load_crs(crs: str | osr.SpatialReference) -> osr.SpatialReference:
    """
    Loads a CRS from a string or osr.SpatialReference object.

    Args:
        crs (str | osr.SpatialReference): The CRS string or SpatialReference object to load.

    Returns:
        osr.SpatialReference: The loaded SpatialReference object.
    
    Raises:
        ValueError: If the CRS string is not recognized and module _USE_EXCEPTIONS is True.
    """
    if isinstance(crs, str):
        return from_crs_str(crs)
    elif isinstance(crs, osr.SpatialReference):
        return crs
    else:
        if _USE_EXCEPTIONS:
            raise ValueError(f"Invalid CRS type: {type(crs)}")
        return None


def to_crs_type(crs: str | osr.SpatialReference, crs_type: str) -> str:
    """
    Converts a CRS string to a specified type (EPSG, WKT, PROJ, OGC_URN, OGC_URL).

    Args:
        crs (str): The CRS string to convert.
        crs_type (str): The target CRS type, one of "EPSG", "WKT", "PROJ", "OGC_URN", "OGC_URL".

    Returns:
        str: The converted CRS string in the specified format.

    Raises:
        ValueError: If the conversion is not possible or the target type is invalid.
    """
    srs = load_crs(crs)
    
    if crs_type.upper() == CRSType.EPSG:
        def export_to_epsg(srs: osr.SpatialReference) -> str | None:
            auth = srs.GetAuthorityName(None)
            code = srs.GetAuthorityCode(None)
            if auth and code:
                return f"{auth.upper()}:{code}"
            elif _USE_EXCEPTIONS:
                raise ValueError("Invalid EPSG code: Authority or code not found")
            return None
        return export_to_epsg(srs)
    elif crs_type.upper() == CRSType.WKT:
        return srs.ExportToWkt()
    elif crs_type.upper() == CRSType.PROJ:
        return srs.ExportToProj4()
    elif crs_type.upper() == CRSType.OGC_URN:
        def export_to_ogc_urn(srs: osr.SpatialReference) -> str | None:
            authority = srs.GetAuthorityName(None)
            code = srs.GetAuthorityCode(None)
            if authority and code:
                return f"urn:ogc:def:crs:{authority}::{code}"
            elif _USE_EXCEPTIONS:
                raise ValueError("Invalid OGC URN: Authority or code not found")
            return None
        return export_to_ogc_urn(srs)
    elif crs_type.upper() == CRSType.OGC_URL:
        def export_to_ogc_url(srs: osr.SpatialReference) -> str | None:
            authority = srs.GetAuthorityName(None)
            code = srs.GetAuthorityCode(None)
            if authority and code:
                return f"http://www.opengis.net/def/crs/{authority}/0/{code}"
            elif _USE_EXCEPTIONS:
                raise ValueError("Invalid OGC URL: Authority or code not found")
            return None
        return export_to_ogc_url(srs)
    else:
        if _USE_EXCEPTIONS:
            raise ValueError(f"Invalid CRS type: {crs_type}")
        return None


def utm_code(lat: float, lon: float) -> str:
    """
    Get the UTM (Universal Transverse Mercator) zone code for a given latitude and longitude.
    
    Args:
        lat (float): Latitude in degrees.
        lon (float): Longitude in degrees.
    
    Returns:
        str: The UTM zone code in the format "EPSG:<code>", where <code> is the UTM zone number.
    """
    zone = int((lon + 180) / 6) + 1
    hemisphere = 32600 if lat >= 0 else 32700
    code = hemisphere + zone
    return code


def utm_crs(lat: float, lon: float, crs_type: str | None) -> str | osr.SpatialReference:
    """
    Get the UTM (Universal Transverse Mercator) coordinate reference system for a given latitude and longitude.
    
    Args:
        lat (float): Latitude in degrees.
        lon (float): Longitude in degrees.
        crs_type (str | None): The desired CRS type to return, one of "EPSG", "WKT", "PROJ", "OGC_URN", "OGC_URL". If None, returns osr.SpatialReference object.
        
    Returns:
        str | osr.SpatialReference: The UTM CRS in the specified format, or an osr.SpatialReference object if crs_type is None.
    """
    
    code = utm_code(lat, lon)
    srs = from_crs_str(f"EPSG:{code}")
    if srs is None:
        if _USE_EXCEPTIONS:
            raise ValueError(f"Invalid UTM CRS for zone {code} and hemisphere {'N' if lat >= 0 else 'S'}")
        return None
    if crs_type is not None:
        srs = to_crs_type(srs, crs_type)
        if srs is None:
            if _USE_EXCEPTIONS:
                raise ValueError(f"Invalid CRS type: {crs_type}")
            return None
        return srs
    return srs
    

def is_valid_crs(crs: str | osr.SpatialReference) -> bool:
    """
    Checks if a given CRS string or osr.SpatialReference object is valid.
    
    Args:
        crs (str | osr.SpatialReference): The CRS string or SpatialReference object to check.
        
    Returns:
        bool: True if the CRS is valid, False otherwise.
    """
    try:
        srs = load_crs(crs)
        return srs.Validate() == 0
    except Exception as e:
        if _USE_EXCEPTIONS:
            raise ValueError(f"Invalid CRS: {crs}") from e
        return False
    

def is_geographic(crs: str | osr.SpatialReference) -> bool:
    """
    Checks if a given CRS string or osr.SpatialReference object is geographic (latitude/longitude).
    
    Args:
        crs (str | osr.SpatialReference): The CRS string or SpatialReference object to check.
        
    Returns:
        bool: True if the CRS is geographic, False otherwise.
    """
    try:
        srs = load_crs(crs)
        return srs.IsGeographic() == 1
    except Exception as e:
        if _USE_EXCEPTIONS:
            raise ValueError(f"Invalid CRS: {crs}") from e
        return False
    
    
def is_projected(crs: str | osr.SpatialReference) -> bool:
    """
    Checks if a given CRS string or osr.SpatialReference object is projected (e.g., UTM).
    
    Args:
        crs (str | osr.SpatialReference): The CRS string or SpatialReference object to check.
        
    Returns:
        bool: True if the CRS is projected, False otherwise.
    """
    try:
        srs = load_crs(crs)
        return srs.IsProjected() == 1
    except Exception as e:
        if _USE_EXCEPTIONS:
            raise ValueError(f"Invalid CRS: {crs}") from e
        return False
    
    
def crs_distance_function(crs: str) -> callable:
    """
    Returns a function to calculate distances in the specified CRS.
    
    Args:
        crs (str): The CRS string, e.g., "EPSG:4326".
        
    Returns:
        callable: A function that takes two points and returns the distance in meters.
    """
    srs = load_crs(crs)
    
    if srs.IsGeographic():
        return coords.geographic_distance
    elif srs.IsProjected():
        return coords.projected_distance
    else:
        raise ValueError(f"Unsupported CRS type for distance calculation: {crs}")