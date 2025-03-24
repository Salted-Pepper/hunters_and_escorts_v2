import constants as cs
import receptors
import routes
import settings
import constant_coords as ccs
import zones
import weather
from polygons import Polygon
from agents import Agent
from managers import MerchantManager, ChinaNavyManager


class World:
    def __init__(self):
        cs.world = self

        # Time Management
        self.time_delta = settings.time_delta

        self.world_time = 0
        self.last_weather_update = 0

        # Geography
        self.landmasses = self.get_land_masses()
        self.visibility_graph = routes.create_base_graph(self.landmasses)
        self.zones = zones.ZONES

        # Receptor Set Up
        self.receptor_grid = None
        self.initiate_receptors()

        # Managers
        # TODO: Add Updated Managers
        self.managers = []
        self.all_agents = []
        self.initiate_managers()

    @staticmethod
    def get_land_masses() -> list[Polygon]:
        return ccs.TAIWAN_AND_ISLANDS + ccs.JAPAN_AND_ISLANDS + ccs.OTHER_LAND

    def initiate_receptors(self) -> None:
        self.receptor_grid = receptors.ReceptorGrid(self.landmasses, self)

    def initiate_managers(self) -> None:
        # TODO: Make this managers and append agents for each manager
        self.managers = [MerchantManager(),
                         ChinaNavyManager()]

        for manager in self.managers:
            self.all_agents.extend(manager.inactive_agents)

    def update_weather_conditions(self) -> None:
        if self.world_time - self.last_weather_update > cs.WEATHER_UPDATE_TIME:
            self.last_weather_update = self.world_time
            weather.update_sea_states(self.receptor_grid)

    def simulate_step(self) -> None:
        self.world_time += self.time_delta

        print(f"Time is {self.world_time}")

        self.update_weather_conditions()

        for manager in self.managers:
            manager.complete_base_activities()
            manager.pre_turn_actions()
            manager.check_if_agents_have_to_return()
            manager.have_agents_observe()
            manager.assign_agents_to_tasks()
            manager.continue_other_missions()

        self.receptor_grid.depreciate_pheromones()
