import time

import constants as cs
import receptors
import routes
import settings
import constant_coords as ccs
import zones
import weather
from polygons import Polygon
from managers import (MerchantManager, ChinaNavyManager, ChinaAirManager, ChinaSubManager,
                      EscortManagerTW, EscortManagerJP, EscortManagerUS, CoalitionAirManager, CoalitionSubManager)
import data_functions

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
        self.visibility_graph_coalition_air = None
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
        self.merchant_manager = None
        self.tw_manager_escorts = None
        self.jp_manager_escorts = None
        self.us_manager_escorts = None
        self.coalition_manager_air = None
        self.coalition_manager_sub = None
        self.china_manager_air = None
        self.china_manager_navy = None
        self.china_manager_sub = None
        self.all_agents = []
        self.initiate_managers()

    @staticmethod
    def get_land_masses() -> list[Polygon]:
        return ccs.LAND_MASSES

    def initiate_visibility_graphs(self) -> None:
        self.coalition_obstacles = self.landmasses + [self.china_polygon]
        self.visibility_graph_coalition = routes.create_base_graph(self.coalition_obstacles)
        self.visibility_graph_coalition_air = routes.create_base_graph([self.china_polygon] + ccs.OTHER_LAND)

        china_avoid_zones = [landmass for landmass in self.landmasses
                             if landmass != ccs.TAIWAN_LAND and landmass not in ccs.JAPAN_AND_ISLANDS]
        for zone in zones.HUNTER_ILLEGAL_ZONES:
            # china_avoid_zones.append(zone.extended_polygon_copy())
            china_avoid_zones.append(zone.polygon)
            china_avoid_zones.append(ccs.KOREA)

        self.china_air_obstacles = china_avoid_zones
        self.visibility_graph_air_china = routes.create_base_graph(self.china_air_obstacles)
        self.china_water_obstacles = china_avoid_zones + [self.china_polygon]
        self.visibility_graph_water_china = routes.create_base_graph(self.china_water_obstacles)

    def initiate_receptors(self) -> None:
        self.receptor_grid = receptors.ReceptorGrid(self.landmasses, self)

    def initiate_managers(self) -> None:
        self.merchant_manager = MerchantManager()
        self.tw_manager_escorts = EscortManagerTW()
        self.jp_manager_escorts = EscortManagerJP()
        self.us_manager_escorts = EscortManagerUS()
        self.coalition_manager_air = CoalitionAirManager()
        self.coalition_manager_sub = CoalitionSubManager()
        self.china_manager_air = ChinaAirManager()
        self.china_manager_navy = ChinaNavyManager()
        self.china_manager_sub = ChinaSubManager()

        self.managers = [self.merchant_manager,
                         self.us_manager_escorts,
                         self.china_manager_air,
                         self.china_manager_navy,
                         self.china_manager_sub,
                         self.tw_manager_escorts,
                         self.jp_manager_escorts,
                         self.coalition_manager_air,
                         self.coalition_manager_sub,
                         ]

        for manager in self.managers:
            self.all_agents.extend(manager.inactive_agents)

        self.set_ammunition()

    def set_ammunition(self) -> None:
        coalition_air_ammo = data_functions.get_ammo_info("COALITION AIRCRAFT")
        coalition_ship_ammo = data_functions.get_ammo_info("COALITION ESCORT")
        coalition_sub_ammo = data_functions.get_ammo_info("COALITION SUB")

        self.tw_manager_escorts.ammunition = coalition_ship_ammo
        self.jp_manager_escorts.ammunition = coalition_ship_ammo
        self.us_manager_escorts.ammunition = coalition_ship_ammo
        self.coalition_manager_air.ammunition = coalition_air_ammo
        self.coalition_manager_sub.ammunition = coalition_sub_ammo

        self.china_manager_air.ammunition = data_functions.get_ammo_info("CN AIRCRAFT")
        self.china_manager_navy.ammunition = data_functions.get_ammo_info("CN NAVY")
        self.china_manager_sub.ammunition = data_functions.get_ammo_info("CN SUB")

    def update_weather_conditions(self) -> None:
        t_0 = time.time()

        if self.world_time - self.last_weather_update > cs.WEATHER_UPDATE_TIME:
            self.last_weather_update = self.world_time
            weather.update_sea_states(self.receptor_grid)

        tracker.USED_TIME["Weather"] += time.time() - t_0

    def remove_agents_from_illegal_zones(self):
        for manager in self.managers:
            manager.remove_agents_from_illegal_zones()

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
            manager.assign_agents_to_requests()
            manager.continue_other_missions()

        self.receptor_grid.depreciate_pheromones()
        self.world_time += self.time_delta
