from __future__ import annotations

import random
from abc import abstractmethod

import constants as cs
import settings
from agents import Agent
from bases import Base
from points import Point

import missions
import tracker

from aircrafts import Aircraft
from submarines import Submarine


class Ship(Agent):

    def __init__(self, manager, model: str, base: Base, ):
        super().__init__(manager, model, base)

    @abstractmethod
    def initiate_model(self) -> None:
        pass


class Merchant(Ship):
    def __init__(self, manager, model: str, base: Base, country: str):
        super().__init__(manager, model, base)
        self.color = "0x267326"
        self.country = country
        self.boarded = False

        self.entry_point = None
        self.sample_entry_point()
        self.base = base
        self.start_delivering_goods()
        self.activated = True

        self.initiate_model()

    def __repr__(self):
        return f"Merchant {self.agent_id} at {self.location} - on {self.mission} - {self.activated}"

    def __str__(self):
        return f"Merchant {self.agent_id} at {self.location} - on {self.mission} - {self.activated}"

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
        self.ship_visibility = attribute["Visibility"]
        self.air_visibility = attribute["Visibility"]
        self.sub_visibility = attribute["Visibility"]
        self.movement_left_in_turn = self.speed_current * settings.time_delta

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
        self.manager.active_agents.remove(self)
        self.manager.inactive_agents.append(self)

        if not self.boarded:
            self.base.receive_agent(self)
            self.set_up_for_maintenance()
            tracker.Event(text=f"Merchant {self.agent_id} made it to {self.base.name}",
                          event_type="Merchant Arrived")
        else:
            tracker.Event(text=f"Merchant {self.agent_id} has been seized.",
                          event_type="Merchant Seized")

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

    def track(self, target: Agent) -> None:
        pass

    def is_boarded(self, boarder: Agent) -> None:
        self.mission.abort()
        self.remove_from_missions()

        self.color = boarder.color
        self.team = boarder.team

        if self.team == 1:
            self.boarded = False
            location = self.base
        elif self.team == 2:
            self.boarded = True
            location = boarder.base.location
        else:
            raise ValueError(f"Unknown team {self.team}")

        missions.Return(self, target=location)

    def get_resistance_level(self) -> str:
        return settings.merchant_rules[settings.COALITION_SELECTED_LEVEL][self.country]


class ChineseShip(Ship):
    def __init__(self, manager, model: str, base: Base):
        super().__init__(manager, model, base)
        self.color = "0xb30000"
        self.aws_enabled = False
        self.helicopter = False

    def initiate_model(self) -> None:
        model_data = cs.CHINA_NAVY_DATA[self.model]
        self.team = model_data["team"]
        self.service = model_data["service"]
        self.armed = True if model_data["Armed"] == "Y" else False

        self.ship_visibility = model_data["SurfaceVisibility"]
        self.air_visibility = model_data["AirVisibility"]
        self.sub_visibility = model_data["UnderseaVisibility"]

        self.speed_max = model_data["SpeedMax"]
        self.speed_cruising = model_data["SpeedCruise"]
        self.speed_current = self.speed_cruising
        self.dwt = model_data["Displacement"]
        self.endurance = model_data["Endurance"]
        self.remaining_endurance = self.endurance

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

        if distance < detection_range:
            return True
        else:
            return False

    def air_detection(self, agent: Agent) -> bool:
        agent_size = agent.ship_visibility
        detection_range = cs.CHINA_NAVY_DETECTING_AIR[self.air_detection_skill][agent_size]
        distance = self.location.distance_to_point(agent.location)

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

        if distance < detection_range:
            return True
        else:
            return False

    def observe(self, agents: list[Agent]) -> None:
        self.make_patrol_move()
        for agent in agents:
            if agent.team == self.team:
                # To handle exception for boarded merchants
                continue
            if self.location.distance_to_point(agent.location) > cs.CHINESE_NAVY_MAX_DETECTION_RANGE:
                continue

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

        self.spread_pheromones(self.location)

    def track(self, target: Agent) -> None:
        if cs.world.world_time - self.route.creation_time > 1 or self.route.next_point() is None:
            self.generate_route(target.location)

        if self.location.distance_to_point(target.location) > 12:
            self.move_through_route()

        if self.location.distance_to_point(target.location) > 12:
            return

        if settings.CHINA_SELECTED_LEVEL == 1 and isinstance(target, Merchant):
            self.prepare_to_board(target)
        else:
            self.go_to_attack(target)

    def request_support(self) -> None:
        pass

    def prepare_to_board(self, target: Merchant) -> None:
        if self.location.distance_to_point(target.location) > 12:
            return
        else:
            successful = self.attempt_boarding(target)

        if successful:
            self.mission.complete()
            target.is_boarded(self)
            missions.Guard(self, target)
        else:
            # TODO: Set up rules for attacking merchants here
            pass

    def attempt_boarding(self, target) -> bool:
        resistance_level = target.get_resistance_level()
        receptor = cs.world.receptor_grid.get_receptor_at_location(target.location)
        base_success_rate = 0.22

        if receptor.sea_state > 4:
            return False
        elif receptor.sea_state == 3:
            base_success_rate *= 0.8

        if self.service == cs.HUNTER_CCG or self.service == cs.HUNTER_MSA:
            base_success_rate *= 1.2

        if self.helicopter:
            base_success_rate *= 1.2

        if resistance_level == cs.COMPLY:
            base_success_rate *= 1.6
        elif resistance_level == cs.RESIST:
            base_success_rate *= 0.7

        if random.uniform(0, 1) < base_success_rate:
            return True
        else:
            return False

    def go_to_attack(self, target: Agent) -> None:
        if not self.armed:
            self.request_support()

        # TODO: Create attack interaction here
