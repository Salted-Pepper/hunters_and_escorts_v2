from __future__ import annotations

from abc import abstractmethod
from multiprocessing import cpu_count
import concurrent.futures
import numpy as np
import random

import settings
import missions
from bases import Base
import zones
from points import Point
import constants as cs
import data_functions

from ships import Merchant, ChineseShip, Escort


class Request:
    def __init__(self, target, mission, action_time: float):
        self.target = target
        self.mission = mission
        self.action_time = action_time


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

        self.agents_to_detect = []

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

    def check_if_can_take_task(self, target, mission, holding_only=False) -> bool:
        zone = target.get_current_zone()

        if holding_only:
            agents_in_holding = [a for a in self.active_agents
                                 if a.mission.mission_type == "hold"
                                 and a.allowed_to_enter_zone(zone)]
            if len(agents_in_holding) > 0:
                self.add_task(target, mission)
                return True
            else:
                return False

        for agent in self.active_agents + self.inactive_agents:
            if (agent.mission.mission_type != "return"
                    and agent.remaining_maintenance_time == 0
                    and agent.allowed_to_enter_zone(zone)):
                self.add_task(target, mission)
                return True
        return False

    def add_task(self, target, mission) -> None:
        self.requests.append(Request(target=target,
                                     mission=mission,
                                     action_time=cs.world.world_time + settings.COMMUNICATION_DELAY))

    def assign_agents_to_requests(self) -> None:
        while len(self.requests) > 0 and self.requests[0].action_time <= cs.world.world_time:
            request = self.requests.pop(0)
            zone = request.target.get_current_zone()

            successful = self.select_agent_for_request(request, zone)
            if not successful:
                self.requests.insert(0, request)
                return

    def select_agent_for_request(self, request, zone) -> bool:
        # Try assigning an agent in holding
        for agent in self.active_agents:
            if agent.mission.mission_type != "hold":
                continue
            elif not agent.check_if_valid_target(request.target):
                continue
            elif not agent.reach_and_return(request.target.location):
                continue
            else:
                agent.mission.complete()
                missions.Track(agent, request.target)
                return True

        # Otherwise assign any ready inactive agent
        for agent in self.inactive_agents:
            if agent.remaining_maintenance_time > 0:
                continue
            elif not agent.check_if_valid_target(request.target):
                continue
            elif not agent.reach_and_return(request.target.location):
                continue
            else:
                agent.activate()
                missions.Track(agent, request.target)
                return True
        return False

    @abstractmethod
    def activate_agent(self, agents: list) -> None:
        pass

    def complete_base_activities(self) -> None:
        for base in self.bases:
            base.serve_agents()

    def check_if_agents_have_to_return(self) -> None:
        relevant_agents = [agent for agent in self.active_agents if not isinstance(agent.mission, missions.Return)]

        if settings.MULTITHREAD:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(agent.can_continue) for agent in relevant_agents]
                concurrent.futures.wait(futures)
        else:
            [agent.can_continue() for agent in relevant_agents]

    def have_agents_observe(self) -> None:
        observing_agents = [agent for agent in self.active_agents if isinstance(agent.mission, missions.Observe)]

        if len(observing_agents) == 0:
            return
        self.agents_to_detect = [agent
                                 for manager in cs.world.managers if (manager.team != self.team and manager.team != 3)
                                 for agent in manager.active_agents]

        self.agents_to_detect.extend(agent for agent in cs.world.merchant_manager.active_agents
                                     if agent.team != self.team)

        if settings.MULTITHREAD:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(agent.mission.execute, self.agents_to_detect) for agent in observing_agents]
                concurrent.futures.wait(futures)
        else:
            [agent.mission.execute(self.agents_to_detect) for agent in observing_agents]

    def continue_other_missions(self) -> None:
        """
        Other missions can't be multithreaded as mission outcome can affect other agent behaviour
        :return:
        """
        other_agents = [agent for agent in self.active_agents
                        if not isinstance(agent.mission, missions.Observe)]

        [agent.mission.execute() for agent in other_agents]

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
        self.country = None

    def __str__(self):
        return "Escort Manager"

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

    def initiate_agents(self) -> None:
        coalition_data = data_functions.get_coalition_data()
        for model in coalition_data:
            if coalition_data[model]["base"] != self.country:
                continue

            quantity = int(coalition_data[model]["numberofagents"])
            for _ in range(quantity):
                new_ship = Escort(manager=self, model=model, base=self.sample_random_base(), country=self.country)
                self.inactive_agents.append(new_ship)

    @abstractmethod
    def initiate_bases(self) -> None:
        pass

    def calc_utilization_rate(self) -> float:
        # TODO: Calculate Utilisation rate properly
        return 0.02

    def activate_agent(self, agents: list) -> None:
        agent = random.choice(agents)
        zone = self.select_zone_to_patrol(agent)

        if zone is None:
            return

        agent.activate()
        agent.go_to_patrol(zone)

    def select_zone_to_patrol(self, agent) -> zones.Zone | None:
        set_assignment = settings.zone_assignment_coalition[agent.service]
        potential_zones = list(set_assignment.keys())
        share = list(set_assignment.values())
        if sum(share) == 0:
            return None
        selected_zone = random.choices(potential_zones, share)[0]
        return selected_zone


class EscortManagerTW(EscortManager):
    def __init__(self):
        super().__init__()
        self.country = settings.TAIWAN
        self.initiate_agents()

    def __str__(self):
        return "TW Escort Manager"

    def initiate_bases(self) -> None:
        self.bases = [Base(name="Kaohsiung", location=Point(120.30, 22.50), agent_share=0.25),
                      Base(name="Tiachung", location=Point(120.35, 24.30), agent_share=0.25),
                      Base(name="Keelung", location=Point(121.73, 25.19), agent_share=0.25),
                      Base(name="Hualien", location=Point(121.65, 24.00), agent_share=0.25),
                      ]


class EscortManagerJP(EscortManager):
    def __init__(self):
        super().__init__()
        self.country = settings.JAPAN
        self.initiate_agents()

    def __str__(self):
        return "JP Escort Manager"

    def initiate_bases(self) -> None:
        self.bases = [Base(name="Okinawa", location=Point(127.737, 26.588), agent_share=1)]


class EscortManagerUS(EscortManager):
    def __init__(self):
        super().__init__()
        self.country = settings.USA
        self.initiate_agents()

    def __str__(self):
        return "US Escort Manager"

    def initiate_bases(self) -> None:
        self.bases = [Base(name="Yokosuka", location=Point(137.307, 34.2), agent_share=1)]


class MerchantManager(Manager):
    def __init__(self):
        super().__init__()
        self.name = "Merchant Manager"
        self.team = 3

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
            new_merchant = Merchant(self, model=merchant_type,
                                    base=self.sample_random_base(), country=self.sample_country())
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

    def activate_agent(self, agents: list) -> None:
        pass

    def select_zone_to_patrol(self, agent) -> zones.Zone:
        pass

    @staticmethod
    def sample_country() -> str:
        values = list(settings.merchant_country_distribution.keys())
        probabilities = list(settings.merchant_country_distribution.values())
        return random.choices(values, probabilities)[0]


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
        self.bases = [Base(name="Shanghai", location=Point(122.70, 31.306), agent_share=0.25),
                      Base(name="Taizhou", location=Point(122.03, 28.231), agent_share=0.25),
                      Base(name="Quanzhou", location=Point(119.04, 24.684), agent_share=0.25),
                      Base(name="Fuzhou", location=Point(119.99, 26.061), agent_share=0.25),
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
        return 0.02

    def activate_agent(self, agents: list) -> None:
        agent = random.choice(agents)
        zone = self.select_zone_to_patrol(agent)

        if zone is None:
            return

        agent.activate()
        agent.go_to_patrol(zone)

    def select_zone_to_patrol(self, agent) -> zones.Zone | None:
        set_assignment = settings.zone_assignment_hunter[agent.service]
        zones = list(set_assignment.keys())
        share = list(set_assignment.values())
        if sum(share) == 0:
            return None
        selected_zone = random.choices(zones, share)[0]
        return selected_zone


class ChinaAirManager(Manager):
    def __init__(self):
        super().__init__()

    def pre_turn_actions(self) -> None:
        pass

    def initiate_agents(self) -> None:
        pass

    def initiate_bases(self) -> None:
        self.bases = [Base(name="Ningbo", location=Point(121.57, 29.92), icon="AirportRed", agent_share=0.33),
                      Base(name="Fuzhou", location=Point(119.31, 26.00), icon="AirportRed", agent_share=0.34),
                      Base(name="Liangcheng", location=Point(116.75, 25.68), icon="AirportRed", agent_share=0.33)]

    def calc_utilization_rate(self) -> float:
        pass

    def activate_agent(self, agents: list) -> None:
        pass

    def select_zone_to_patrol(self, agent) -> None:
        pass
