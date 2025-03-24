from __future__ import annotations

import random
from abc import abstractmethod

import constants as cs
import settings
from agents import Agent
from bases import Base
from points import Point

import missions

from aircrafts import Aircraft
from submarines import Submarine


class Ship(Agent):

    def __init__(self, manager, model: str, base: Base, ):
        super().__init__(manager, model, base)

    @abstractmethod
    def initiate_model(self) -> None:
        pass


class Merchant(Ship):
    def __init__(self, manager, model: str, base: Base):
        super().__init__(manager, model, base)
        self.boarded = False

        self.entry_point = None
        self.sample_entry_point()
        self.base = base
        self.start_delivering_goods()
        self.activated = True

        self.visibility = None
        self.initiate_model()

    def sample_entry_point(self) -> None:
        x = cs.MAX_LAT
        y = random.uniform(cs.MIN_LONG, 30)
        self.entry_point = Point(x, y)

    def start_delivering_goods(self) -> None:
        self.location = self.entry_point
        missions.Return(agent=self, target=self.base.location)

    def initiate_model(self) -> None:
        attribute = settings.MERCHANT_INFO[self.model]
        self.dwt = attribute["DWT"]
        self.set_speed(attribute["Speed (km/h)"])
        self.visibility = attribute["Visibility"]

    def set_speed(self, speed: float) -> None:
        self.speed_max = speed
        self.speed_cruising = speed
        self.speed_current = speed

    def complete_maintenance(self) -> None:
        missions.Depart(agent=self, target=self.entry_point)
        self.activate()

    def leave_world(self) -> None:
        self.mission.complete()
        self.activated = False
        self.manager.active_agents.remove(self)
        self.remove_from_missions()

    def can_continue(self) -> bool:
        pass

    def enter_base(self) -> None:
        if not self.boarded:
            self.manager.active_agents.remove(self)
            self.manager.inactive_agents.append(self)
            self.base.receive_agent(self)
            self.set_up_for_maintenance()
        else:
            self.manager.active_agents.remove(self)

        self.mission.complete()
        self.activated = False
        self.remove_from_missions()

    def surface_detection(self, agent: Agent) -> bool:
        pass

    def air_detection(self, agent: Agent) -> bool:
        return False

    def sub_detection(self, agent: Agent) -> bool:
        return False

    def observe(self, agents: list[Agent]) -> None:
        pass


class ChineseShip(Ship):
    def __init__(self, manager, model: str, base: Base):
        super().__init__(manager, model, base)

        self.aws_enabled = False
        self.helicopter = False

    def initiate_model(self) -> None:
        model_data = cs.CHINA_NAVY_DATA[self.model]
        self.team = model_data["team"]
        self.service = model_data["service"]

        self.ship_visibility = model_data["SurfaceVisibility"]
        self.air_visibility = model_data["AirVisibility"]
        self.sub_visibility = model_data["UnderseaVisibility"]

        self.speed_max = model_data["SpeedMax"]
        self.speed_cruising = model_data["SpeedCruise"]
        self.dwt = model_data["Displacement"]
        self.endurance = model_data["Endurance"]

        self.ship_detection_skill = model_data["Ship Detection Skill"]
        self.air_detection_skill = model_data["Air Detection Skill"]
        self.sub_detection_skill = model_data["Submarine Detection Skill"]

        self.anti_ship_skill = model_data["Anti-ship Skill"]
        self.anti_air_skill = model_data["Anti-air Skill"]
        self.anti_sub_skill = model_data["Anti-submarine Skill"]

        self.anti_ship_ammo = model_data["Anti-Ship Ammunition"]
        self.anti_air_ammo = model_data["Anti-air Ammunition"]
        self.anti_sub_ammo = model_data["Anti-submarine Ammunition"]

        self.helicopter = True if model_data["helicopter"] == "Y" else False

    def surface_detection(self, agent: Agent) -> bool:
        agent_size = agent.ship_visibility
        detection_range = cs.CHINA_NAVY_DETECTING_SHIP[self.ship_detection_skill][agent_size]
        distance = self.location.distance_to_point(agent.location)

        self.spread_pheromones(detection_range)

        if distance < detection_range:
            return True
        else:
            return False

    def air_detection(self, agent: Agent) -> bool:
        agent_size = agent.ship_visibility
        detection_range = cs.CHINA_NAVY_DETECTING_AIR[self.air_detection_skill][agent_size]
        distance = self.location.distance_to_point(agent.location)

        self.spread_pheromones(detection_range)

        if distance < detection_range:
            return True
        else:
            return False

    def sub_detection(self, agent: Agent) -> bool:
        agent_size = agent.ship_visibility
        if self.aws_enabled:
            detection_range = cs.CHINA_NAVY_DETECTING_SUB_AWS[self.sub_detection_skill][agent_size]
        else:
            detection_range = cs.CHINA_NAVY_DETECTING_SUB_NO_AWS[self.sub_detection_skill][agent_size]
        distance = self.location.distance_to_point(agent.location)

        self.spread_pheromones(detection_range)

        if distance < detection_range:
            return True
        else:
            return False

    def observe(self, agents: list[Agent]) -> None:
        self.make_patrol_move()

        for agent in agents:
            if issubclass(type(agent), Ship):
                detected = self.surface_detection(agent)
            elif issubclass(type(agent), Aircraft):
                detected = self.air_detection(agent)
            elif issubclass(type(agent), Submarine):
                detected = self.sub_detection(agent)
            else:
                raise ValueError(f"Unknown Class {type(agent)} - unable to observe.")

            if detected:
                self.mission.complete()
                missions.Track(self, agent)
                return
