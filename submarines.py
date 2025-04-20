from abc import abstractmethod
import random

import data_functions
import constants as cs
import settings
from agents import Agent
from bases import Base

import missions


class Submarine(Agent):
    def __init__(self, manager, model: str, base: Base):
        super().__init__(manager, model, base)
        self.agent_type = "sub"

    @abstractmethod
    def initiate_model(self) -> None:
        pass

    def set_agent_attributes(self, model_data: dict) -> None:
        self.team = model_data["team"]
        self.service = model_data["service"]
        self.armed = True if model_data.get("Armed", "Y") == "Y" else False

        self.ship_visibility = data_functions.parse_string_input(model_data, "SurfaceVisibility", cs.SMALL)
        self.air_visibility = data_functions.parse_string_input(model_data, "AirVisibility", cs.SMALL)
        self.sub_visibility = data_functions.parse_string_input(model_data, "UnderseaVisibility", cs.SMALL)

        self.speed_max = model_data.get("SpeedMax", 40)
        self.speed_cruising = model_data.get("SpeedCruise", 30)
        self.speed_current = self.speed_cruising
        self.dwt = model_data.get("Displacement", 1500)
        self.endurance = float(model_data.get("Endurance", 8100))
        self.remaining_endurance = self.endurance

        self.ship_detection_skill = data_functions.parse_string_input(model_data, "Ship Detection Skill", cs.DET_BASIC)
        self.air_detection_skill = data_functions.parse_string_input(model_data, "Air Detection Skill", None)
        self.sub_detection_skill = data_functions.parse_string_input(model_data, "Submarine Detection Skill",
                                                                     cs.DET_BASIC)
        self.anti_ship_ammo = int(model_data.get("Anti-Ship Ammunition", 6)) if self.anti_ship_skill is not None else 0
        self.anti_air_ammo = int(model_data.get("Anti-air Ammunition", 6)) if self.anti_air_skill is not None else 0
        self.anti_sub_ammo = int(
            model_data.get("Anti-submarine Ammunition", 6)) if self.anti_sub_skill is not None else 0

    @abstractmethod
    def surface_detection(self, agent: Agent) -> bool:
        pass

    def air_detection(self, agent: Agent) -> bool:
        return False

    @abstractmethod
    def sub_detection(self, agent: Agent) -> bool:
        pass

    def observe(self, agents: list[Agent], traveling=False) -> None:
        if not traveling:
            self.make_patrol_move()
        agents = self.remove_invalid_targets(agents)

        for agent in agents:
            if agent.world_data:
                continue

            if agent.agent_type == "air":
                continue

            if self.location.distance_to_point(agent.location) > cs.COALITION_NAVY_MAX_DETECTION_RANGE:
                continue

            if not self.check_if_valid_target(agent):
                return

            if agent.agent_type == "ship":
                detected = self.surface_detection(agent)
            elif agent.agent_type == "sub":
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

        if ((target.agent_type == "ship" and self.anti_ship_skill is not None) or
                (target.agent_type == "sub" and self.anti_sub_skill is not None)):
            self.mission.change()
            missions.Attack(self, target)
            return
        else:
            self.request_support(target)

    def attack(self, target, ammo, attacker_skill) -> None:
        if target.agent_type == "sub":
            defense_skill = target.ship_visibility
            probabilities = data_functions.get_attack_probabilities(self.combat_type, attacker_skill,
                                                                    target.combat_type, defense_skill)
            self.anti_sub_ammo -= 1
        elif target.combat_type == cs.MERCHANT:
            self.handle_merchant_attack(target)
            return
        elif target.agent_type == "ship":
            defense_skill = target.anti_sub_skill
            probabilities = data_functions.get_attack_probabilities(self.combat_type, attacker_skill,
                                                                    target.combat_type, defense_skill)
            self.anti_sub_ammo -= 1
            self.anti_ship_ammo -= 1
        else:
            raise ValueError(f"Unaccounted agent type {target.agent_type}")

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

    def handle_merchant_attack(self, target) -> None:
        hit_chance = cs.SUB_HIT_CHANCE[self.anti_ship_skill][target.anti_sub_skill]
        if random.uniform(0, 1) > hit_chance:
            return

        # Check if Tanker or LNG:
        if target.model.startswith("T") or target.model == "LNG":
            if target.damage == 0:
                prob_sink = 0.75
            else:
                prob_sink = 1
        else:
            if target.damage == 0:
                prob_sink = 0.53
            elif target.damage == 1:
                prob_sink = 0.73
            elif target.damage == 2:
                prob_sink = 0.71
            else:
                prob_sink = 1

        if random.uniform(0, 1) <= prob_sink:
            target.is_destroyed()
            self.mission.complete()
            self.return_to_base()
        else:
            target.damage += 1


class ChineseSub(Submarine):
    def __init__(self, manager, model: str, base: Base):
        super().__init__(manager, model, base)
        self.asw_enabled = False
        self.combat_type = "CN SUB"
        self.initiate_model()
        self.service = cs.HUNTER_SUBMARINE

    def initiate_model(self) -> None:
        model_data = cs.CHINA_SUB_DATA[self.model]
        self.set_agent_attributes(model_data)

    def surface_detection(self, agent: Agent) -> bool:
        agent_size = agent.sub_visibility
        detection_range = cs.CHINA_SUB_DETECTING_SHIP[self.ship_detection_skill][agent_size]
        distance = self.location.distance_to_point(agent.location)

        if distance < detection_range:
            return True
        else:
            return False

    def sub_detection(self, agent: Agent) -> bool:
        agent_size = agent.sub_visibility
        detection_range = cs.CHINA_SUB_DETECTING_SUB[self.ship_detection_skill][agent_size]
        distance = self.location.distance_to_point(agent.location)

        if distance < detection_range:
            return True
        else:
            return False


class CoalitionSub(Submarine):
    def __init__(self, manager, model: str, base: Base):
        super().__init__(manager, model, base)
        self.asw_enabled = False
        self.combat_type = "COALITION SUB"
        self.initiate_model()

    def initiate_model(self) -> None:
        model_data = cs.COALITION_SUB_DATA[self.model]
        self.set_agent_attributes(model_data)

        if self.service == "USN":
            self.country = settings.USA
            self.service = cs.COALITION_US_SUB
        elif self.service == "JMSDF":
            self.country = settings.JAPAN
            self.service = cs.COALITION_JP_SUB
        else:
            raise ValueError(f"Invalid service for submarine {self.service}")

    def surface_detection(self, agent: Agent) -> bool:
        agent_size = agent.sub_visibility
        detection_range = cs.COALITION_SUB_DETECTING_SHIP[self.ship_detection_skill][agent_size]
        distance = self.location.distance_to_point(agent.location)

        if distance < detection_range:
            return True
        else:
            return False

    def sub_detection(self, agent: Agent) -> bool:
        agent_size = agent.sub_visibility
        detection_range = cs.COALITION_SUB_DETECTING_SUB[self.ship_detection_skill][agent_size]
        distance = self.location.distance_to_point(agent.location)

        if distance < detection_range:
            return True
        else:
            return False

