import shapely
import random

from points import Point


class Polygon:
    def __init__(self, points: list[Point], name=None, color=None):
        self.name = name
        self.color = color
        self.points = points
        self.coords = [p for point in points for p in point.get_tuple()]  # Coords in JS notation
        self.shapely = shapely.Polygon([p.get_tuple() for p in self.points])
        self.shrunk = self.shapely.buffer(-0.01)

        self.min_x = None
        self.max_x = None
        self.min_y = None
        self.max_y = None
        self.calculate_bounds()

    def __repr__(self) -> str:
        return f"Polygon {self.name} at {str(self.points)}"

    def __str__(self) -> str:
        if self.name is None:
            return f"Unnamed polygon at {self.points}"
        else:
            return self.name

    def output_dict(self):
        return {"name": self.name,
                "color": self.color,
                "coords": self.coords}

    def contains_point(self, point: Point) -> bool:
        if self.shapely.contains(point.shapely):
            return True
        else:
            return False

    def calculate_bounds(self):
        """
        Calculates the min/max of lon and lat of the polygon for sampling
        :return:
        """
        min_x = 360
        max_x = 0
        min_y = 360
        max_y = 0
        for point in self.points:
            if point.x < min_x:
                min_x = point.x
            if point.x > max_x:
                max_x = point.x
            if point.y < min_y:
                min_y = point.y
            if point.y > max_y:
                max_y = point.y

        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

    def get_sample_point(self) -> Point:
        # TODO: Improve this selection by updating the polygons
        while True:
            p = Point(x=random.uniform(self.min_x, self.max_x), y=random.uniform(self.min_y, min(40, self.max_y)))
            if self.contains_point(p):
                return p
