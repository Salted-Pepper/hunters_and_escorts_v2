import random
import numpy as np
from scipy.stats import qmc

from points import Point
from polygons import Polygon
import constant_coords as ccs
import copy


def create_poisson_disk_sample(polygon: Polygon, obstacles: list) -> list:
    obstacles.append(ccs.CHINA)
    rng = np.random.default_rng()
    radius = 0.5
    engine = qmc.PoissonDisk(d=2, radius=radius, rng=rng,
                             l_bounds=[polygon.min_x + 0.05, polygon.min_y + 0.05],
                             u_bounds=[polygon.max_x - 0.05, polygon.max_y - 0.05])
    sample = engine.fill_space()
    points = []
    for p in sample:
        point = Point(p[0], p[1])
        if polygon.shrunk.contains(point.shapely) and not any(
                [obstacle.contains_point(point) for obstacle in obstacles]):
            points.append(point)
    return points


zone_id = 0


class Zone:
    def __init__(self, name: str, polygon: Polygon):
        global zone_id
        self.zone_id = zone_id
        zone_id += 1
        self.name = name
        if name in ["C", "E", "G"]:
            self.polygon = polygon
        else:
            self.polygon = ccs.set_points_to_bounds(polygon)

        self.obstacles = [landmass for landmass in (ccs.LAND_MASSES + [ccs.CHINA])
                          if any([self.polygon.contains_point(point) for point in landmass.points])]
        self.patrol_locations = create_poisson_disk_sample(self.polygon, self.obstacles)
        print(f"Zone {self} has {len(self.patrol_locations)} patrol locations.")

    def __str__(self):
        return self.name

    def __eq__(self, other) -> bool:
        if other is None:
            return False

        if self.zone_id == other.zone_id:
            return True
        else:
            return False

    def __hash__(self) -> int:
        return self.zone_id

    def check_if_agent_in_zone(self, agent) -> bool:
        if self.polygon.contains_point(agent.location):
            return True
        else:
            return False

    def extended_polygon_copy(self) -> Polygon:
        extended_polygon = copy.copy(self.polygon)
        extended_polygon.shapely.buffer(0.01)
        extended_polygon.shrunk = extended_polygon.shapely.buffer(-0.005)
        return extended_polygon

    def sample_patrol_location(self):
        return random.choice(self.patrol_locations)

    def clear_patrol_in_zone(self, zone) -> None:
        points_to_remove = []
        for location in self.patrol_locations:
            if zone.polygon.contains_point(location):
                points_to_remove.append(location)

        self.patrol_locations = [p for p in self.patrol_locations if p not in points_to_remove]


# Zones
ZONE_A = Zone(name="A", polygon=Polygon(ccs.A_ALL_ZONES, name="A"))
ZONE_B = Zone(name="B", polygon=Polygon(ccs.B_TAIWAN_CONT, name="B"))
ZONE_C = Zone(name="C", polygon=Polygon(ccs.C_TAIWAN_TERRITORIAL, name="C"))
ZONE_D = Zone(name="D", polygon=Polygon(ccs.D_JAPAN_CONT, name="D"))
ZONE_E = Zone(name="E", polygon=Polygon(ccs.E_JAPAN_TERRITORIAL, name="E"))
ZONE_F = Zone(name="F", polygon=Polygon(ccs.F_FILIPINO_CONT, name="F"))
ZONE_G = Zone(name="G", polygon=Polygon(ccs.G_FILIPINO_TERRITORIAL, name="G"))
ZONE_H = Zone(name="H", polygon=Polygon(ccs.H_OUTSIDE_10_DASH, name="H"))
ZONE_I = Zone(name="I", polygon=Polygon(ccs.I_INSIDE_10_DASH, name="I"))
ZONE_J = Zone(name="J", polygon=Polygon(ccs.J_TAIWAN_FILIPINO, name="J"))
ZONE_K = Zone(name="K", polygon=Polygon(ccs.K_TAIWAN_JAPAN, name="K"))
ZONE_L = Zone(name="L", polygon=Polygon(ccs.L_INSIDE_MEDIAN_LINE, name="L"))
ZONE_N = Zone(name="N", polygon=Polygon(ccs.N_HOLDING_ZONE, name="N"))
ZONE_P = Zone(name="P", polygon=Polygon(ccs.P_PRIMARY_HUNTING_ZONE, name="P"))
ZONE_Q = Zone(name="Q", polygon=Polygon(ccs.Q_SECOND_JAPAN, name="Q"))

# Clear patrol locations in sub-zones for these to prevent Chinese agents from crossing into these zones
ZONE_B.clear_patrol_in_zone(ZONE_C)
ZONE_D.clear_patrol_in_zone(ZONE_E)
ZONE_H.clear_patrol_in_zone(ZONE_C)
ZONE_H.clear_patrol_in_zone(ZONE_E)
ZONE_H.clear_patrol_in_zone(ZONE_G)
ZONE_H.clear_patrol_in_zone(ZONE_Q)
ZONE_I.clear_patrol_in_zone(ZONE_C)
ZONE_F.clear_patrol_in_zone(ZONE_G)
ZONE_F.clear_patrol_in_zone(ZONE_Q)
ZONE_A.clear_patrol_in_zone(ZONE_C)
ZONE_A.clear_patrol_in_zone(ZONE_E)
ZONE_A.clear_patrol_in_zone(ZONE_G)
ZONE_A.clear_patrol_in_zone(ZONE_Q)
ZONE_H.clear_patrol_in_zone(ZONE_B)
ZONE_H.clear_patrol_in_zone(ZONE_C)
ZONE_H.clear_patrol_in_zone(ZONE_D)
ZONE_H.clear_patrol_in_zone(ZONE_E)
ZONE_H.clear_patrol_in_zone(ZONE_F)
ZONE_H.clear_patrol_in_zone(ZONE_G)

# Sort zones from top zones to lower zones and establish overarching zones
ZONES = [ZONE_P, ZONE_K, ZONE_Q, ZONE_J, ZONE_C, ZONE_B, ZONE_E, ZONE_D,
         ZONE_G, ZONE_F, ZONE_I, ZONE_L, ZONE_N, ZONE_H, ZONE_A]
ZONES_DISPLAY_ORDER = [ZONE_A, ZONE_B, ZONE_C, ZONE_D, ZONE_E, ZONE_F, ZONE_G, ZONE_H, ZONE_I, ZONE_L, ZONE_N, ZONE_P]
UNDERLYING_ZONES = [zone for zone in ZONES if zone not in [ZONE_A, ZONE_N, ZONE_Q, ZONE_J, ZONE_K]]
HUNTER_ILLEGAL_ZONES = [ZONE_C, ZONE_E, ZONE_G]
COALITION_ILLEGAL_ZONES = [ccs.CHINA]

NAVY_ILLEGAL_ZONES = ccs.JAPAN_AND_ISLANDS + [ccs.CHINA] + ccs.OTHER_LAND
