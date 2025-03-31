from __future__ import annotations
from abc import abstractmethod
import copy

import settings
from bases import Base

from points import Point
import zones
import routes
import constants as cs

import missions

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
        self.color = None
        self.dwt = None

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
        self.CTL = False

        self.maintenance_time = 3*24  # TODO: Update placeholder
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
        self.mission = None
        self.involved_missions = []

        # ---- Display ----
        self.color = None

        self.initiate_model()

    def __repr__(self):
        return f"Agent {self.agent_id} of {type(self)} - on mission: {self.mission}"

    def __eq__(self, other):
        if self.agent_id == other.agent_id:
            return True
        else:
            return False

    def to_dict(self) -> dict:
        return {"x": self.location.x,
                "y": self.location.y,
                "agent_id": self.agent_id,
                "color": self.color,
                "activated": self.activated,
                "mission": str(self.mission),
                "type": str(self.manager)}  # TODO: Make sprite reliant on other property than manager

    @abstractmethod
    def initiate_model(self) -> None:
        pass

    def activate(self) -> None:
        self.activated = True
        self.manager.inactive_agents.remove(self)
        self.manager.active_agents.append(self)
        self.movement_left_in_turn = self.speed_current * settings.time_delta

    def generate_route(self, destination: Point = None) -> None:
        self.route = routes.create_route(start=self.location,
                                         end=destination, team=self.team)
        if self.route is None:
            raise ValueError(f"Failed to generate Route")

    def set_turn_movement(self) -> None:
        self.movement_left_in_turn = self.speed_current * settings.time_delta
        if self.movement_left_in_turn is None:
            raise ValueError(f"Movement set to None - {self.speed_current}, {settings.time_delta}")

    def move_through_route(self) -> str:
        if self.movement_left_in_turn is None:
            raise ValueError(f"{self} - "
                             f"Movement not set - speed: {self.speed_current} - timedelta {settings.time_delta}")
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
                self.location = next_point
                self.route.reached_point()
            else:
                part_travelled = dist_travelled / dist_to_next_point
                new_x = self.location.x + part_travelled * (next_point.x - self.location.x)
                new_y = self.location.y + part_travelled * (next_point.y - self.location.y)
                self.location = Point(new_x, new_y)
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
        required_endurance_max = (1.5 * dist_to_base)
        if required_endurance_max < self.remaining_endurance:
            return True

        base_route = routes.create_route(self.location, self.base.location, team=self.team)
        if self.remaining_endurance * (1 + cs.SAFETY_ENDURANCE) <= base_route.length:
            self.return_to_base()
            return False
        else:
            return True

    def return_to_base(self) -> None:
        self.mission.abort()
        self.mission = missions.Return(self, self.base.location)

    def enter_base(self) -> None:
        self.manager.active_agents.remove(self)
        self.manager.inactive_agents.append(self)
        self.mission.complete()
        self.activated = False
        self.base.receive_agent(self)
        self.set_up_for_maintenance()
        self.remove_from_missions()

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

    def check_if_target_in_legal_zone(self) -> None:
        pass

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

    def determine_current_zone(self) -> zones.Zone:
        """
        Checks if agent is in a zone going from the highest zone to the lowest zone.
        Only returning the highest zone.
        (highest as in smallest, that overrules, lowest as in no zone rule)
        :return:
        """
        for zone in zones.ZONES:
            if zone.check_if_agent_in_zone(self):
                return zone

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
    def observe(self, agents: list[Agent]) -> None:
        pass

    @abstractmethod
    def track(self, target: Agent) -> None:
        pass

    def go_to_patrol(self, zone: zones.Zone) -> None:
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
