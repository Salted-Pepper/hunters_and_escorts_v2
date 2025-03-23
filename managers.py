from abc import abstractmethod
from multiprocessing import cpu_count
import concurrent.futures
import numpy as np

import settings
from missions import Travel, Attack, Track, Observe, Guard, Return, Holding
from bases import Base
from points import Point
import constants as cs

from ships import Merchant


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

    def check_if_agents_have_to_return(self) -> None:
        relevant_agents = [agent for agent in self.active_agents if not isinstance(agent.mission, Return)]

        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = [executor.submit(agent.mission.execute) for agent in relevant_agents]

            concurrent.futures.wait(futures)

    def have_agents_observe(self) -> None:
        observing_agents = [agent for agent in self.active_agents if isinstance(agent.mission, Observe)]

        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = [executor.submit(agent.mission.execute) for agent in observing_agents]

            concurrent.futures.wait(futures)

    def continue_other_missions(self) -> None:
        other_agents = [agent for agent in self.active_agents
                        if not isinstance(agent.mission, Observe)]

        for agent in other_agents:
            if agent.mission is None:
                print(f"{agent.location} is None - {agent.agent_id} - {agent.activated}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=cpu_count() - 1) as executor:
            futures = [executor.submit(agent.mission.execute) for agent in other_agents]

        print("Completed Other Missions")


class EscortManager(Manager):
    def __init__(self):
        super().__init__()

    def pre_turn_actions(self) -> None:
        pass

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


class MerchantManager(Manager):
    def __init__(self):
        super().__init__()
        self.name = "Merchant Manager"

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
            new_merchant = Merchant(self, model=merchant_type)
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
