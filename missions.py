from __future__ import annotations

from abc import abstractmethod
from typing import Type, TYPE_CHECKING
import datetime
import logging
import os

import time
import tracker
import constants as cs

date = datetime.date.today()
logging.basicConfig(level=logging.DEBUG, filename=os.path.join(os.getcwd(), 'logs/mission_log_' + str(date) + '.log'),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%H:%M:%S")
logger = logging.getLogger("MISSIONS")
logger.setLevel(logging.DEBUG)

if TYPE_CHECKING:
    from agents import Agent
    from points import Point

mission_id = 0


class Mission:
    def __init__(self, agent: Agent, target: Agent | Point):
        global mission_id
        self.support_requested = False
        self.mission_id = mission_id
        mission_id += 1

        self.mission_type = None
        self.agent = agent
        self.target = target
        logger.debug(f"{cs.world.world_time} - Setting {agent} to {self} -  (previously {self.agent.previous_mission})")

        self.set_mission()

    def set_mission(self) -> None:
        if self.agent.mission is not None:
            raise ValueError(f"{self.agent} - can't set to {self}.")
        else:
            self.agent.mission = self

        if hasattr(self.target, 'involved_missions'):
            self.target.involved_missions.append(self)

    def remove_mission_status(self) -> None:
        self.agent.previous_mission = str(self.agent.mission)
        self.agent.mission = None

        if hasattr(self.target, 'involved_missions'):
            self.target.involved_missions.remove(self)

    def __repr__(self):
        return "Mission Mission"

    @abstractmethod
    def execute(self, *args):
        pass

    @abstractmethod
    def change(self):
        self.remove_mission_status()

    @abstractmethod
    def complete(self):
        pass

    @abstractmethod
    def abort(self):
        pass


class Travel(Mission):
    """
    Agents set to travel to a specific location, ignoring everything but endurance restrictions
    """
    def __init__(self, agent: Agent, target: Agent | Point, next_mission: Type[Mission], next_settings: dict):
        super().__init__(agent, target)
        self.mission_type = "travel"
        self.next_mission = next_mission
        self.next_settings = next_settings
        self.location = None

        if hasattr(target, 'location'):
            self.location = target.location
        else:
            self.location = target

        agent.generate_route(destination=self.location)

    def __repr__(self):
        return f"{self.mission_id} - Travel to {self.target}"

    def execute(self, *args) -> None:
        t_0 = time.time()
        if len(args) > 0:
            raise ValueError(f"{self} received detection {args} for Travel")

        if self.agent.route is None:
            raise ValueError(f"No route to move through for {self.agent}")

        outcome = self.agent.move_through_route()

        if outcome == "Reached End Of Route":
            self.agent.mission.complete()
            self.agent.mission = self.next_mission(**self.next_settings)
        elif outcome == "Spent Turn Movement":
            pass
        else:
            raise ValueError(f"Unknown Outcome for Travelling - {outcome}")

        tracker.USED_TIME["Travel"] += time.time() - t_0

    def change(self) -> None:
        self.remove_mission_status()

    def complete(self) -> None:
        self.remove_mission_status()

    def abort(self) -> None:
        self.remove_mission_status()

    def remove_agent_from_mission(self, agent: Agent) -> None:
        """Observe has no target agent so this is redundant"""
        pass


class Track(Mission):
    """
    Agent actively following another agent, which calls in or awaits support.
    """
    def __init__(self, agent: Agent, target: Agent):
        super().__init__(agent, target)
        self.mission_type = "track"

        logger.debug(f"{agent}")
        if agent.team == target.team:
            raise ValueError(f"Tracking same team:\n {agent} tracking {target}")

        if target.destroyed:
            raise ValueError(f"{self.agent} tracking destroyed agent  {target}")
        if target in self.agent.manager.agents_to_detect:
            self.agent.manager.agents_to_detect.remove(target)
        self.agent.speed_current = self.agent.speed_max

        try:
            self.agent.generate_route(target.location)
        except ValueError as e:
            raise ValueError(f"{self.agent} Failed to generate route to {target} -\n {e}")

    def __repr__(self):
        return f"{self.mission_id} - Tracking {self.target.service}-{self.target.agent_id}"

    def execute(self, *args) -> None:
        t_0 = time.time()

        if len(args) > 0:
            raise ValueError(f"{self.agent} received detection {args} for Travel")

        if not self.agent.check_if_valid_target(self.target):
            self.abort()
            return

        try:
            self.agent.track(self.target)
        except ValueError:
            raise ValueError(f"{self.agent} failed to track {self.target}")

        tracker.USED_TIME["Track"] += time.time() - t_0

    def change(self) -> None:
        self.remove_mission_status()
        self.agent.speed_current = self.agent.speed_cruising

    def complete(self) -> None:
        self.remove_mission_status()
        self.agent.speed_current = self.agent.speed_cruising

    def abort(self) -> None:
        self.remove_mission_status()
        self.agent.speed_current = self.agent.speed_cruising
        self.agent.mission = Observe(self.agent, self.agent.assigned_zone.sample_patrol_location())

    def remove_agent_from_mission(self, agent: Agent) -> None:
        if agent == self.target:
            self.abort()


class Attack(Mission):
    """
    Agent actively following another agent, which calls in or awaits support.
    """
    def __init__(self, agent: Agent, target: Agent):
        super().__init__(agent, target)
        self.mission_type = "attack"
        self.agent.generate_route(target.location)
        self.agent.speed_current = self.agent.speed_max
        self.execute()

    def __repr__(self):
        return f"{self.mission_id} - Attacking {self.target.service}-{self.target.agent_id}"

    def execute(self, *args) -> None:
        t_0 = time.time()

        if not self.agent.check_if_valid_target(self.target):
            self.abort()
            return
        logger.debug(f"{self.agent} is attacking {self.target}")
        try:
            self.agent.attempt_to_attack(self.target)
        except ValueError:
            raise ValueError(f"{self.agent} failed to attack {self.target}")

        tracker.USED_TIME["Attack"] += time.time() - t_0

    def change(self) -> None:
        self.remove_mission_status()
        self.agent.speed_current = self.agent.speed_cruising

    def complete(self) -> None:
        self.remove_mission_status()
        self.agent.speed_current = self.agent.speed_cruising

    def abort(self) -> None:
        self.remove_mission_status()
        self.agent.speed_current = self.agent.speed_cruising
        self.agent.return_to_base()

    def remove_agent_from_mission(self, agent: Agent) -> None:
        if agent == self.target:
            self.abort()


class Observe(Mission):
    """
    Agents actively observing their surroundings to locate particular other agents
    """
    def __init__(self, agent: Agent, target: Point):
        super().__init__(agent, target)
        self.mission_type = "observe"

        if hasattr(agent, "asw_location"):
            agent.asw_location = target

    def __repr__(self):
        return f"{self.mission_id} Observing {self.agent.assigned_zone}"

    def execute(self) -> None:
        if cs.world.world_time < 0:
            return

        t_0 = time.time()
        self.agent.observe(self.agent.manager.agents_to_detect)
        tracker.USED_TIME["Observe"] += time.time() - t_0

    def change(self) -> None:
        self.remove_mission_status()

    def complete(self) -> None:
        self.remove_mission_status()

    def abort(self) -> None:
        self.remove_mission_status()

    def remove_agent_from_mission(self, agent: Agent) -> None:
        pass


class Guard(Mission):
    """
    Agents actively guarding a Merchant agent.
    """
    def __init__(self, agent: Agent, target: Agent):
        super().__init__(agent, target)
        self.mission_type = "guard"

        if target in self.agent.manager.agents_to_detect:
            self.agent.manager.agents_to_detect.remove(target)

    def __repr__(self):
        return f"{self.mission_id} Guarding {self.target}"

    def execute(self) -> None:
        t_0 = time.time()

        self.agent.generate_route(self.target.location)
        self.agent.move_through_route()
        tracker.USED_TIME["Guard"] += time.time() - t_0

    def change(self) -> None:
        self.remove_mission_status()

    def complete(self) -> None:
        self.remove_mission_status()
        Return(self.agent, self.agent.base.location)

    def abort(self) -> None:
        if hasattr(self.target, "boarded"):
            if self.target.boarded:
                self.target.boarded = False
                self.target.team = 1
                if self.target.mission is not None:
                    self.target.mission.abort()
                Return(self.target, target=self.target.base.location)
        self.remove_mission_status()
        Return(self.agent, self.agent.base.location)

    def remove_agent_from_mission(self, agent: Agent) -> None:
        if agent == self.target:
            self.abort()
        else:
            raise ValueError(f"Agent {agent.agent_id} is not a part of {self}")


class Return(Mission):
    """
    Agents returning to base and then starting maintenance
    OR
    Merchants going to their target dock to deliver goods.
    """
    def __init__(self, agent: Agent, target: Point = None):
        super().__init__(agent, target)
        self.mission_type = "return"

        if target is None:
            target = agent.base.location
        agent.generate_route(target)

    def __repr__(self):
        return f"{self.mission_id} - Returning"

    def execute(self) -> None:
        t_0 = time.time()

        # Observe as we travel
        if self.agent.combat_type != cs.MERCHANT:
            detected_agent = self.agent.observe(self.agent.manager.agents_to_detect, traveling=True)

            if detected_agent:
                tracker.USED_TIME["Return"] += time.time() - t_0
                return

        outcome = self.agent.move_through_route()
        if outcome == "Reached End Of Route":
            self.agent.enter_base()
            self.complete()
        elif outcome == "Spent Turn Movement":
            pass
        else:
            raise ValueError(f"Unknown Outcome for Travelling - {outcome}")
        tracker.USED_TIME["Return"] += time.time() - t_0

    def change(self) -> None:
        self.remove_mission_status()

    def complete(self) -> None:
        self.remove_mission_status()

    def abort(self) -> None:
        self.remove_mission_status()

    def remove_agent_from_mission(self, agent: Agent) -> None:
        if agent == self.target:
            self.abort()
        else:
            raise ValueError(f"Agent {agent.agent_id} is not a part of {self}")


class Holding(Mission):
    """
    Agents awaiting in the holding zone awaiting further instructions
    (Hunters only)
    """
    def __init__(self, agent: Agent, target: Point):
        super().__init__(agent, target)
        self.mission_type = "hold"

    def __repr__(self):
        return f"{self.mission_id} - Holding "

    def execute(self) -> None:
        t_0 = time.time()
        self.agent.hold()
        tracker.USED_TIME["Holding"] += time.time() - t_0

    def change(self) -> None:
        self.remove_mission_status()

    def complete(self) -> None:
        self.remove_mission_status()

    def abort(self) -> None:
        self.remove_mission_status()

    def remove_agent_from_mission(self, agent: Agent) -> None:
        pass


class Depart(Mission):
    """
    Merchants leaving the world after delivering goods - Merchants ONLY.
    """
    def __init__(self, agent: "Merchant", target: Point):
        super().__init__(agent, target)
        self.mission_type = "depart"
        agent.generate_route(target)

    def __repr__(self):
        return f"{self.mission_id} - Departing to {self.target}"

    def execute(self) -> None:
        t_0 = time.time()

        outcome = self.agent.move_through_route()
        if outcome == "Reached End Of Route":
            self.agent.leave_world()
        elif outcome == "Spent Turn Movement":
            pass
        else:
            raise ValueError(f"Unknown Outcome for Travelling - {outcome}")
        tracker.USED_TIME["Depart"] += time.time() - t_0

    def change(self) -> None:
        self.remove_mission_status()

    def complete(self) -> None:
        self.remove_mission_status()

    def abort(self) -> None:
        self.remove_mission_status()

    def remove_agent_from_mission(self, agent: Agent) -> None:
        if agent == self.target:
            self.abort()
        else:
            raise ValueError(f"Agent {agent.agent_id} is not a part of {self}")
