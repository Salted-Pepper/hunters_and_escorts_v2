import shapely

import general_maths as gm

unique_point_id = 0


class Point:
    def __init__(self, x: float, y: float):
        global unique_point_id
        self.point_id = unique_point_id
        unique_point_id += 1

        self.shapely = shapely.Point(x, y)
        self.x = x
        self.y = y

    def get_tuple(self) -> tuple:
        return self.x, self.y

    def __str__(self):
        return f"({self.x:0.2f}, {self.y:0.2f})"

    def __repr__(self):
        return f"Point at ({self.x}, {self.y})"

    def __eq__(self, other) -> bool:
        if self.x == other.x and self.y == other.y:
            return True
        else:
            return False

    def __hash__(self) -> int:
        return self.point_id

    def distance_to_point(self, other) -> float:
        return gm.calculate_distance(self, other)
