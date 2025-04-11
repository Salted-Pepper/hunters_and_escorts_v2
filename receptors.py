# import datetime
# import logging
# import os
import math
import numpy as np

import constants as cs
import general_maths as gm
from points import Point
from polygons import Polygon

# date = datetime.date.today()
# logging.basicConfig(level=logging.DEBUG, filename=os.path.join(os.getcwd(),
#                     'logs/receptor_log_' + str(date) + '.log'),
#                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
# logger = logging.getLogger("RECEPTORS")
# logger.setLevel(logging.DEBUG)


class Receptor:
    def __init__(self, point: Point, in_polygon=False):
        self.location = point
        self.visible = True

        self.coalition_pheromones = None
        self.china_pheromones = None
        self.decay = None
        self.set_pheromone_settings(in_polygon)
        
        # Sea State Variables
        self.sea_state = 2
        self.last_uniform_value = 0.5  # Ensure history is defined by mean value
        self.new_uniform_value = 0.5

    def set_pheromone_settings(self, in_polygon: bool):
        if in_polygon:
            self.coalition_pheromones = 100
            self.china_pheromones = 100
            self.decay = False
        elif not is_in_area_of_interest(self.location):
            self.coalition_pheromones = 100
            self.china_pheromones = 100
            self.decay = False
        else:
            self.coalition_pheromones = 0
            self.china_pheromones = 0
            self.decay = True
            
    def __repr__(self):
        return (f"Receptor at: {self.location} - with alpha: {self.coalition_pheromones}, "
                f"beta: {self.china_pheromones}, sea state: {self.sea_state}")
    
    def in_range_of_point(self, point: Point, radius: float) -> bool:
        if point.distance_to_point(self.location) <= radius:
            return True
        else:
            return False
        

def is_in_area_of_interest(point: Point) -> bool:
    if cs.MIN_LAT <= point.x <= cs.MAX_LAT and cs.MIN_LONG <= point.y <= cs.MAX_LONG:
        return True
    else:
        return False
    

class ReceptorGrid:
    def __init__(self, polygons: list[Polygon], world):
        self.world = world
        self.polygons = polygons
        
        self.receptors = []
        self.max_cols = None
        self.max_rows = None
        
        self.initiate_grid()
        
    def initiate_grid(self) -> None:
        """
        Creates all receptors in the grid given the settings.
        Initiates the pheromone values (0 for empty, inf for in polygon)
        """
        # Add a frame around the AoI, to ensure UAVs don't just hover the edge
        min_lat = cs.MIN_LAT - cs.LAT_GRID_EXTRA
        max_lat = cs.MAX_LAT + cs.LAT_GRID_EXTRA

        min_lon = cs.MIN_LONG - cs.LONG_GRID_EXTRA
        max_lon = cs.MAX_LONG + cs.LONG_GRID_EXTRA

        num_cols = (max_lon - min_lon) // cs.GRID_WIDTH
        num_rows = (max_lat - min_lat) // cs.GRID_HEIGHT

        self.max_cols = int(np.ceil(num_cols))
        self.max_rows = int(np.ceil(num_rows))

        for row in range(self.max_rows):
            for col in range(self.max_cols):
                x_location = min_lat + row * cs.GRID_HEIGHT
                y_location = min_lon + col * cs.GRID_WIDTH

                point = Point(x_location, y_location)

                in_polygon = gm.check_if_point_in_polygons(point, self.polygons)
                self.receptors.append(Receptor(point, in_polygon=in_polygon))

    def get_receptor_at_location(self, point: Point) -> Receptor | None:
        min_lat = cs.MIN_LAT - cs.LAT_GRID_EXTRA
        max_lat = cs.MAX_LAT + cs.LAT_GRID_EXTRA

        min_lon = cs.MIN_LONG - cs.LONG_GRID_EXTRA
        max_lon = cs.MAX_LONG + cs.LONG_GRID_EXTRA

        if max_lat < point.x or point.x < min_lat or max_lon < point.y or point.y < min_lon:
            raise ValueError(f"Illegal location - {point}")

        row = int((point.x - min_lat) / cs.GRID_HEIGHT)
        col = int((point.y - min_lon) / cs.GRID_WIDTH)
        index = row * self.max_cols + col

        return self.receptors[index]

    def select_receptors_in_radius(self, point: Point, radius: float) -> list:
        """
        Select all the receptors within a radius of a point.
        Prevents having to cycle through all points by using how the list of receptors was created
        :param point: Point object
        :param radius: Radius around the point
        :return:
        """
        # Adjust radius to an upperbound of the coordinate transformation
        lon_lat_radius = max(radius / 100, cs.GRID_WIDTH / 2)
        # only check receptors in the rectangle of size radius - select receptors in the list based on
        # how the list is constructed.
        x, y = point.x, point.y
        min_x = x - lon_lat_radius
        max_x = x + lon_lat_radius
        min_y = y - lon_lat_radius
        max_y = y + lon_lat_radius

        # see in which rows and columns this rectangle is:
        min_row = int(max(np.floor((min_x - (cs.MIN_LAT - cs.LAT_GRID_EXTRA))
                                   / cs.GRID_HEIGHT), 0))
        max_row = int(min(np.ceil((max_x - (cs.MIN_LAT - cs.LAT_GRID_EXTRA))
                                  / cs.GRID_HEIGHT), self.max_rows))

        min_col = int(max(np.floor((min_y - (cs.MIN_LONG - cs.LONG_GRID_EXTRA))
                                   / cs.GRID_WIDTH), 0))
        max_col = int(min(np.ceil((max_y - (cs.MIN_LONG - cs.LONG_GRID_EXTRA))
                                  / cs.GRID_WIDTH), self.max_cols))

        receptors_in_radius = []
        for row_index in range(min_row, max_row):
            for col_index in range(min_col, max_col):
                index = self.max_cols * row_index + col_index
                r = self.receptors[index]

                if r.in_range_of_point(point, radius * cs.RECEPTOR_RADIUS_MULTIPLIER):
                    receptors_in_radius.append(r)
        return receptors_in_radius

    def calculate_cop(self, point: Point, radius: float, pheromone_type: str) -> (float, list):
        """
        Calculates the concentration of pheromones (c_o_p)
        :param point:
        :param radius:
        :param pheromone_type: Type of pheromone (Taiwan is alpha pheromones, China is beta pheromones)
        :return:
        """
        # Increase radius of receptors selected by a factor 2 to make more future-proof decisions
        receptors = self.select_receptors_in_radius(point, radius * 2)

        if not is_in_area_of_interest(point):
            return math.inf, receptors

        for polygon in self.polygons:
            if polygon.contains_point(point):
                return math.inf, receptors

        c_o_p = 0
        if pheromone_type == "coalition":
            for receptor in receptors:
                c_o_p += (1 / max(0.1, point.distance_to_point(receptor.location))) * receptor.coalition_pheromones
        elif pheromone_type == "china":
            for receptor in receptors:
                c_o_p += (1 / max(0.1, point.distance_to_point(receptor.location))) * receptor.china_pheromones
        # logger.debug(f"Calculated c_o_p at {point} with rad {radius}: {c_o_p} - from {len(receptors)} receptors.")
        return c_o_p, receptors

    def depreciate_pheromones(self):
        for receptor in self.receptors:
            if receptor.decay:
                receptor.coalition_pheromones = (receptor.coalition_pheromones * cs.DEPRECIATION_PER_TIME_DELTA
                                                 ** (1 / self.world.time_delta))
                receptor.china_pheromones = (receptor.china_pheromones * cs.DEPRECIATION_PER_TIME_DELTA
                                             ** (1 / self.world.time_delta))

