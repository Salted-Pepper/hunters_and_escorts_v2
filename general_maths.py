import math
import constants as cs


def calculate_distance(p1, p2) -> float:
    latitudinal_distance_in_km = longitudinal_distance_to_km(p1.y, p2.y)
    mean_latitude = (p1.y + p2.y) / 2
    longitudinal_distance_in_km = latitudinal_distance_to_km(p1.x, p2.x, mean_latitude)
    distance = math.sqrt(latitudinal_distance_in_km ** 2 + longitudinal_distance_in_km ** 2)
    return distance


def longitudinal_distance_to_km(lon_1: float, lon_2: float) -> float:
    return abs((lon_1 - lon_2) * cs.LATITUDE_CONVERSION_FACTOR)


def latitudinal_distance_to_km(lat_1: float, lat_2: float, approx_long: float) -> float:
    return abs((lat_1 - lat_2) * (cs.LONGITUDE_CONVERSION_FACTOR * math.cos(math.radians(approx_long))))


def check_if_point_in_polygons(point, polygons: list) -> bool:
    for polygon in polygons:
        if polygon.contains_point(point):
            return True
    return False
