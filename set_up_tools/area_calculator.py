from shapely.geometry import Polygon
from geopy.distance import geodesic
import math

# Define the latitude-longitude points
coords = [(25.26, 122.87),
 (24.5, 122.7),
 (23.4867, 122.6),
 (23.4867, 121.5088),
 (24.5983, 121.8950),
 (25.0100, 122.0000),
 (25.6300, 122.0650),
 (25.6300, 122.0650)]

# Convert to Polygon (Shapely expects lon, lat format)
polygon_coords = [(lon, lat) for lat, lon in coords]
polygon = Polygon(polygon_coords)

def polygon_area_geographic(coords):
    """
    Calculate the area of a polygon using the spherical excess method
    for geographic coordinates (lat, lon in degrees).
    """
    # Convert coordinates to radians
    coords_rad = [(math.radians(lat), math.radians(lon)) for lat, lon in coords]
    
    # Earth's radius in meters
    R = 6371000
    
    # Calculate area using spherical coordinates
    n = len(coords_rad)
    area = 0
    
    for i in range(n):
        j = (i + 1) % n
        lat1, lon1 = coords_rad[i]
        lat2, lon2 = coords_rad[j]
        
        # Spherical excess formula component
        area += (lon2 - lon1) * (2 + math.sin(lat1) + math.sin(lat2))
    
    area = abs(area) * R * R / 2
    return area / 1_000_000  # Convert to square kilometers

# Alternative: Use Shapely's built-in area (approximation)
def polygon_area_shapely(coords):
    """
    Use Shapely's area calculation (planar approximation).
    Note: This is less accurate for large geographic areas.
    """
    polygon_coords = [(lon, lat) for lat, lon in coords]
    polygon = Polygon(polygon_coords)
    # Convert from square degrees to approximate square kilometers
    # This is a rough approximation: 1 degree ≈ 111 km at equator
    area_deg2 = polygon.area
    area_km2 = area_deg2 * (111 * 111)  # Very rough approximation
    return area_km2

# Calculate area using geographic method
area_km2 = polygon_area_geographic(coords)
print(f"Geographic Area: {area_km2:.2f} km²")

# Compare with Shapely approximation
area_shapely = polygon_area_shapely(coords)
print(f"Shapely Approximation: {area_shapely:.2f} km²")

# Also show the perimeter for reference
def polygon_perimeter(coords):
    """Calculate perimeter using geodesic distances."""
    perimeter = 0
    for i in range(len(coords)):
        next_i = (i + 1) % len(coords)
        perimeter += geodesic(coords[i], coords[next_i]).kilometers
    return perimeter

perimeter_km = polygon_perimeter(coords)
print(f"Perimeter: {perimeter_km:.2f} km")