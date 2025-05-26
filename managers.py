from __future__ import annotations

from abc import abstractmethod
from multiprocessing import cpu_count
import concurrent.futures
import numpy as np
import random

import datetime
import logging
import os

import settings
import missions
from bases import Base
import zones
from points import Point
import constants as cs
import data_functions

from ships import Merchant, ChineseShip, Escort
from aircraft import ChineseAircraft, CoalitionAircraft
from submarines import ChineseSub, CoalitionSub

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename=os.path.join(os.getcwd(), 'logs/mission_log_' + str(date) + '.log'),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("MANAGERS")
logger.setLevel(logging.DEBUG)


class Request:
    def __init__(self, target, mission, action_time: float):
        self.target = target
        self.mission = mission
        self.action_time = action_time

    def __str__(self):
        return f"Request {self.mission} - {self.target}"


class Manager:
    def __init__(self):
        self.team = None
        self.name = None
        self.active_agents = []
        self.inactive_agents = []
        self.destroyed_agents = []
        self.reserved_agents = []

        self.requests = []

        self.bases = []
        self.initiate_bases()

        self.utilisation_rate = None

        self.ammunition = []
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

    def get_current_utilisation(self) -> float:
        if len(self.active_agents) > 0:
            utilisation = len(self.active_agents) / (len(self.active_agents) + len(self.inactive_agents))
        else:
            utilisation = 0
        return utilisation

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
                                 if a.mission is not None and a.mission.mission_type == "hold"
                                 and a.allowed_to_enter_zone(zone)]
            if len(agents_in_holding) > 0:
                self.add_task(target, mission)
                return True
            else:
                return False

        for agent in self.active_agents + self.inactive_agents:
            if ((agent.mission is None or agent.mission.mission_type != "return")
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

            if request.target.destroyed:
                return

            # Filter out edge case of ship being boarded in meantime
            if request.target.team == self.team:
                return

            successful = self.select_agent_for_request(request)
            if not successful:
                self.requests.insert(0, request)
                return

    def select_agent_for_request(self, request) -> bool:
        # Try assigning an agent in holding
        for agent in self.active_agents:
            if agent.mission is None:
                logger.warning(f"Fount active agent with mission none: {agent} - previously: {agent.previous_mission}")
                continue
            if agent.mission.mission_type != "hold":
                continue
            elif not agent.check_if_valid_target(request.target):
                continue
            elif not agent.reach_and_return(request.target.location):
                continue
            elif not agent.able_to_attack(request.target):
                continue
            else:
                agent.mission.complete()
                missions.Track(agent, request.target)
                print(f"Sending {agent} to {request}")
                return True

        # Otherwise assign any ready inactive agent
        for agent in self.inactive_agents:
            if agent.remaining_maintenance_time > 0:
                continue
            elif not agent.check_if_valid_target(request.target):
                continue
            elif not agent.reach_and_return(request.target.location):
                continue
            elif not agent.able_to_attack(request.target):
                continue
            else:
                agent.activate()
                agent.assigned_zone = request.target.get_current_zone()
                missions.Track(agent, request.target)
                logger.debug(f"Sending {agent} to {request}")
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
            with concurrent.futures.ThreadPoolExecutor(max_workers=cpu_count() - 1) as executor:
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
            with concurrent.futures.ThreadPoolExecutor(max_workers=cpu_count() - 1) as executor:
                futures = [executor.submit(agent.mission.execute) for agent in observing_agents]
                concurrent.futures.wait(futures)
        else:
            [agent.mission.execute() for agent in observing_agents]

    def continue_other_missions(self) -> None:
        """
        Other missions can't be multithreaded as mission outcome can affect other agent behaviour
        :return:
        """
        other_agents = [agent for agent in self.active_agents
                        if not isinstance(agent.mission, missions.Observe)]
        for agent in other_agents:
            if agent.mission is None:
                missions.Return(agent, agent.base.location)
                logger.warning(f"{agent} was not on a mission - Previously: {agent.previous_mission}")
        [agent.mission.execute() for agent in other_agents]

    def sample_random_base(self) -> Base:
        return random.choices(self.bases, weights=[base.agent_share
                                                   if base.agent_share is not None
                                                   else 1 / len(self.bases)
                                                   for base in self.bases])[0]

    def remove_agents_from_illegal_zones(self) -> None:
        for agent in self.active_agents:
            zone = agent.assigned_zone
            if self.team == 1:
                if settings.zone_assignment_coalition[agent.service][zone] == 0:
                    agent.return_to_base()
            elif self.team == 2:
                if settings.zone_assignment_hunter[agent.service][zone] == 0:
                    agent.return_to_base()
            else:
                pass

    def reserve_agents(self) -> None:
        agent_types = set([a.service for a in self.active_agents] + [a.service for a in self.inactive_agents])
        for service in agent_types:
            current_share = 0
            required_share = 1
            error_margin = 0.05

            while current_share > required_share + error_margin or current_share < required_share - error_margin:
                active_agents = [a for a in self.active_agents if a.service == service]
                inactive_agents = [a for a in self.inactive_agents if a.service == service]
                reserved_agents = [a for a in self.reserved_agents if a.service == service]
                total_agents = len(active_agents) + len(inactive_agents) + len(reserved_agents)
                current_share = (len(active_agents) + len(inactive_agents)) / total_agents

                # Accept when unable to fix
                if len(reserved_agents) == 0 and current_share < required_share - error_margin:
                    return
                if len(inactive_agents) == 0 and current_share > required_share + error_margin:
                    return

                if self.team == 1:
                    required_share = sum(settings.zone_assignment_coalition[service].values())
                elif self.team == 2:
                    required_share = sum(settings.zone_assignment_hunter[service].values())

                # Move the agent to obtain desired share - we select an agent of the service and adjust
                #   the manager's original lists and update the local copies to match
                if current_share < required_share - error_margin:
                    if len(reserved_agents) == 0:
                        return
                    moved_agent = reserved_agents.pop()
                    self.reserved_agents.remove(moved_agent)
                    self.inactive_agents.append(moved_agent)
                    inactive_agents.append(moved_agent)

                elif current_share > required_share + error_margin:
                    if len(inactive_agents) == 0:
                        return
                    moved_agent = inactive_agents.pop()
                    self.inactive_agents.remove(moved_agent)
                    self.reserved_agents.append(moved_agent)
                    reserved_agents.append(moved_agent)

                # Recalculate statistic after update
                total_agents = len(active_agents) + len(inactive_agents) + len(reserved_agents)
                current_share = (len(active_agents) + len(inactive_agents)) / total_agents

    def adjust_to_setting_change(self) -> None:
        self.remove_agents_from_illegal_zones()
        self.reserve_agents()

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
        eligible_agents = [agent for agent in self.inactive_agents if agent.remaining_maintenance_time == 0
                           and sum(settings.zone_assignment_coalition[agent.service].values()) > 0]

        i = 0
        while utilisation < self.calc_utilization_rate() and len(eligible_agents) > 0:
            self.activate_agent(eligible_agents)
            utilisation = self.get_current_utilisation()
            i += 1
            if i > settings.ITERATION_LIMIT:
                return

    def initiate_agents(self) -> None:
        coalition_data = data_functions.get_coalition_navy_data()
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
        return 0.12

    def activate_agent(self, agents: list) -> None:
        agent = random.choice(agents)
        agents.remove(agent)
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


class CoalitionAirManager(Manager):
    def __init__(self):
        super().__init__()
        self.team = 1
        self.initiate_agents()

    def __str__(self):
        return "Coalition Air Manager"

    def pre_turn_actions(self) -> None:
        for agent in self.active_agents:
            agent.set_turn_movement()

        utilisation = self.get_current_utilisation()
        eligible_agents = [agent for agent in self.inactive_agents if agent.remaining_maintenance_time == 0
                           and sum(settings.zone_assignment_coalition[agent.service].values()) > 0]
        i = 0
        while utilisation < self.calc_utilization_rate() and len(eligible_agents) > 0:
            self.activate_agent(eligible_agents)
            utilisation = self.get_current_utilisation()
            i += 1
            if i > settings.ITERATION_LIMIT:
                return

    def initiate_agents(self) -> None:
        coalition_data = data_functions.get_coalition_aircraft_data()

        for model in coalition_data:
            quantity = int(coalition_data[model]["numberofagents"])
            for _ in range(quantity):
                base, country = self.select_base(country=coalition_data[model]["base"])
                new_ship = CoalitionAircraft(manager=self, model=model, base=base, country=country)
                self.inactive_agents.append(new_ship)

    def initiate_bases(self) -> None:
        self.bases = [Base(name="US Air", location=Point(139.371, 35.768), agent_share=0.1, icon="AirportBlue"),
                      Base(name="JP Air", location=Point(128.236, 26.758), agent_share=0.45, icon="AirportWhite"),
                      Base(name="TW Air", location=Point(121.537, 25.028), agent_share=0.45, icon="AirportGreen")]

    def select_base(self, country: str) -> tuple[Base, str]:
        if country == "Taiwan":
            return self.bases[2], settings.TAIWAN
        elif country == "Japan":
            return self.bases[1], settings.JAPAN
        elif country == "US":
            return self.bases[0], settings.USA
        else:
            raise ValueError(f"Invalid Country {country} for Coalition Aircraft base selection.")

    def calc_utilization_rate(self) -> float:
        return 0.2

    def activate_agent(self, agents: list) -> None:
        agent = random.choice(agents)
        agents.remove(agent)
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


class CoalitionSubManager(Manager):
    def __init__(self):
        super().__init__()
        self.name = "Coalition Sub Manager"
        self.team = 1
        self.initiate_agents()

    def pre_turn_actions(self) -> None:
        for agent in self.active_agents:
            agent.set_turn_movement()

        utilisation = self.get_current_utilisation()
        eligible_agents = [agent for agent in self.inactive_agents if agent.remaining_maintenance_time == 0]

        while utilisation < self.calc_utilization_rate() and len(eligible_agents) > 0:
            successful = self.activate_agent(eligible_agents)

            if not successful:
                return

            utilisation = self.get_current_utilisation()
            eligible_agents = [agent for agent in self.inactive_agents if agent.remaining_maintenance_time == 0]

    def activate_agent(self, agents: list) -> bool:
        agent = random.choice(agents)
        zone = self.select_zone_to_patrol(agent)

        if zone is None:
            return False

        agent.activate()
        agent.go_to_patrol(zone)
        return True

    def select_zone_to_patrol(self, agent) -> zones.Zone | None:
        set_assignment = settings.zone_assignment_coalition[agent.service]
        options = list(set_assignment.keys())
        share = list(set_assignment.values())
        if sum(share) == 0:
            return None

        invalid_zones = [None]

        if not agent.armed:
            invalid_zones.append(zones.ZONE_N)

        selected_zone = None
        while selected_zone in invalid_zones:
            # TODO: Ensure that this doesn't get stuck in a loop when an entire category is only set to zone N
            selected_zone = random.choices(options, share)[0]

        return selected_zone

    def initiate_agents(self) -> None:
        coalition_sub_data = data_functions.get_coalition_sub_data()
        for model in coalition_sub_data:
            quantity = int(coalition_sub_data[model]["numberofagents"])
            for _ in range(quantity):
                new_sub = CoalitionSub(manager=self, model=model, base=self.sample_random_base())
                self.inactive_agents.append(new_sub)

    def initiate_bases(self) -> None:
        self.bases = [Base(name="Okinawa", location=Point(127.737, 26.588), agent_share=1)]

    def calc_utilization_rate(self) -> float:
        return 0.3


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
        self.country = settings.CHINA
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
        self.bases = [Base(name="Shanghai", location=Point(122.0, 31.306), agent_share=0.25),
                      Base(name="Taizhou", location=Point(121.7, 28.231), agent_share=0.25),
                      Base(name="Quanzhou", location=Point(119.04, 24.684), agent_share=0.25),
                      Base(name="Fuzhou", location=Point(119.8, 26.061), agent_share=0.25),]

    def pre_turn_actions(self) -> None:
        for agent in self.active_agents:
            agent.set_turn_movement()

        utilisation = self.get_current_utilisation()
        eligible_agents = [agent for agent in self.inactive_agents if agent.remaining_maintenance_time == 0]

        while utilisation < self.calc_utilization_rate() and len(eligible_agents) > 0:
            successful = self.activate_agent(eligible_agents)

            if not successful:
                return

            utilisation = self.get_current_utilisation()
            eligible_agents = [agent for agent in self.inactive_agents if agent.remaining_maintenance_time == 0]

    def calc_utilization_rate(self) -> float:
        # TODO: Calculate Utilisation rate properly
        return 0.25

    def activate_agent(self, agents: list) -> bool:
        agent = random.choice(agents)
        zone = self.select_zone_to_patrol(agent)

        if zone is None:
            return False

        agent.activate()
        agent.go_to_patrol(zone)
        return True

    def select_zone_to_patrol(self, agent) -> zones.Zone | None:
        set_assignment = settings.zone_assignment_hunter[agent.service]
        options = list(set_assignment.keys())
        share = list(set_assignment.values())
        if sum(share) == 0:
            return None

        invalid_zones = [None]

        if not agent.armed:
            invalid_zones.append(zones.ZONE_N)

        selected_zone = None
        while selected_zone in invalid_zones:
            # TODO: Ensure that this doesn't get stuck in a loop when an entire category is only set to zone N
            selected_zone = random.choices(options, share)[0]

        return selected_zone


class ChinaAirManager(Manager):
    def __init__(self):
        super().__init__()
        self.name = "China Air Manager"
        self.team = 2
        self.initiate_agents()
        self.country = settings.CHINA

    def pre_turn_actions(self) -> None:
        for agent in self.active_agents:
            agent.set_turn_movement()

        utilisation = self.get_current_utilisation()
        eligible_agents = [agent for agent in self.inactive_agents if agent.remaining_maintenance_time == 0]

        while utilisation < self.calc_utilization_rate() and len(eligible_agents) > 0:
            successful = self.activate_agent(eligible_agents)

            if not successful:
                return

            utilisation = self.get_current_utilisation()
            eligible_agents = [agent for agent in self.inactive_agents if agent.remaining_maintenance_time == 0]

    def initiate_agents(self) -> None:
        cn_air_data = data_functions.get_chinese_aircraft_data()
        for model in cn_air_data:
            quantity = int(cn_air_data[model]["numberofagents"])
            for _ in range(quantity):
                new_aircraft = ChineseAircraft(manager=self, model=model, base=self.sample_random_base())
                self.inactive_agents.append(new_aircraft)

    def initiate_bases(self) -> None:
        self.bases = [Base(name="Ningbo", location=Point(121.57, 29.92), icon="AirportRed", agent_share=0.33),
                      Base(name="Fuzhou", location=Point(119.31, 26.00), icon="AirportRed", agent_share=0.34),
                      Base(name="Liangcheng", location=Point(116.75, 25.68), icon="AirportRed", agent_share=0.33)]

    def calc_utilization_rate(self) -> float:
        # TODO: Calculate Utilisation rate properly
        return 0.15

    def activate_agent(self, agents: list) -> bool:
        agent = random.choice(agents)
        zone = self.select_zone_to_patrol(agent)

        if zone is None:
            return False

        agent.activate()
        agent.go_to_patrol(zone)
        return True

    def select_zone_to_patrol(self, agent) -> zones.Zone | None:
        set_assignment = settings.zone_assignment_hunter[agent.service]
        options = list(set_assignment.keys())
        share = list(set_assignment.values())
        if sum(share) == 0:
            return None

        invalid_zones = [None]

        if not agent.armed:
            invalid_zones.append(zones.ZONE_N)

        selected_zone = None
        while selected_zone in invalid_zones:
            # TODO: Ensure that this doesn't get stuck in a loop when an entire category is only set to zone N
            selected_zone = random.choices(options, share)[0]

        return selected_zone


class ChinaSubManager(Manager):
    def __init__(self):
        super().__init__()
        self.name = "China Sub Manager"
        self.team = 2
        self.country = settings.CHINA
        self.initiate_agents()

    def pre_turn_actions(self) -> None:
        for agent in self.active_agents:
            agent.set_turn_movement()

        utilisation = self.get_current_utilisation()
        eligible_agents = [agent for agent in self.inactive_agents if agent.remaining_maintenance_time == 0]

        while utilisation < self.calc_utilization_rate() and len(eligible_agents) > 0:
            successful = self.activate_agent(eligible_agents)

            if not successful:
                return

            utilisation = self.get_current_utilisation()
            eligible_agents = [agent for agent in self.inactive_agents if agent.remaining_maintenance_time == 0]

    def initiate_agents(self) -> None:
        china_sub_data = data_functions.get_chinese_sub_data()
        for model in china_sub_data:
            quantity = int(china_sub_data[model]["numberofagents"])
            for _ in range(quantity):
                new_sub = ChineseSub(manager=self, model=model, base=self.sample_random_base())
                self.inactive_agents.append(new_sub)

    def initiate_bases(self) -> None:
        self.bases = [Base(name="Shanghai", location=Point(122.0, 31.306), agent_share=0.25),
                      Base(name="Taizhou", location=Point(121.7, 28.231), agent_share=0.25),
                      Base(name="Quanzhou", location=Point(119.04, 24.684), agent_share=0.25),
                      Base(name="Fuzhou", location=Point(119.8, 26.061), agent_share=0.25),]

    def calc_utilization_rate(self) -> float:
        return 0.4

    def activate_agent(self, agents: list) -> bool:
        agent = random.choice(agents)
        zone = self.select_zone_to_patrol(agent)

        if zone is None:
            return False

        agent.activate()
        agent.go_to_patrol(zone)
        return True

    def select_zone_to_patrol(self, agent) -> zones.Zone | None:
        set_assignment = settings.zone_assignment_hunter[agent.service]
        options = list(set_assignment.keys())
        share = list(set_assignment.values())
        if sum(share) == 0:
            return None

        invalid_zones = [None]

        if not agent.armed:
            invalid_zones.append(zones.ZONE_N)

        selected_zone = None
        while selected_zone in invalid_zones:
            # TODO: Ensure that this doesn't get stuck in a loop when an entire category is only set to zone N
            selected_zone = random.choices(options, share)[0]

        return selected_zone
