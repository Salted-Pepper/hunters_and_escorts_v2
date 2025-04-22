from __future__ import annotations
from abc import abstractmethod
import copy
import os
import logging
import datetime

import settings
import tracker
from bases import Base

from points import Point
import zones
import routes
import constants as cs
import constant_coords as ccs

import missions
from ammo import Ammunition

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename=os.path.join(os.getcwd(), 'logs/mission_log_' + str(date) + '.log'),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("MISSIONS")
logger.setLevel(logging.DEBUG)

agent_id = 0


class Agent:
    def __init__(self, manager, model: str, base: Base):
        global agent_id
        self.agent_id = agent_id
        agent_id += 1

        self.base = base
        self.manager = manager
        self.team = manager.team
        self.country = None
        self.model = model
        self.service = None
        self.agent_type = None
        self.combat_type = None
        self.dwt = None
        self.manned = True

        # ---- Detection Parameters ----
        self.ship_visibility = None
        self.air_visibility = None
        self.sub_visibility = None

        self.ship_detection_skill = None
        self.air_detection_skill = None
        self.sub_detection_skill = None

        self.anti_ship_skill = None
        self.anti_air_skill = None
        self.anti_sub_skill = None

        self.missile_defense = None

        self.anti_ship_ammo = None
        self.anti_air_ammo = None
        self.anti_sub_ammo = None

        # ---- Movement ----
        self.assigned_zone = None
        self.legal_zones = []

        if base is None:
            self.location = None
        else:
            self.location = base.location
        self.speed_current = 0
        self.speed_cruising = None
        self.speed_max = None

        self.endurance = None
        self.remaining_endurance = None
        self.movement_left_in_turn = None

        # Routing
        self.route = None

        # ----- Agent States -----
        self.activated = False
        self.destroyed = False
        self.in_combat = False
        self.CTL = False

        self.maintenance_time = 3*24
        self.remaining_maintenance_time = 0

        # ---- Ammunition ----
        self.armed = False

        self.air_ammo_max = None
        self.surf_ammo_max = None
        self.sub_ammo_max = None

        self.air_ammo_current = None
        self.surf_ammo_current = None
        self.sub_ammo_current = None

        # ---- Mission ----
        self.previous_mission = None
        self.mission = None
        self.involved_missions = []

        # ---- Display ----
        self.icon = None

    def __repr__(self):
        return f"{self.service}-{self.agent_id} - {self.mission} - zone: {self.assigned_zone}"

    def __eq__(self, other):
        if self.agent_id == other.agent_id:
            return True
        else:
            return False

    def to_dict(self) -> dict:
        return {"x": self.location.x,
                "y": self.location.y,
                "model": self.model,
                "agent_id": self.agent_id,
                "activated": self.activated,
                "mission": str(self.mission),
                "type": str(self.manager),
                "service": self.service,
                "rem_endurance": self.remaining_endurance}  # TODO: Make sprite reliant on other property than manager

    @abstractmethod
    def initiate_model(self) -> None:
        pass

    def activate(self) -> None:
        self.activated = True
        self.manager.inactive_agents.remove(self)
        self.manager.active_agents.append(self)
        self.movement_left_in_turn = self.speed_current * settings.time_delta

    def generate_route(self, destination: Point = None) -> None:
        try:
            air = True if self.agent_type == "air" else False
            self.route = routes.create_route(start=self.location,
                                             end=destination, team=self.team, air=air)
        except ValueError as e:
            if self.agent_type != "air":
                island = ccs.check_if_point_in_shared_island(destination)
                if island is not None:
                    alternative_point = min([p for p in island.points], key=lambda x: x.distance_to_point(destination))
                    self.route = routes.create_route(start=self.location, end=alternative_point, team=self.team)
                    return
            print(f"Failed to create route for {self} to {destination}. "
                  f"Agent was assigned to {self.assigned_zone}. Team {self.team}")
            raise ValueError(e)

    def set_turn_movement(self) -> None:
        self.movement_left_in_turn = self.speed_current * settings.time_delta
        if self.movement_left_in_turn is None:
            raise ValueError(f"Movement set to None - {self.speed_current}, {settings.time_delta}")

    def move_through_route(self) -> str:
        if not zones.ZONE_A.polygon.contains_point(self.location):
            raise ValueError(f"{self} left zone of interest.")
        iterations = 0
        while self.movement_left_in_turn > 0:
            iterations += 1
            if iterations > settings.ITERATION_LIMIT:
                raise TimeoutError(f"Exceeded Iteration limit while moving through Route")

            if self.route is None:
                raise ValueError(f"No Route is set")

            next_point = self.route.next_point()
            if next_point is None:
                return "Reached End Of Route"

            dist_to_next_point = self.location.distance_to_point(next_point)
            dist_travelled = min(self.movement_left_in_turn, dist_to_next_point)

            if dist_travelled == dist_to_next_point:
                self.movement_left_in_turn -= dist_travelled
                self.remaining_endurance -= dist_travelled

                self.location = next_point
                self.route.reached_point()
            else:
                part_travelled = dist_travelled / dist_to_next_point
                new_x = self.location.x + part_travelled * (next_point.x - self.location.x)
                new_y = self.location.y + part_travelled * (next_point.y - self.location.y)
                self.location = Point(new_x, new_y)
                self.remaining_endurance -= dist_travelled
                self.movement_left_in_turn = 0
        return "Spent Turn Movement"

    def reach_and_return(self, location: Point) -> bool:
        dist_to_point = self.location.distance_to_point(location)
        dist_to_base = self.location.distance_to_point(self.base.location)
        endurance_required = dist_to_base + dist_to_point

        if endurance_required * cs.SAFETY_ENDURANCE > self.remaining_endurance:
            return False
        else:
            return True

    def can_continue(self) -> bool:
        dist_to_base = self.location.distance_to_point(self.base.location)
        required_endurance_max = (3 * dist_to_base)
        if required_endurance_max < self.remaining_endurance:
            return True

        try:
            air = True if self.agent_type == "air" else False
            base_route = routes.create_route(self.location, self.base.location, team=self.team, air=air)
        except ValueError as e:
            raise ValueError(f"Failed to create route for {self}: \n{e}")
        if self.remaining_endurance * (1 + cs.SAFETY_ENDURANCE) <= base_route.length:
            self.return_to_base()
            return False
        else:
            return True

    def return_to_base(self) -> None:
        if self.mission is not None:
            self.mission.change()
        self.mission = missions.Return(self, self.base.location)

    def enter_base(self) -> None:
        self.manager.active_agents.remove(self)
        if not self.CTL:
            self.manager.inactive_agents.append(self)
        else:
            self.create_event("CTL")
        self.mission.complete()
        self.activated = False
        self.in_combat = False
        self.base.receive_agent(self)
        self.set_up_for_maintenance()
        self.remove_from_missions()

    def create_event(self, type_of_event):
        if self.combat_type == "COALITION ESCORT":
            identifier = "Escort"
        elif self.combat_type == "COALITION AIRCRAFT":
            identifier = "Coalition Aircraft"
        elif self.combat_type == "CN NAVY":
            identifier = "Hunter"
        elif self.combat_type == "CN AIRCRAFT":
            identifier = "CN Aircraft"
        elif self.combat_type == "CN SUB":
            identifier = "CN Submarine"
        elif self.combat_type == "COALITION SUB":
            identifier = "Coalition Submarine"
        else:
            identifier = "Merchant"

        tracker.log_event(self.service, "destroyed")
        tracker.Event(text=f"{self.agent_id} - {self.service} has been {type_of_event}",
                      event_type=f"{identifier} {type_of_event}")

    def set_up_for_maintenance(self) -> None:
        self.remaining_maintenance_time = self.maintenance_time

    def complete_maintenance(self) -> None:
        self.remaining_endurance = self.endurance
        self.air_ammo_current = self.air_ammo_max
        self.surf_ammo_current = self.sub_ammo_max
        self.sub_ammo_current = self.sub_ammo_max

    def remove_from_missions(self):
        involved_missions = copy.copy(self.involved_missions)
        for mission in involved_missions:
            mission.remove_agent_from_mission(self)

        if len(self.involved_missions) > 0:
            raise ValueError(f"Did not clear all missions for {self}")

    def check_if_valid_target(self, target) -> bool:
        target_zone = target.get_current_zone()

        if self.team == 1:
            # if coalition, it depends on the r_o_e
            rules = settings.coalition_r_o_e_rules
            if zones.ZONE_L.polygon.contains_point(target.location):
                # Filters out all Chinese aircraft returning to land
                return False
            elif target_zone == zones.ZONE_P:
                target_zone = zones.ZONE_B
            elif target_zone == zones.ZONE_N:
                target_zone = zones.ZONE_H
            rule_value = rules[self.service][target_zone.name]
            logger.debug(f"Service: {self.service} - Target: {target} in {target_zone} - rule value is {rule_value}")
            if rule_value == 1:
                return True
            elif rule_value == 2:
                if target.in_combat:
                    return True
                else:
                    return False
            elif rule_value == 3:
                if not target.manned:
                    return True
                else:
                    return False
            else:
                return False

        elif self.team == 2:
            if target_zone in settings.HUNTER_ILLEGAL_ZONES:
                return False
            # if china, it depends on assigned and legal zones and targeting
            zone_rules = settings.zone_assignment_hunter
            target_rules = settings.hunter_target_rules

            valid_zone = True if (zone_rules[self.service].get(target_zone, 0) > 0 or
                                  (zone_rules[self.service][zones.ZONE_A] > 0 and
                                   target_zone not in settings.HUNTER_ILLEGAL_ZONES)) else False
            valid_target = target_rules[self.service][target.service]
            logger.debug(f"Service: {self.service} - {target} in {target_zone} - "
                         f"Valid zone: {valid_zone}, Valid Target: {valid_target}")

            if valid_zone and valid_target:
                return True
            else:
                return False
        else:
            raise ValueError(f"Undefined team {self.team}")

    def able_to_attack(self, target) -> bool:
        if target.agent_type == "ship":
            if self.anti_ship_skill is None or self.anti_ship_ammo == 0:
                return False
            else:
                return True
        elif target.agent_type == "air":
            if self.anti_air_skill is None or self.anti_air_ammo == 0:
                return False
            else:
                return True
        elif target.agent_type == "sub":
            if self.anti_sub_skill is None or self.anti_sub_ammo == 0:
                return False
            else:
                return True
        else:
            raise TypeError(f"Unaccounted agent type {target.agent_type} for {target}")

    def update_legal_zones(self) -> None:
        pass

    def allowed_to_attack(self) -> None:
        pass

    def is_destroyed(self) -> None:
        self.mission.abort()
        self.remove_from_missions()
        self.destroyed = True
        self.activated = False
        self.manager.agent_was_destroyed(self)
        print(f"{cs.world.world_time}-{self} was destroyed.")
        self.create_event(type_of_event="Destroyed")

    def check_if_in_zone(self, zone: zones.Zone) -> bool:
        """
        Check if the Agent is in a ZONE
        :param zone:
        :return:
        """
        if zone.polygon.contains_point(self.location):
            return True
        else:
            return False

    def get_current_zone(self) -> zones.Zone:
        """
        Checks if agent is in a zone going from the highest zone to the lowest zone.
        Only returning the highest zone.
        (highest as in smallest, that overrules, lowest as in no zone rule)
        :return:
        """
        for zone in zones.ZONES:
            if zone.check_if_agent_in_zone(self):
                return zone
        raise ValueError(f"No zone found for {self} at {self.location}")

    def allowed_to_enter_zone(self, zone: zones.Zone) -> bool:
        if self.team == 1:
            return settings.zone_assignment_coalition[self.service][zone]
        elif self.team == 2:
            return settings.zone_assignment_hunter[self.service][zone]
        else:
            raise ValueError(f"Unaccounted team {self.team}.")

    @abstractmethod
    def surface_detection(self, agent: Agent) -> bool:
        pass

    @abstractmethod
    def air_detection(self, agent: Agent) -> bool:
        pass

    @abstractmethod
    def sub_detection(self, agent: Agent) -> bool:
        pass

    def observe(self, agents: list[Agent], traveling=False) -> bool:
        if not traveling:
            self.make_patrol_move()

        agents = self.remove_invalid_targets(agents)

        for agent in agents:
            if not agent.activated:
                continue

            if agent.team == self.team:
                continue

            if self.location.distance_to_point(agent.location) > 700:
                continue

            if not self.check_if_valid_target(agent):
                continue

            if agent.agent_type == "ship" or agent.agent_type == cs.MERCHANT:
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

            if detected:
                self.mission.complete()
                missions.Track(self, agent)
                return True

        self.spread_pheromones(self.location)
        return False

    def remove_invalid_targets(self, agents: list) -> list:
        agents_to_remove = []

        if self.ship_detection_skill is None:
            agents_to_remove.extend([a for a in agents if a.agent_type == "ship" or a.agent_type == cs.MERCHANT])
        if self.air_detection_skill is None:
            agents_to_remove.extend([a for a in agents if a.agent_type == "air"])
        if self.sub_detection_skill is None:
            agents_to_remove.extend([a for a in agents if a.agent_type == "sub"])

        if len(agents_to_remove) > 0:
            return [a for a in agents if a not in agents_to_remove]
        else:
            return agents

    @abstractmethod
    def track(self, target: Agent) -> None:
        pass

    def request_support(self, target, boarding=False) -> None:
        if self.mission.support_requested:
            return
        # print(f"{self} is requesting support.")

        world = cs.world
        if self.team == 1:
            if boarding:
                managers = [world.tw_manager_escorts,
                            world.jp_manager_escorts,
                            world.us_manager_escorts,]
            else:
                managers = [world.tw_manager_escorts,
                            world.jp_manager_escorts,
                            world.us_manager_escorts,
                            world.coalition_manager_air]
        elif self.team == 2:
            if boarding:
                managers = [world.china_manager_navy]
            else:
                managers = [world.china_manager_navy,
                            world.china_manager_air,]
        else:
            raise ValueError(f"Invalid team {self.team}")

        # First check holding zones
        for manager in managers:
            task_taken = manager.check_if_can_take_task(target, self.mission, holding_only=True)
            if task_taken:
                self.mission.support_requested = True
                return
        # Otherwise any available agent
        for manager in managers:
            task_taken = manager.check_if_can_take_task(target, self.mission, holding_only=False)
            if task_taken:
                self.mission.support_requested = True
                return

    def go_to_patrol(self, zone: zones.Zone) -> None:
        if zone == zones.ZONE_N:
            self.mission = missions.Travel(agent=self,
                                           target=zone.sample_patrol_location(),
                                           next_mission=missions.Holding,
                                           next_settings={"agent": self,
                                                          "target": None})
        else:
            self.mission = missions.Travel(agent=self,
                                           target=zone.sample_patrol_location(),
                                           next_mission=missions.Observe,
                                           next_settings={"agent": self,
                                                          "target": None})
        self.assigned_zone = zone

    def make_patrol_move(self) -> None:
        iterations = 0
        while self.movement_left_in_turn > 0:
            iterations += 1
            if iterations > settings.ITERATION_LIMIT:
                raise TimeoutError(f"Exceeded Iteration limit in Patrol Move")
            outcome = self.move_through_route()

            if outcome == "Reached End Of Route":
                selected_location = self.select_next_patrol_location()
                self.generate_route(destination=selected_location)

    def select_next_patrol_location(self) -> Point:
        locations = [self.assigned_zone.sample_patrol_location() for _ in range(3)]

        options = {}
        for location in locations:
            receptor = cs.world.receptor_grid.get_receptor_at_location(location)

            if receptor is None:
                print(f"{self} - assigned zone: {self.assigned_zone}")
                raise ValueError(f"Failed to fetch receptor at {location}")

            if self.team == 1:
                value = receptor.coalition_pheromones
            elif self.team == 2:
                value = receptor.china_pheromones
            else:
                raise ValueError(f"Invalid Team {self.team}")

            options[location] = value
        return min(options, key=options.get)

    def hold(self) -> None:
        """
        Accounts for agents for an agent waiting in the holding zone.
        """
        self.remaining_endurance -= self.movement_left_in_turn
        self.movement_left_in_turn = 0

    def spread_pheromones(self, location) -> None:
        # TODO: Consider set up for pheromone spread (based on radius or just closest - and if so what radius)
        # radius: float
        # receptors = cs.world.receptor_grid.select_receptors_in_radius(self.location, radius)
        # receptors = [receptor for receptor in receptors if receptor.decay]
        #
        # for receptor in receptors:
        #     assigned_pheromones = (distance/radius) * cs.PHEROMONE_SPREAD

        receptor = cs.world.receptor_grid.get_receptor_at_location(location)
        assigned_pheromones = cs.PHEROMONE_SPREAD

        if self.team == 1:
            receptor.coalition_pheromones += assigned_pheromones
        elif self.team == 2:
            receptor.china_pheromones += assigned_pheromones
        else:
            raise ValueError(f"{self} - Invalid Team {self.team}")

    def set_combat_type(self) -> None:
        """
        Gets the attacker/defender type
        """
        if self.team == 1:
            if self.agent_type == "ship":
                self.combat_type = "COALITION ESCORT"
            elif self.agent_type == "sub":
                self.combat_type = "COALITION SUB"
            elif self.agent_type == "air":
                self.combat_type = "COALITION AIR"
        elif self.team == 2:
            if self.agent_type == "ship":
                self.combat_type = "CN NAVY"
            elif self.agent_type == "sub":
                self.combat_type = "CN SUB"
            elif self.agent_type == "air":
                self.combat_type = "CN AIR"
        else:
            raise ValueError(f"Invalid Team {self.team}")

    def attempt_to_attack(self, target: Agent) -> None:
        logger.debug(f"{self} is trying to attack {target}")
        if target.agent_type == "ship" or target.agent_type == cs.MERCHANT:
            if self.anti_ship_ammo == 0:
                self.abort_attack()
                return
            attacker_skill = self.anti_ship_skill
        elif target.agent_type == "air":
            if self.anti_air_ammo == 0:
                self.abort_attack()
                return
            attacker_skill = self.anti_air_skill
        elif target.agent_type == "sub":
            if self.anti_sub_ammo == 0:
                self.abort_attack()
                return
            attacker_skill = self.anti_sub_skill
        else:
            raise ValueError(f"No protocol for {target} - {target.agent_type}")

        defender_type = target.combat_type
        attacker_type = self.combat_type

        viable_ammunition = [a for a in self.manager.ammunition
                             if a.attacker.lower() == attacker_type.lower()
                             and a.defender.lower() == defender_type.lower()
                             and a.stock > 0]

        if len(viable_ammunition) == 0:
            print(f"No viable ammunition for {attacker_type} - {defender_type}")
            self.abort_attack()
            return

        ammo = self.select_ammo(viable_ammunition, target, attacker_skill)
        max_distance = ammo.range

        # Handle exception of plane being above island
        self.generate_route(target.location)
        self.move_through_route()

        if self.location.distance_to_point(target.location) < max_distance:
            self.attack(target, ammo, attacker_skill)

    def abort_attack(self):
        logger.debug(f"{self} is aborting attack on {self.mission.target}")
        self.mission.abort()

    @staticmethod
    def select_ammo(options: list, target: Agent, attacker_skill: str) -> Ammunition:
        if target.combat_type == cs.MERCHANT:
            options = [a for a in options if a.attacker_skill.lower() == cs.ATT_BASIC]
            return options[0]
        else:
            if attacker_skill == cs.ATT_BASIC:
                filtered_options = [a for a in options if a.attacker_skill.lower() == cs.ATT_BASIC]
            else:
                filtered_options = options
            if len(filtered_options) == 0:
                raise ValueError(f"Failed to select ammo: {options} - {target} - {attacker_skill}")
            return filtered_options[0]

    @abstractmethod
    def attack(self, target, ammo, attacker_skill) -> None:
        pass
