from __future__ import annotations

import random
from abc import abstractmethod
import logging
import os
import datetime
import time

import constants as cs
import data_functions
import settings
from agents import Agent
from bases import Base
from points import Point
import zones

import missions
import tracker

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename=os.path.join(os.getcwd(), 'logs/mission_log_' + str(date) + '.log'),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("Ships")
logger.setLevel(logging.DEBUG)


class Ship(Agent):

    def __init__(self, manager, model: str, base: Base, ):
        super().__init__(manager, model, base)
        self.helicopter = False
        self.aws_enabled = False
        self.agent_type = "ship"

    @abstractmethod
    def initiate_model(self) -> None:
        pass

    def set_agent_attributes(self, model_data: dict) -> None:
        self.team = model_data["team"]
        self.service = "Ship " + model_data["service"]
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
        self.air_detection_skill = data_functions.parse_string_input(model_data, "Air Detection Skill", cs.DET_BASIC)
        self.sub_detection_skill = data_functions.parse_string_input(model_data, "Submarine Detection Skill",
                                                                     cs.DET_BASIC)

        self.anti_ship_skill = data_functions.parse_string_input(model_data, "Anti-ship Skill", cs.ATT_BASIC)
        self.anti_air_skill = data_functions.parse_string_input(model_data, "Anti-air Skill", cs.ATT_BASIC)
        self.anti_sub_skill = data_functions.parse_string_input(model_data, "Anti-submarine Skill", cs.ATT_BASIC)

        self.anti_ship_ammo = int(model_data.get("Anti-Ship Ammunition", 6)) if self.anti_ship_skill is not None else 0
        self.anti_air_ammo = int(model_data.get("Anti-air Ammunition", 6)) if self.anti_air_skill is not None else 0
        self.anti_sub_ammo = int(
            model_data.get("Anti-submarine Ammunition", 6)) if self.anti_sub_skill is not None else 0

        self.missile_defense = data_functions.parse_string_input(model_data, "Defense against missiles", cs.ATT_BASIC)
        self.helicopter = True if model_data["helicopter"] == "Y" else False

    def attack(self, target, ammo, attacker_skill):
        if target.agent_type == "sub":
            defense_skill = target.ship_visibility
            probabilities = data_functions.get_attack_probabilities(self.combat_type, attacker_skill,
                                                                    target.combat_type, defense_skill)
            self.anti_sub_ammo -= 1
        elif target.combat_type == cs.MERCHANT:
            probabilities = cs.MERCHANT_PROBABILITIES[target.ship_visibility]
            new_probability = probabilities["sunk"] + target.damage * 0.2
            probabilities["sunk"] = min(new_probability, 1 - probabilities["ctl"])
            probabilities["nothing"] = 1 - (probabilities["sunk"] + probabilities["ctl"])
            self.anti_ship_ammo -= 1
        elif target.agent_type == "ship":
            defense_skill = target.missile_defense
            probabilities = data_functions.get_attack_probabilities(self.combat_type, attacker_skill,
                                                                    target.combat_type, defense_skill)
            self.anti_ship_ammo -= 1
        elif target.agent_type == "air":
            defense_skill = target.missile_defense
            probabilities = data_functions.get_attack_probabilities(self.combat_type, attacker_skill,
                                                                    target.combat_type, defense_skill)
            self.anti_air_ammo -= 1
        else:
            raise ValueError(f"Unknown agent type {target.agent_type}")

        outcome = random.choices(list(probabilities.keys()), list(probabilities.values()))[0]
        ammo.stock -= 1

        if outcome == "sunk":
            target.is_destroyed(self)
            self.mission.complete()
            self.return_to_base()
        elif outcome == "ctl":
            target.CTL = True
            tracker.log_event(self.service, self.model,"CTL")
        elif outcome == "nothing":
            if target.combat_type == cs.MERCHANT:
                if target.damage == 0:
                    tracker.log_event(self.service, self.model, "damaged")
                target.damage += 1
        else:
            raise ValueError(f"Unknown outcome {outcome}")


class Merchant(Ship):
    def __init__(self, manager, model: str, base: Base, country: str):
        super().__init__(manager, model, base)
        self.country = country
        self.set_service()
        self.team = 1
        self.boarded = False
        self.seizing_agent = None
        self.damage = 0

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

    def to_dict(self) -> dict:
        if self.boarded:
            manager = str(self.manager) + " Boarded"
        else:
            manager = str(self.manager)
        return {"x": self.location.x,
                "y": self.location.y,
                "model": self.model,
                "agent_id": self.agent_id,
                "activated": self.activated,
                "mission": str(self.mission),
                "type": manager,
                "service": self.service,
                "rem_endurance": self.remaining_endurance}

    def sample_entry_point(self) -> None:
        x = cs.MAX_LAT - 0.01
        y = random.uniform(cs.MIN_LONG, 34)
        self.entry_point = Point(x, y)

    def start_delivering_goods(self) -> None:
        self.location = self.entry_point
        missions.Return(agent=self, target=self.base.location)

    def initiate_model(self) -> None:
        attribute = settings.MERCHANT_INFO[self.model]
        self.dwt = attribute["DWT"]
        self.set_speed(attribute["Speed"])
        self.ship_visibility = attribute["Visibility"]
        self.air_visibility = attribute["Visibility"]
        self.sub_visibility = attribute["Visibility"]
        self.movement_left_in_turn = self.speed_current * settings.time_delta
        self.remaining_endurance = 0
        self.combat_type = cs.MERCHANT

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
        return True

    def enter_base(self) -> None:
        self.manager.active_agents.remove(self)
        self.manager.inactive_agents.append(self)

        if not self.boarded:
            self.base.receive_agent(self)
            self.set_up_for_maintenance()
            tracker.Event(text=f"{self.service} ({self.agent_id}) reached {self.base.name}",
                          event_type="Merchant Arrived")
            tracker.log_event(self.service, self.model, "arrived")
        else:
            tracker.log_event(self.service, self.model, "seized")
            tracker.Event(text=f"{self.service} ({self.agent_id}) has been seized by "
                               f"{self.seizing_agent.service} ({self.seizing_agent.agent_id}) - {self.seizing_agent.model}.",
                          event_type="Merchant Seized")

        self.mission.complete()
        self.activated = False
        self.remove_from_missions()

    def get_seizing_agent(self) -> Agent:
        for mission in self.involved_missions:
            if mission.mission_type == "guard":
                return mission.agent

    def surface_detection(self, agent: Agent) -> bool:
        pass

    def air_detection(self, agent: Agent) -> bool:
        return False

    def sub_detection(self, agent: Agent) -> bool:
        return False

    def observe(self, agents: list[Agent], traveling=False) -> None:
        pass

    def track(self, target: Agent) -> None:
        pass

    def attempt_to_attack(self, target) -> None:
        raise TypeError(f"{self} is unable to attack.")

    def attack(self, target, ammo, attacker_skill) -> None:
        raise TypeError(f"{self} is unable to attack.")

    def is_boarded(self, boarder: Agent) -> None:
        logger.debug(f"{self} got boarded by {boarder}.")
        self.seizing_agent = boarder
        self.mission.abort()
        self.remove_from_missions()

        self.team = boarder.team

        if self.team == 1:
            self.boarded = False
            location = self.base.location
        elif self.team == 2:
            self.boarded = True
            location = boarder.base.location
        else:
            raise ValueError(f"Unknown team {self.team}")

        missions.Return(self, target=location)

    def get_resistance_level(self) -> str:
        return settings.merchant_rules[settings.COALITION_SELECTED_LEVEL][self.country]

    def escort_near(self) -> bool:
        all_escorts = (cs.world.tw_manager_escorts.active_agents +
                       cs.world.jp_manager_escorts.active_agents +
                       cs.world.us_manager_escorts.active_agents)
        for escort in all_escorts:
            if self.location.distance_to_point(escort.location) < 12:
                return True
        return False


class ChineseShip(Ship):
    def __init__(self, manager, model: str, base: Base):
        super().__init__(manager, model, base)
        self.asw_enabled = False
        self.helicopter = False
        self.combat_type = "CN NAVY"
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

    def track(self, target: Agent) -> None:
        if cs.world.world_time - self.route.creation_time > 1 or self.route.next_point() is None:
            self.generate_route(target.location)

        if self.location.distance_to_point(target.location) > 12:
            self.move_through_route()

        if settings.CHINA_SELECTED_LEVEL == 1 and isinstance(target, Merchant):
            self.prepare_to_board(target)
        elif isinstance(target, Merchant):
            if self.anti_ship_skill is not None:
                self.mission.change()
                missions.Attack(self, target)
            else:
                self.request_support(target)
        elif ((target.agent_type == "ship" and self.anti_ship_skill is not None) or
              (target.agent_type == "air" and self.anti_air_skill is not None) or
              (target.agent_type == "sub" and self.anti_sub_skill is not None)):
            self.mission.change()
            missions.Attack(self, target)
            return
        else:
            self.request_support(target)

    def prepare_to_board(self, target: Merchant) -> None:
        if self.location.distance_to_point(target.location) > 12:
            return

        successful = self.attempt_boarding(target)

        if successful:
            self.mission.complete()
            target.is_boarded(self)
            missions.Guard(self, target)
            return
        elif not settings.boarding_only:
            if self.armed:
                outcome = random.choices(["ctl", "sunk", "damaged"], [0.2, 0.2, 0.6])[0]
                if outcome == "ctl":
                    target.ctl = True
                    tracker.log_event(self.service, self.model, "CTL")
                elif outcome == "sunk":
                    target.is_destroyed(self)
                    self.mission.complete()
                    self.return_to_base()
                elif outcome == "damaged":
                    if target.damage == 0:
                        tracker.log_event(self.service, self.model, "damaged")
                    target.damage += 1
                return
            elif self.anti_ship_skill is not None:
                self.mission.change()
                missions.Attack(self, target)
                return
            else:
                self.request_support(target)

    def attempt_boarding(self, target: Merchant) -> bool:
        resistance_level = target.get_resistance_level()
        receptor = cs.world.receptor_grid.get_receptor_at_location(target.location)
        base_success_rate = 0.22

        if self.team == 1 and target.escort_near():
            return False

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


class Escort(Ship):
    def __init__(self, manager, model: str, base: Base, country: str):
        super().__init__(manager, model, base)
        self.country = country
        self.initiate_model()
        self.combat_type = "COALITION ESCORT"

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

    def observe(self, agents: list[Agent], traveling=False) -> bool:
        if not traveling:
            t_0 = time.time()
            self.make_patrol_move()
            tracker.USED_TIME["Observe-Moving"] += time.time() - t_0

        t_0 = time.time()
        agents = self.remove_invalid_targets(agents)
        tracker.USED_TIME["Observe-Filtering"] += time.time() - t_0

        for agent in agents:
            t_0 = time.time()
            if self.location.distance_to_point(agent.location) > cs.COALITION_NAVY_MAX_DETECTION_RANGE:
                tracker.USED_TIME["Observe-Distance"] += time.time() - t_0
                continue
            tracker.USED_TIME["Observe-Distance"] += time.time() - t_0

            t_0 = time.time()
            if not self.check_if_valid_target(agent):
                tracker.USED_TIME["Observe-Validation"] += time.time() - t_0
                return False
            tracker.USED_TIME["Observe-Validation"] += time.time() - t_0

            t_0 = time.time()
            if agent.agent_type == "ship":
                if self.ship_detection_skill is None:
                    continue
                detected = self.surface_detection(agent)
            elif agent.agent_type == "air":
                if self.air_detection_skill is None:
                    continue
                detected = self.air_detection(agent)
            elif agent.agent_type == "sub":
                if self.sub_detection_skill is None:
                    continue
                detected = self.sub_detection(agent)
            else:
                raise ValueError(f"Unknown Class {type(agent)} - unable to observe.")
            tracker.USED_TIME["Observe-Detecting"] += time.time() - t_0

            if detected:
                self.mission.complete()
                missions.Track(self, agent)
                return True

        self.spread_pheromones(self.location)
        return False

    def track(self, target: Agent) -> None:
        if cs.world.world_time - self.route.creation_time > 1 or self.route.next_point() is None:
            self.generate_route(target.location)

        if self.location.distance_to_point(target.location) > 12:
            self.move_through_route()

        if self.location.distance_to_point(target.location) > 12:
            return

        if isinstance(target, Merchant):
            self.prepare_to_board(target)
        elif ((target.agent_type == "ship" and self.anti_ship_skill is not None) or
              (target.agent_type == "air" and self.anti_air_skill is not None) or
              (target.agent_type == "sub" and self.anti_sub_skill is not None)):
            self.mission.change()
            missions.Attack(self, target)
            return
        else:
            self.request_support(target)

    def prepare_to_board(self, target: Merchant) -> None:
        if self.location.distance_to_point(target.location) > 12:
            return
        else:
            successful = self.attempt_boarding(target)

        if successful and not zones.ZONE_L.polygon.contains_point(target.location):
            self.mission.complete()
            target.is_boarded(self)
            missions.Guard(self, target)

    def attempt_boarding(self, target) -> bool:
        # TODO: Get boarding parameters for escort here - for now just guaranteed success
        print(f"{self} is counter-boarding {target}")
        return True
