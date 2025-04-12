import math
import random
from abc import abstractmethod

import constants as cs
import data_functions

from agents import Agent
from bases import Base
import missions


class Aircraft(Agent):
    def __init__(self, manager, model: str, base: Base):
        super().__init__(manager, model, base)
        self.agent_type = "air"
        self.manned = True
        self.max_detection_range = 648

    @abstractmethod
    def initiate_model(self) -> None:
        pass

    def set_agent_attributes(self, model_data: dict) -> None:
        self.team = model_data["team"]
        self.manned = False if model_data["type"] == "UAV" else True

        self.ship_visibility = data_functions.parse_string_input(model_data, "SurfaceVisibility", cs.SMALL)
        self.air_visibility = data_functions.parse_string_input(model_data, "AirVisibility", cs.SMALL)
        self.sub_visibility = data_functions.parse_string_input(model_data, "UnderseaVisibility", cs.SMALL)

        self.speed_max = float(model_data.get("SpeedMax", 40))
        self.speed_cruising = float(model_data.get("SpeedCruise", 30))
        self.speed_current = self.speed_cruising
        self.endurance = float(model_data.get("Endurance", 8100))
        self.remaining_endurance = self.endurance

        self.ship_detection_skill = data_functions.parse_string_input(model_data, "Ship Detection Skill", cs.DET_BASIC)
        self.air_detection_skill = data_functions.parse_string_input(model_data, "Air Detection Skill", cs.DET_BASIC)
        self.sub_detection_skill = data_functions.parse_string_input(model_data, "Submarine Detection Skill", cs.DET_BASIC)

        self.anti_ship_skill = data_functions.parse_string_input(model_data, "Anti-ship Skill", cs.ATT_BASIC)
        self.anti_air_skill = data_functions.parse_string_input(model_data, "Anti-air Skill", cs.ATT_BASIC)
        self.anti_sub_skill = data_functions.parse_string_input(model_data, "Anti-submarine Skill", cs.ATT_BASIC)

        self.anti_ship_ammo = int(model_data.get("Anti-Ship Ammunition", 6)) if self.anti_ship_skill is not None else 0
        self.anti_air_ammo = int(model_data.get("Anti-air Ammunition", 6))  if  self.anti_air_skill is not None else 0
        self.anti_sub_ammo = int(model_data.get("Anti-submarine Ammunition", 6)) if self.anti_sub_skill is not None else 0

    @abstractmethod
    def surface_detection(self, agent: Agent) -> bool:
        pass

    @abstractmethod
    def air_detection(self, agent: Agent) -> bool:
        pass

    @abstractmethod
    def sub_detection(self, agent: Agent) -> bool:
        pass

    @abstractmethod
    def track(self, target: Agent) -> None:
        pass

    @abstractmethod
    def attack(self, target: Agent, ammo, attacker_skill: str) -> None:
        pass


class ChineseAircraft(Aircraft):
    def __init__(self, manager, model: str, base: Base):
        super().__init__(manager, model, base)
        self.combat_type = "CN AIRCRAFT"
        self.initiate_model()

    def __repr__(self):
        return f"{self.service}-{self.agent_id} - on mission: {self.mission} - zone: {self.assigned_zone}"

    def __str__(self):
        return f"{self.service}-{self.agent_id} - on mission: {self.mission} - zone: {self.assigned_zone}"

    def initiate_model(self) -> None:
        model_data = cs.CHINA_AIR_DATA[self.model]
        self.set_agent_attributes(model_data)

        if self.manned:
            self.service = "Air Manned"
        else:
            self.service = "Air UAV"

    def surface_detection(self, agent: Agent) -> bool:
        if self.anti_ship_skill is None:
            return False
        elif self.anti_ship_skill == cs.DET_BASIC:
            k = 2747
        elif self.anti_ship_skill == cs.DET_ADV:
            k = 39633
        else:
            raise ValueError(f"Invalid anti-ship skill for {self.model}: {self.anti_ship_skill}")


        distance = self.location.distance_to_point(agent.location)
        if distance > 300:
            return False

        sea_state = cs.world.receptor_grid.get_receptor_at_location(self.location).sea_state
        h = 10
        s = cs.sea_state_values.get(sea_state, 0.4)
        r = cs.rcs_dict[agent.air_visibility]

        detection_probability = (1 - math.exp(-(k * h * r * s) / distance ** 3))
        print(f"Detection prob {self} - {agent} is {detection_probability}")
        if random.uniform(0, 1) < detection_probability:
            return True
        else:
            return False

    def air_detection(self, agent: Agent) -> bool:
        distance = self.location.distance_to_point(agent.location)
        max_distance = cs.CHINA_AIR_DETECTING_AIR[self.anti_air_skill][agent.air_visibility]
        if distance > max_distance:
            return False
        else:
            return True

    def sub_detection(self, agent: Agent) -> bool:
        distance = self.location.distance_to_point(agent.location)

        if self.anti_sub_skill == cs.DET_BASIC:
            max_distance = 5
        elif self.anti_ship_skill == cs.DET_ADV:
            max_distance = 18.5
        else:
            raise ValueError(f"Invalid anti-ship skill for {self.model}")

        if distance > max_distance:
            return False
        else:
            return True

    def detection(self, target) -> bool:
        if target.agent_type == "ship" or target.agent_type == cs.MERCHANT:
            if self.anti_ship_skill is None:
                return False
            return self.surface_detection(target)

        elif target.agent_type == "air":
            if self.anti_air_skill is None:
                return False
            return self.air_detection(target)

        elif target.agent_type == "sub":
            if self.anti_sub_skill is None:
                return False
            return self.sub_detection(target)
        else:
            raise ValueError(f"Unhandled agent type {target.agent_type} for {target}")

    def track(self, target: Agent) -> None:
        if cs.world.world_time - self.route.creation_time > 1 or self.route.next_point() is None:
            self.generate_route(target.location)

        if self.location.distance_to_point(target.location) > 12:
            self.move_through_route()

        if ((target.agent_type == "ship" and self.anti_ship_skill is not None) or
              (target.agent_type == "air" and self.anti_air_skill is not None) or
              (target.agent_type == "sub" and self.anti_sub_skill is not None)):
            self.mission.change()
            missions.Attack(self, target)
            return
        else:
            self.request_support(target)

    def attack(self, target: Agent, ammo, attacker_skill: str) -> None:
        if target.agent_type == "sub":
            defense_skill = target.air_visibility
            probabilities = data_functions.get_attack_probabilities(self.combat_type, attacker_skill,
                                                                    target.combat_type, defense_skill)
            self.anti_sub_ammo -= 1
        elif target.combat_type == cs.MERCHANT:
            probabilities = cs.MERCHANT_PROBABILITIES[target.air_visibility]
            new_probability = probabilities["sunk"] + target.damage * 0.2
            probabilities["sunk"] = min(new_probability, 1 - probabilities["ctl"])
            probabilities["nothing"] = 1 - (probabilities["sunk"] + probabilities["ctl"])
            self.anti_ship_ammo -= 1
        elif target.agent_type == "ship":
            defense_skill = target.anti_air_skill
            probabilities = data_functions.get_attack_probabilities(self.combat_type, attacker_skill,
                                                                    target.combat_type, defense_skill)
            self.anti_ship_ammo -= 1
        elif target.agent_type == "air":
            defense_skill = target.anti_air_skill
            probabilities = data_functions.get_attack_probabilities(self.combat_type, attacker_skill,
                                                                    target.combat_type, defense_skill)
            self.anti_air_ammo -= 1
        else:
            raise ValueError(f"Unknown agent type {target.agent_type}")

        outcome = random.choices(list(probabilities.keys()), list(probabilities.values()))[0]
        ammo.stock -= 1

        if outcome == "sunk":
            target.is_destroyed()
            self.mission.complete()
            self.return_to_base()
        elif outcome == "ctl":
            target.CTL = True
        elif outcome == "nothing":
            if target.combat_type == cs.MERCHANT:
                target.damage += 1
        else:
            raise ValueError(f"Unknown outcome {outcome}")

