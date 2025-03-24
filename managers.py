from __future__ import annotations

from abc import abstractmethod
from multiprocessing import cpu_count
import concurrent.futures
import numpy as np
import random

import settings
from missions import Travel, Attack, Track, Observe, Guard, Return, Holding, Depart
from bases import Base
from zones import Zone
from points import Point
import constants as cs
import data_functions

from ships import Merchant, ChineseShip


class Manager:
    def __init__(self):
        self.team = None
        self.name = None
        self.active_agents = []
        self.inactive_agents = []
        self.destroyed_agents = []

        self.requests = []

        self.bases = []
        self.initiate_bases()

        self.utilisation_rate = None

    def __str__(self):
        return self.name

    @abstractmethod
    def pre_turn_actions(self) -> None:
        self.set_agent_movement()

    def set_agent_movement(self) -> None:
        for agent in self.active_agents:
            agent.set_turn_movement()

    @abstractmethod
    def initiate_agents(self) -> None:
        raise NotImplementedError("Initiate Agents not defined on MANAGER Level")

    @abstractmethod
    def initiate_bases(self) -> None:
        raise NotImplementedError("Initiate Bases not defined on MANAGER Level")

    @abstractmethod
    def calc_utilization_rate(self) -> float:
        pass

    def agent_was_destroyed(self, agent) -> None:
        self.active_agents.remove(agent)
        self.destroyed_agents.append(agent)

    @abstractmethod
    def assign_agents_to_tasks(self) -> None:
        pass

    @abstractmethod
    def activate_agent(self, agents: list) -> None:
        pass

    def complete_base_activities(self) -> None:
        for base in self.bases:
            base.serve_agents()

    def check_if_agents_have_to_return(self) -> None:
        relevant_agents = [agent for agent in self.active_agents if not isinstance(agent.mission, Return)]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(agent.can_continue) for agent in relevant_agents]
            concurrent.futures.wait(futures)

    def have_agents_observe(self) -> None:
        observing_agents = [agent for agent in self.active_agents if isinstance(agent.mission, Observe)]

        # TODO: Handle exception for boarded Merchants that might remain under merchant Manager
        #  (or put under separate manager?)
        agents_to_detect = [agent
                            for manager in cs.world.managers if manager.team != self.team
                            for agent in manager.active_agents]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(agent.mission.execute, agents_to_detect) for agent in observing_agents]
            concurrent.futures.wait(futures)

    def continue_other_missions(self) -> None:
        other_agents = [agent for agent in self.active_agents
                        if not isinstance(agent.mission, Observe)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=cpu_count() - 1) as executor:
            futures = [executor.submit(agent.mission.execute) for agent in other_agents]
            concurrent.futures.wait(futures)

        # [agent.mission.execute() for agent in other_agents]

    def sample_random_base(self) -> Base:
        return random.choices(self.bases, weights=[base.agent_share
                                                   if base.agent_share is not None
                                                   else 1 / len(self.bases)
                                                   for base in self.bases])[0]

    @abstractmethod
    def select_zone_to_patrol(self, agent) -> None:
        pass


class EscortManager(Manager):
    def __init__(self):
        super().__init__()
        self.team = 1

    def pre_turn_actions(self) -> None:
        for agent in self.active_agents:
            agent.set_turn_movement()

    def initiate_agents(self) -> None:
        pass

    def initiate_bases(self) -> None:
        self.bases = [Base(name="Kaohsiung", location=Point(120.30, 22.50), agent_share=0.25),
                      Base(name="Tiachung", location=Point(120.35, 24.30), agent_share=0.25),
                      Base(name="Keelung", location=Point(121.73, 25.19), agent_share=0.25),
                      Base(name="Hualien", location=Point(121.65, 24.00), agent_share=0.25),
                      ]

    def calc_utilization_rate(self) -> float:
        pass

    def assign_agents_to_tasks(self) -> None:
        pass

    def activate_agent(self, agents: list) -> None:
        pass

    def select_zone_to_patrol(self, agent) -> None:
        pass


class MerchantManager(Manager):
    def __init__(self):
        super().__init__()
        self.name = "Merchant Manager"
        self.team = 1

    def __str__(self):
        return self.name

    def pre_turn_actions(self) -> None:
        self.generate_incoming_merchants()
        self.set_agent_movement()

    def generate_incoming_merchants(self) -> None:
        for merchant_type in settings.MERCHANT_INFO:
            attributes = settings.MERCHANT_INFO[merchant_type]
            weekly_arrivals = attributes["arrivals"]
            sample_arrivals = self.sample_arrivals(weekly_arrivals)
            self.generate_merchants(merchant_type, sample_arrivals)

    @staticmethod
    def sample_arrivals(weekly_arrivals: int) -> int:
        per_period_arrivals = weekly_arrivals / ((24 * 7) / cs.world.time_delta)
        sampled_arrivals = np.random.poisson(per_period_arrivals)
        return sampled_arrivals

    def generate_merchants(self, merchant_type: str, number: int):
        for _ in range(number):
            new_merchant = Merchant(self, model=merchant_type, base=self.sample_random_base())
            self.active_agents.append(new_merchant)
            cs.world.all_agents.append(new_merchant)

    def initiate_agents(self) -> None:
        """
        Merchant Manager generates agents instead of having a fixed set of agents
        :return:
        """
        pass

    def initiate_bases(self) -> None:
        self.bases = [Base(name="Kaohsiung", location=Point(120.30, 22.50), agent_share=0.4),
                      Base(name="Tiachung", location=Point(120.35, 24.30), agent_share=0.3),
                      Base(name="Keelung", location=Point(121.73, 25.19), agent_share=0.25),
                      Base(name="Hualien", location=Point(121.65, 24.00), agent_share=0.05),
                      ]

    def calc_utilization_rate(self) -> float:
        """
        Merchant Manager does not send agents based on utilisation rate, but instead at a poission rate.
        :return:
        """
        pass

    def assign_agents_to_tasks(self) -> None:
        pass

    def activate_agent(self, agents: list) -> None:
        pass

    def select_zone_to_patrol(self, agent) -> Zone:
        pass


class ChinaNavyManager(Manager):
    def __init__(self):
        super().__init__()
        self.name = "China Navy Manager"
        self.team = 2
        self.initiate_agents()

    def initiate_agents(self) -> None:
        cn_navy_data = data_functions.get_chinese_navy_data()
        for model in cn_navy_data:
            quantity = int(cn_navy_data[model]["numberofagents"])
            for _ in range(quantity):
                new_ship = ChineseShip(manager=self, model=model, base=self.sample_random_base())
                self.inactive_agents.append(new_ship)

    def initiate_bases(self) -> None:
        self.bases = [Base(name="Shanghai", location=Point(122.747, 31.306), agent_share=0.25),
                      Base(name="Taizhou", location=Point(122.037, 28.231), agent_share=0.25),
                      Base(name="Quanzhou", location=Point(119.039, 24.684), agent_share=0.25),
                      Base(name="Fuzhou", location=Point(119.994, 26.061), agent_share=0.25),
                      ]

    def pre_turn_actions(self) -> None:
        for agent in self.active_agents:
            agent.set_turn_movement()

        utilisation = self.get_current_utilisation()
        eligible_agents = [agent for agent in self.inactive_agents if agent.remaining_maintenance_time == 0]

        while utilisation < self.calc_utilization_rate() and len(eligible_agents) > 0:
            self.activate_agent(eligible_agents)

            utilisation = self.get_current_utilisation()
            eligible_agents = [agent for agent in self.inactive_agents if agent.remaining_maintenance_time == 0]

    def get_current_utilisation(self) -> float:
        if len(self.active_agents) > 0:
            utilisation = len(self.active_agents) / (len(self.active_agents) + len(self.inactive_agents))
        else:
            utilisation = 0
        return utilisation

    def calc_utilization_rate(self) -> float:
        # TODO: Calculate Utilisation rate properly
        return 0.4

    def assign_agents_to_tasks(self) -> None:
        pass

    def activate_agent(self, agents: list) -> None:
        agent = random.choice(agents)
        zone = self.select_zone_to_patrol(agent)

        if zone is None:
            return

        agent.activate()
        agent.go_to_patrol(zone)

    def select_zone_to_patrol(self, agent) -> Zone | None:
        set_assignment = settings.zone_assignment_hunter[agent.service]
        zones = list(set_assignment.keys())
        share = list(set_assignment.values())
        if sum(share) == 0:
            return None
        selected_zone = random.choices(zones, share)[0]
        return selected_zone

