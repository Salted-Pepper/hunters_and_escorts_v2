from __future__ import annotations

from abc import abstractmethod
from typing import Type, TYPE_CHECKING

import time
import tracker
import constants as cs

if TYPE_CHECKING:
    from agents import Agent
    from points import Point

mission_id = 0


class Mission:
    def __init__(self, agent: Agent, target: Agent | Point):
        global mission_id
        self.mission_id = mission_id
        mission_id += 1

        self.mission_type = None
        self.agent = agent
        self.target = target
        print(f"{cs.world.world_time} - Setting {agent} to {self}")

        self.set_mission()

    def set_mission(self) -> None:
        if self.agent.mission is not None:
            raise ValueError(
                f"{self.agent} - can't set to {self}.")
        else:
            self.agent.mission = self

        if hasattr(self.target, 'involved_missions'):
            self.target.involved_missions.append(self)

    def remove_mission_status(self) -> None:
        print(f"Closing mission {self}")
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
    def change(self, new_mission):
        pass

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

    def change(self, new_mission) -> None:
        pass

    def complete(self) -> None:
        self.remove_mission_status()

    def abort(self) -> None:
        self.remove_mission_status()

    @abstractmethod
    def remove_agent_from_mission(self, agent: Agent) -> None:
        """
        Checks what happens once the agent is removed from the mission and ensures either the mission seizes correctly
        or continues if possible.
        :param agent:
        :return:
        """
        pass


class Track(Mission):
    """
    Agent actively following another agent, which calls in or awaits support.
    """
    def __init__(self, agent: Agent, target: Agent):
        super().__init__(agent, target)
        self.mission_type = "track"
        self.agent.generate_route(target.location)
        self.agent.speed_current = self.agent.speed_max

        self.support_requested = False

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

    def change(self, new_mission) -> None:
        pass

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


class Observe(Mission):
    """
    Agents actively observing their surroundings to locate particular other agents
    """
    def __init__(self, agent: Agent, target: Point):
        super().__init__(agent, target)
        self.mission_type = "observe"

    def __repr__(self):
        return f"{self.mission_id} Observing {self.agent.assigned_zone}"

    def execute(self, agents_to_observe: list[Agent] = None) -> None:
        t_0 = time.time()

        if agents_to_observe is None:
            agents_to_observe = self.agent.manager.agents_to_detect
        self.agent.observe(agents_to_observe)

        tracker.USED_TIME["Observe"] += time.time() - t_0

    def change(self, new_mission) -> None:
        pass

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

    def __repr__(self):
        return f"{self.mission_id} Guarding {self.target}"

    def execute(self) -> None:
        t_0 = time.time()

        self.agent.generate_route(self.target.location)
        self.agent.move_through_route()
        tracker.USED_TIME["Guard"] += time.time() - t_0

    def change(self, new_mission) -> None:
        pass

    def complete(self) -> None:
        self.remove_mission_status()
        Return(self.agent, self.agent.base.location)

    def abort(self) -> None:
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
        outcome = self.agent.move_through_route()
        if outcome == "Reached End Of Route":
            self.agent.enter_base()
            self.complete()
        elif outcome == "Spent Turn Movement":
            pass
        else:
            raise ValueError(f"Unknown Outcome for Travelling - {outcome}")
        tracker.USED_TIME["Return"] += time.time() - t_0

    def change(self, new_mission) -> None:
        pass

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

        tracker.USED_TIME["Holding"] += time.time() - t_0

    def change(self, new_mission) -> None:
        pass

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

    def change(self, new_mission) -> None:
        pass

    def complete(self) -> None:
        self.remove_mission_status()

    def abort(self) -> None:
        self.remove_mission_status()

    def remove_agent_from_mission(self, agent: Agent) -> None:
        if agent == self.target:
            self.abort()
        else:
            raise ValueError(f"Agent {agent.agent_id} is not a part of {self}")
