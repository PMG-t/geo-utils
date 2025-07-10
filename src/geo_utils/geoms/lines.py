import os

import numpy as np
from shapely.geometry import Point, LineString, MultiLineString

from geo_utils.spatial import coords


def line_from_points(points: list | tuple | np.ndarray) -> LineString:
    """
    Create a LineString from a list, tuple, or numpy array of coordinates.

    Args:
        coords (list | tuple | np.ndarray): Coordinates to create the LineString.

    Returns:
        LineString: A Shapely LineString object.
    """
    
    points = [coords.point2shape(p) for p in points]
    return LineString(points)


def explode_multiline(mls: MultiLineString) -> list[LineString]:
    """
    Explode a MultiLineString into a list of LineStrings.

    Args:
        mls (MultiLineString): A Shapely MultiLineString object.

    Returns:
        list[LineString]: A list of Shapely LineString objects.
    """
    
    if isinstance(mls, LineString):
        return [LineString(mls.coords)]
    
    if not isinstance(mls, MultiLineString):
        raise TypeError("Input must be a MultiLineString.")
    
    return [LineString(line.coords) for line in mls.geoms]


def resample(line: LineString, distance: float) -> LineString:
    """
    Resample a LineString to a specified distance.

    Args:
        line (LineString): The input LineString to resample.
        distance (float): The distance between resampled points.

    Returns:
        LineString: A new LineString with resampled points.
    """
    
    resampled_segments = [coords.points_between(point, line.coords[ip + 1], distance, endpoint=False) for ip,point in enumerate(line.coords[:-1])]
    resampled_points = [point for segment in resampled_segments for point in segment]
    resampled_points.append(line.coords[-1])
    return LineString(resampled_points)
        
    
def concat_distance(line1: LineString, line2: LineString, distance_f: callable = None) -> float:
    """
    Distance between last point of line1 and first point of line2.

    Args:
        line1 (LineString): The first LineString.
        line2 (LineString): The second LineString.

    Returns:
        float: The distance between the last point of line1 and the first point of line2.
    """
    
    distance_f = distance_f if distance_f is not None else coords.projected_distance
    return distance_f(line1.coords[-1], line2.coords[0])


def point_distance(line: LineString, point: list | tuple | np.ndarray | Point, distance_f: callable | None = None, vals_callback: callable | None = np.min) -> float:
    """
    Distance between a point and the closest point on a LineString.

    Args:
        line (LineString): The LineString to measure against.
        point (tuple | list | np.ndarray): The point to measure the distance from.
        distance_f (callable, optional): A function to calculate the distance. Defaults to coords.projected_distance.
        vals_callback (callable, optional): A callback function to process the distances. Defaults to None.

    Returns:
        float: The distance from the point to the closest point on the LineString.
    """
    
    point = coords.point2shape(point)
    
    distance_f = distance_f if distance_f is not None else coords.projected_distance
    distances = np.array([distance_f(point, p) for p in line.coords])
    if vals_callback is not None:
        distances = vals_callback(distances)
    return distances


def line_distance(line1: LineString, line2: LineString, distance_f: callable = None, vals_callbacks: callable | tuple[callable] | None = np.min) -> float:
    """
    Distance between two LineStrings.

    Args:
        line1 (LineString): The first LineString.
        line2 (LineString): The second LineString.
        distance_f (callable, optional): A function to calculate the distance. Defaults to coords.projected_distance.
        vals_callbacks (callable | tuple[callable] | None, optional): A callback function to process the distances. If a tuple is provided, the first element is used for the distance calculation and the second for the point-to-line distance. Defaults to np.min.

    Returns:
        float: The distance between the two LineStrings.
    """
    
    if vals_callbacks is not None:
        if isinstance(vals_callbacks, callable):
            vals_callback = vals_callbacks
            l2_to_p1_callback = vals_callbacks
        elif isinstance(vals_callbacks, tuple):
            vals_callback = vals_callbacks[0] if len(vals_callbacks) > 0 else None
            l2_to_p1_callback = vals_callbacks[1] if len(vals_callbacks) > 1 else vals_callbacks
    else:
        vals_callback = None
        l2_to_p1_callback = None
        
    distance_f = distance_f if distance_f is not None else coords.projected_distance
    distances = np.array([
        point_distance(line1, p, distance_f=distance_f, vals_callback=l2_to_p1_callback)
        for p in line2.coords
    ])
    if vals_callback is not None:
        distances = vals_callback(distances)
    return distances

