import settings

from polygons import Polygon
import constant_coords as ccs


class Zone:
    def __init__(self, name: str, polygon: Polygon):
        self.name = name
        self.polygon = polygon
        self.obstacles = [landmass for landmass in (ccs.LAND_MASSES + [ccs.CHINA])
                          if any([self.polygon.contains_point(point) for point in landmass.points])]

    def __str__(self):
        return self.name

    def check_if_agent_in_zone(self, agent) -> bool:
        return self.polygon.contains_point(agent.location)

    def sample_patrol_location(self):

        attempts = 0
        valid_point = False

        while not valid_point:
            attempts += 1
            if attempts >= settings.ITERATION_LIMIT:
                raise TimeoutError(f"Unable to sample patrol location in {self.name} - "
                                   f"{[obs.name for obs in self.obstacles]}")
            sample_point = self.polygon.get_sample_point()
            # TODO: Update this check by only checking the zones IN the obstacles
            #  (create obstacles reference in Zone object?)
            if not any([obstacle.contains_point(sample_point) for obstacle in self.obstacles]):
                return sample_point


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
ZONE_L = Zone(name="L", polygon=Polygon(ccs.L_INSIDE_MEDIAN_LINE, name="L"))
ZONE_N = Zone(name="N", polygon=Polygon(ccs.N_HOLDING_ZONE, name="N"))
ZONE_P = Zone(name="P", polygon=Polygon(ccs.P_PRIMARY_HUNTING_ZONE, name="P"))

# Sort zones from top zones to lower zones and establish overarching zones
ZONES = [ZONE_P, ZONE_C, ZONE_B, ZONE_E, ZONE_D, ZONE_G, ZONE_F, ZONE_I, ZONE_L, ZONE_N, ZONE_H, ZONE_A]
ZONES_DISPLAY_ORDER = [ZONE_A, ZONE_B, ZONE_C, ZONE_D, ZONE_E, ZONE_F, ZONE_G, ZONE_H, ZONE_I, ZONE_L, ZONE_N, ZONE_P]
HUNTER_ILLEGAL_ZONES = ccs.JAPAN_AND_ISLANDS + [ZONE_B.polygon, ZONE_C.polygon]
COALITION_ILLEGAL_ZONES = [ccs.CHINA]

NAVY_ILLEGAL_ZONES = ccs.JAPAN_AND_ISLANDS + [ccs.CHINA] + ccs.OTHER_LAND
