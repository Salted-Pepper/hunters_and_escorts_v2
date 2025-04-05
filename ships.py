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
        self.helicopter = False
        self.aws_enabled = False

    @abstractmethod
    def initiate_model(self) -> None:
        pass

    def set_agent_attributes(self, model_data: dict) -> None:

        self.team = model_data["team"]
        self.service = model_data["service"]
        self.armed = True if model_data.get("Armed", "Y") == "Y" else False
        self.agent_type = model_data.get("type", None)

        self.ship_visibility = self.parse_string_input(model_data, "SurfaceVisibility", cs.SMALL)
        self.air_visibility = self.parse_string_input(model_data, "AirVisibility", cs.SMALL)
        self.sub_visibility = self.parse_string_input(model_data, "UnderseaVisibility", cs.SMALL)

        self.speed_max = model_data.get("SpeedMax", 40)
        self.speed_cruising = model_data.get("SpeedCruise", 30)
        self.speed_current = self.speed_cruising
        self.dwt = model_data.get("Displacement", 1500)
        self.endurance = model_data.get("Endurance", 8100)
        self.remaining_endurance = self.endurance

        self.ship_detection_skill = self.parse_string_input(model_data, "Ship Detection Skill", cs.DET_BASIC)
        self.air_detection_skill = self.parse_string_input(model_data, "Air Detection Skill", cs.DET_BASIC)
        self.sub_detection_skill = self.parse_string_input(model_data, "Submarine Detection Skill", cs.DET_BASIC)

        self.anti_ship_skill = self.parse_string_input(model_data, "Anti-ship Skill", cs.ATT_BASIC)
        self.anti_air_skill = self.parse_string_input(model_data, "Anti-air Skill", cs.ATT_BASIC)
        self.anti_sub_skill = self.parse_string_input(model_data, "Anti-submarine Skill", cs.ATT_BASIC)

        self.anti_ship_ammo = model_data.get("Anti-Ship Ammunition", 6)
        self.anti_air_ammo = model_data.get("Anti-air Ammunition", 6)
        self.anti_sub_ammo = model_data.get("Anti-submarine Ammunition", 6)

        self.helicopter = True if model_data["helicopter"] == "Y" else False

    @staticmethod
    def parse_string_input(model_data, key, default) -> str | None:
        value = model_data.get(key, default)
        if value is None:
            return value
        else:
            return value.lower()


class Merchant(Ship):
    def __init__(self, manager, model: str, base: Base, country: str):
        super().__init__(manager, model, base)
        self.country = country
        self.set_service()
        self.team = 1
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

    def set_service(self) -> None:
        if self.country == settings.TAIWAN:
            self.service = cs.COALITION_TW_MERCHANT
        elif self.country == settings.JAPAN:
            self.service = cs.COALITION_JP_MERCHANT
        elif self.country == settings.USA:
            self.service = cs.COALITION_US_MERCHANT
        elif self.country == settings.MARKET:
            self.service = cs.COALITION_MK_MERCHANT
        else:
            raise ValueError(f"Invalid Country {self.country}")

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
            tracker.Event(text=f"Merchant {self.agent_id} reached {self.base.name}",
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
        print(f"{self} got boarded.")
        self.mission.abort()
        self.remove_from_missions()

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
        self.aws_enabled = False
        self.helicopter = False

        self.initiate_model()

    def __repr__(self):
        return f"{self.service}-{self.agent_id} - on mission: {self.mission} - zone: {self.assigned_zone}"

    def __str__(self):
        return f"{self.service}-{self.agent_id} - on mission: {self.mission} - zone: {self.assigned_zone}"

    def initiate_model(self) -> None:
        model_data = cs.CHINA_NAVY_DATA[self.model]
        self.set_agent_attributes(model_data)

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
            if self.location.distance_to_point(agent.location) > cs.CHINESE_NAVY_MAX_DETECTION_RANGE:
                continue

            if not self.check_if_valid_target(agent):
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
        print(f"{self} is attempting to board {target}")
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


class Escort(Ship):
    def __init__(self, manager, model: str, base: Base, country: str):
        super().__init__(manager, model, base)
        self.country = country

        self.initiate_model()

    def initiate_model(self) -> None:
        model_data = cs.COALITION_NAVY_DATA[self.model]
        self.set_agent_attributes(model_data)

        if self.country == settings.TAIWAN:
            self.service = cs.COALITION_TW_ESCORT
        elif self.country == settings.JAPAN:
            self.service = cs.COALITION_JP_ESCORT
        elif self.country == settings.USA:
            self.service = cs.COALITION_US_ESCORT

    def surface_detection(self, agent: Agent) -> bool:
        agent_size = agent.ship_visibility
        detection_range = cs.COALITION_NAVY_DETECTING_SHIP[self.ship_detection_skill][agent_size]
        distance = self.location.distance_to_point(agent.location)

        if distance < detection_range:
            return True
        else:
            return False

    def air_detection(self, agent: Agent) -> bool:
        agent_size = agent.ship_visibility
        detection_range = cs.COALITION_NAVY_DETECTING_AIR[self.air_detection_skill][agent_size]
        distance = self.location.distance_to_point(agent.location)

        if distance < detection_range:
            return True
        else:
            return False

    def sub_detection(self, agent: Agent) -> bool:
        agent_size = agent.ship_visibility
        if self.aws_enabled:
            detection_range = cs.COALITION_NAVY_DETECTING_SUB_AWS[self.sub_detection_skill][agent_size]
        else:
            detection_range = cs.COALITION_NAVY_DETECTING_SUB_NO_AWS[self.sub_detection_skill][agent_size]
        distance = self.location.distance_to_point(agent.location)

        if distance < detection_range:
            return True
        else:
            return False

    def observe(self, agents: list[Agent]) -> None:
        self.make_patrol_move()
        for agent in agents:
            if self.location.distance_to_point(agent.location) > cs.COALITION_NAVY_MAX_DETECTION_RANGE:
                continue

            if not self.check_if_valid_target(agent):
                return

            if issubclass(type(agent), Ship):
                if self.anti_ship_skill is None:
                    continue
                detected = self.surface_detection(agent)
            elif issubclass(type(agent), Aircraft):
                if self.anti_air_skill is None:
                    continue
                detected = self.air_detection(agent)
            elif issubclass(type(agent), Submarine):
                if self.anti_sub_skill is None:
                    continue
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

        # TODO: Add Check if able to attack or liberate here
        if isinstance(target, Merchant):
            pass

    def prepare_to_board(self, target: Merchant) -> None:
        print(f"{self} is attempting to board {target}")
        if self.location.distance_to_point(target.location) > 12:
            return
        else:
            successful = self.attempt_boarding(target)

        if successful and not cs.world.zones.ZONE_L.contains_point(target.location):
            self.mission.complete()
            target.is_boarded(self)
            missions.Guard(self, target)

    def attempt_boarding(self, target) -> bool:
        # TODO: Get boarding parameters for escort here - for now just guaranteed success
        return True

