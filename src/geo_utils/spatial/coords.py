import os
import math

import numpy as np

import geopandas as gpd
from shapely.geometry import Point

from osgeo import osr
from geopy.distance import geodesic

from geo_utils.base import _utils
from geo_utils.spatial import sref, um


_USE_EXCEPTION: bool = True


def point2shape(coord: list | tuple | np.ndarray | Point) -> Point:
    """
    Converts a coordinate to a 2D Point object.
    
    Args:
        coord (list, tuple, np.ndarray, Point): The coordinate to convert.

    Returns:
        Point: A 2D Point object.
    """
    if isinstance(coord, Point):
        return coord
    if isinstance(coord, (list, tuple)):
        return Point(*coord)
    if isinstance(coord, np.ndarray):
        return Point(coord[0], coord[1])
    raise ValueError("Unsupported coordinate type for conversion to Point.")


def point2array(coord: list | tuple | np.ndarray | Point) -> np.ndarray:
    """
    Converts a coordinate to a 2D numpy array.
    
    Args:
        coord (list, tuple, np.ndarray, Point): The coordinate to convert.

    Returns:
        np.ndarray: A 2D numpy array with the coordinate.
    """
    if isinstance(coord, Point):
        return np.array([coord.x, coord.y])
    if isinstance(coord, (list, tuple)):
        return np.array(coord)
    if isinstance(coord, np.ndarray):
        return coord[:2]  # Ensure only the first two dimensions are returned
    raise ValueError("Unsupported coordinate type for conversion to numpy array.")


def point2type(coord: list | tuple | np.ndarray | Point, ptype: type) -> list | tuple | np.ndarray | Point:
    """
    Converts a coordinate to a specified type.
    
    Args:
        coord (list, tuple, np.ndarray, Point): The coordinate to convert.
        ptype (type): The type to convert the coordinate to (e.g., list, tuple, np.ndarray, Point).

    Returns:
        Converted coordinate in the specified type.
    """
    if ptype is Point:
        return point2shape(coord)
    elif ptype is np.ndarray:
        return point2array(coord)
    elif ptype is list:
        return point2array(coord).tolist()
    elif ptype is tuple:
        return tuple(point2array(coord))
    
    raise ValueError(f"Unsupported type for conversion: {ptype}.")


def projected_distance(coord1: list | tuple | np.ndarray | Point, coord2: list | tuple | np.ndarray | Point)-> float:
    """
    Computes the Euclidean distance between two coordinates in a projected CRS.
    
    Args:
        coord1 (list, tuple, np.ndarray, Point): The first coordinate.
        coord2 (list, tuple, np.ndarray, Point): The second coordinate.

    Returns:
        Distance in the same unit of the CRS (e.g., meters).
    """
    coord1 = point2array(coord1)
    coord2 = point2array(coord2)

    return np.linalg.norm(coord1 - coord2)


def geographic_distance(coord1: list | tuple | np.ndarray | Point, coord2: list | tuple | np.ndarray | Point) -> float:
    """
    Computes the geodesic distance (in meters) between two geographic coordinates.

    Args:
        coord1 (list, tuple, np.ndarray, Point): The first coordinate (latitude, longitude).
        coord2 (list, tuple, np.ndarray, Point): The second coordinate (latitude, longitude).

    Returns:
        Distance in degrees.
    """
    coord1 = point2array(coord1)
    coord2 = point2array(coord2)
        
    return um.m2dg(geodesic(coord1, coord2).meters, lat = (coord1[1] + coord2[1]) / 2)


def point_line_eq(coord1: list | tuple | np.ndarray | Point, coord2: list | tuple | np.ndarray | Point) -> tuple[float, float]:
    """
    Computes the slope (m) and y-intercept (q) of the line passing through two points.
    
    Args:
        coord1 (list, tuple, np.ndarray, Point): The first coordinate (x0, y0).
        coord2 (list, tuple, np.ndarray, Point): The second coordinate (x1, y1).
        
    Returns:
        tuple: The slope (m) and y-intercept (q) of the line. In case of a vertical line, returns (inf, y0).
    """
    
    coord1 = point2array(coord1)
    coord2 = point2array(coord2)
    
    x0, y0 = coord1
    x1, y1 = coord2
    
    if x1 == x0:
        return np.inf, y0  # Vertical line case, slope is infinite
    
    m = (y1 - y0) / (x1 - x0)
    q = y0 - m * x0
    
    return m, q 


def perpedicular_line(coord1: list | tuple | np.ndarray | Point, coord2: list | tuple | np.ndarray | Point, coord: list | tuple | np.ndarray | Point) -> tuple[float, float]:
    """
    Computes the slope (m) and y-intercept (q) of the perpendicular line to the segment coord1 -> coord2 that passes through coord.
    
    Args:
        coord1 (list, tuple, np.ndarray, Point): The first coordinate (x0, y0).
        coord2 (list, tuple, np.ndarray, Point): The second coordinate (x1, y1).
        coord (list, tuple, np.ndarray, Point): The point through which the perpendicular line passes (x, y).
        
    Returns:
        tuple: The slope (m) and y-intercept (q) of the perpendicular line. In case of a vertical line, returns (0, y).
    """
    
    m_line, _ = point_line_eq(coord1, coord2)
    
    if m_line == 0:
        return np.inf, coord[1]  # Perpendicular to a horizontal line is vertical
    
    if m_line == np.inf:
        return 0.0, coord[1]  # Perpendicular to a vertical line is horizontal
    
    m_perp = -1 / m_line
    q_perp = coord[1] - m_perp * coord[0]
    
    return m_perp, q_perp


def middle_point(coord1: list | tuple | np.ndarray | Point, coord2: list | tuple | np.ndarray | Point) -> list | tuple | np.ndarray | Point:
    """
    Computes the middle point between two coordinates.
    
    Args:
        coord1 (list, tuple, np.ndarray, Point): The first coordinate.
        coord2 (list, tuple, np.ndarray, Point): The second coordinate.
        
    Returns:
        tuple: The coordinates of the middle point (x, y).
    """
    
    return_type = type(coord1)
    
    coord1 = point2array(coord1)
    coord2 = point2array(coord2)
    
    x1, y1 = coord1
    x2, y2 = coord2
    
    x_mid = (x1 + x2) / 2
    y_mid = (y1 + y2) / 2
    
    return point2type((x_mid, y_mid), return_type)


def next_point(coord1: list | tuple | np.ndarray | Point, coord2: list | tuple | np.ndarray | Point, distance: float) -> list | tuple | np.ndarray | Point:
    """
    Computes the next point in the direction from coord1 to coord2 at a specified distance.
    
    Args:
        coord1 (list, tuple, np.ndarray, Point): The starting coordinate.
        coord2 (list, tuple, np.ndarray, Point): The ending coordinate.
        distance (float): The distance to move from coord2 in the direction of coord1.
        
    Returns:
        tuple: The coordinates of the next point (x, y).
    """
    
    return_type = type(coord1)
    
    coord1 = point2array(coord1)
    coord2 = point2array(coord2)
    
    x1, y1 = coord1
    x2, y2 = coord2
    
    vx, vy = x2 - x1, y2 - y1
    v_length = np.sqrt(vx**2 + vy**2)
    
    ux, uy = vx / v_length, vy / v_length
    
    x3 = x2 + distance * ux
    y3 = y2 + distance * uy
    
    return point2type((x3, y3), return_type)


def determinant(coord1: list | tuple | np.ndarray | Point, coord2: list | tuple | np.ndarray | Point, coord: list | tuple | np.ndarray | Point) -> float:
    """
    Calculates the determinant to determine where a point p is with respect to the oriented segment coord1 -> p1.

    Args:
        coord1 (list | tuple | np.ndarray | Point): Starting point of the segment (x0, y0).
        coord2 (list | tuple | np.ndarray | Point): Ending point of the segment (x1, y1).
        coord (list | tuple | np.ndarray | Point): Point to check (x, y).

    Returns:
        float: Determinant (positive, negative or zero).
    """
    coord1 = point2array(coord1)
    coord2 = point2array(coord2)
    coord = point2array(coord)

    return (coord2[0] - coord1[0]) * (coord[1] - coord1[1]) - (coord2[1] - coord1[1]) * (coord[0] - coord1[0])


def point_position(coord1: list | tuple | np.ndarray | Point, coord2: list | tuple | np.ndarray | Point, coord: list | tuple | np.ndarray | Point) -> int:
    """
    Calc the determinant to determine where a point p is with respect to the oriented segment p0 -> p1.

    Args:
        coord1 (tuple): Starting point of the segment (x0, y0).
        coord2 (tuple): Ending point of the segment (x1, y1).
        coord (tuple): Point to check (x, y)..

    Returns:
        float: 1 if the point is to the left of the segment, -1 if it is to the right, and 0 if it is collinear.
    """
    
    det = determinant(coord1, coord2, coord)
    
    if det > 0:
        return 1
    elif det < 0:
        return -1
    else:
        return 0
    
    
def neighboring_points(coord: list | tuple | np.ndarray | Point, distance: float, m_line: float | None) -> tuple[list | tuple | np.ndarray | Point, list | tuple | np.ndarray | Point]:
    """
    Generates neighboring points around a given coordinate at a specified distance that are on a given line slope.
    
    Args:
        coord (list, tuple, np.ndarray, Point): The center coordinate.
        distance (float): The distance to the neighboring points.
        m_line (float | None): The slope of the line.
        
    Returns:
        tuple (list | tuple | np.ndarray | Point, list | tuple | np.ndarray | Point): Two neighboring points at the specified distance from the center coordinate.
    """
    return_type = type(coord)
    
    coord = point2array(coord)
    x, y = coord
    
    if m_line is None:
        p1 = (x, y + distance)
        p2 = (x, y - distance)
        return p1, p2

    # Get the perpendicular line passing through p0
    qp = y - m_line * x
    # Coeff for the quadratic equation
    a = 1 + m_line**2
    b = -2 * x + 2 * m_line * (qp - y)
    c = x**2 + (qp - y)**2 - distance**2
    
    # Solve the quadratic equation ax^2 + bx + c = 0
    discriminant = b**2 - 4 * a * c
    if discriminant < 0:
        raise ValueError("No real solutions for the quadratic equation, check the distance and slope.")

    sqrt_discriminant = math.sqrt(discriminant)
    x1 = (-b + sqrt_discriminant) / (2 * a)
    y1 = m_line * x1 + qp
    x2 = (-b - sqrt_discriminant) / (2 * a)
    y2 = m_line * x2 + qp

    np1 = point2type((x1, y1), return_type)
    np2 = point2type((x2, y2), return_type)
    
    return np1, np2