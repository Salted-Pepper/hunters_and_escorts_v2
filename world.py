import time

import constants as cs
import receptors
import routes
import settings
import constant_coords as ccs
import zones
import weather
from polygons import Polygon
from managers import (MerchantManager, ChinaNavyManager, ChinaAirManager,
                      EscortManagerTW, EscortManagerJP, EscortManagerUS)

import tracker


class World:
    def __init__(self):
        cs.world = self

        # Time Management
        self.time_delta = settings.time_delta

        self.world_time = 0
        self.last_weather_update = 0

        # Geography
        self.landmasses = self.get_land_masses()
        self.china_polygon = ccs.CHINA
        self.coalition_obstacles = None
        self.visibility_graph_coalition = None
        self.china_air_obstacles = None
        self.visibility_graph_air_china = None
        self.china_water_obstacles = None
        self.visibility_graph_water_china = None
        self.zones = zones.ZONES
        self.initiate_visibility_graphs()

        # Receptor Set Up
        self.receptor_grid = None
        self.initiate_receptors()

        # Managers
        self.managers = []
        self.all_agents = []
        self.initiate_managers()

    @staticmethod
    def get_land_masses() -> list[Polygon]:
        return ccs.LAND_MASSES

    def initiate_visibility_graphs(self) -> None:
        self.coalition_obstacles = self.landmasses + [self.china_polygon]
        self.visibility_graph_coalition = routes.create_base_graph(self.coalition_obstacles)

        china_avoid_zones = [landmass for landmass in self.landmasses
                             if landmass != ccs.TAIWAN_LAND and landmass not in ccs.JAPAN_AND_ISLANDS]
        china_avoid_zones.append(zones.ZONE_C.polygon)
        china_avoid_zones.append(zones.ZONE_E.polygon)
        self.china_air_obstacles = china_avoid_zones
        self.visibility_graph_air_china = routes.create_base_graph(self.china_air_obstacles)
        self.china_water_obstacles = china_avoid_zones + [self.china_polygon]
        self.visibility_graph_water_china = routes.create_base_graph(self.china_water_obstacles)

    def initiate_receptors(self) -> None:
        self.receptor_grid = receptors.ReceptorGrid(self.landmasses, self)

    def initiate_managers(self) -> None:
        self.managers = [MerchantManager(),
                         ChinaNavyManager(),
                         ChinaAirManager(),
                         EscortManagerTW(),
                         EscortManagerJP(),
                         EscortManagerUS(),
                         ]

        for manager in self.managers:
            self.all_agents.extend(manager.inactive_agents)

    def update_weather_conditions(self) -> None:
        t_0 = time.time()

        if self.world_time - self.last_weather_update > cs.WEATHER_UPDATE_TIME:
            self.last_weather_update = self.world_time
            weather.update_sea_states(self.receptor_grid)

        tracker.USED_TIME["Weather"] += time.time() - t_0

    def simulate_step(self) -> None:

        self.update_weather_conditions()
        if self.world_time % 24 == 0:
            print(f"\nTime is {self.world_time}")
            tracker.display_times()

        for manager in self.managers:
            manager.complete_base_activities()
            manager.pre_turn_actions()
            manager.check_if_agents_have_to_return()
            manager.have_agents_observe()
            manager.assign_agents_to_tasks()
            manager.continue_other_missions()

        self.receptor_grid.depreciate_pheromones()
        self.world_time += self.time_delta
