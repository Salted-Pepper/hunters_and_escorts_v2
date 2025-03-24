from __future__ import annotations

from abc import abstractmethod
from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from agents import Agent
    from points import Point


class Mission:
    def __init__(self, agent: Agent, target: Agent | Point):
        self.agent = agent
        self.target = target

        self.set_mission()

    def set_mission(self) -> None:
        if self.agent.mission is not None:
            raise ValueError(
                f"Agent {self.agent.agent_id} mission is already set to {self.agent.mission}, can't set to "
                f"{self}. Agent is at {self.agent.location}")
        else:
            self.agent.mission = self

        if hasattr(self.target, 'involved_missions'):
            self.target.involved_missions.append(self)

    def remove_mission_status(self) -> None:
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
        self.next_mission = next_mission
        self.next_settings = next_settings

        if hasattr(target, 'location'):
            self.location = target.location
        else:
            self.location = target

        agent.generate_route(destination=self.location)

    def __repr__(self):
        return "Mission Travel"

    def execute(self) -> None:
        outcome = self.agent.move_through_route()

        if outcome == "Reached End Of Route":
            self.agent.mission.complete()
            self.agent.mission = self.next_mission(**self.next_settings)
        elif outcome == "Spent Turn Movement":
            pass
        else:
            raise ValueError(f"Unknown Outcome for Travelling - {outcome}")

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


class Attack(Mission):
    """
    Agents actively looking to attack another agent
    """
    def __init__(self, agent: Agent, target: Agent):
        super().__init__(agent, target)

    def __repr__(self):
        return "Mission Attack"

    def execute(self) -> None:
        pass

    def change(self, new_mission) -> None:
        pass

    def complete(self) -> None:
        self.remove_mission_status()

    def abort(self) -> None:
        self.remove_mission_status()

    def remove_agent_from_mission(self, agent: Agent) -> None:
        pass


class Track(Mission):
    """
    Agent actively following another agent, which calls in or awaits support.
    """
    def __init__(self, agent: Agent, target: Agent):
        print(f"{agent.agent_id} started tracking {target.agent_id}")
        super().__init__(agent, target)

    def __repr__(self):
        return "Mission Track"

    def execute(self) -> None:
        pass

    def change(self, new_mission) -> None:
        pass

    def complete(self) -> None:
        self.remove_mission_status()

    def abort(self) -> None:
        self.remove_mission_status()

    def remove_agent_from_mission(self, agent: Agent) -> None:
        pass


class Observe(Mission):
    """
    Agents actively observing their surroundings to locate particular other agents
    """
    def __init__(self, agent: Agent, target: Point):
        super().__init__(agent, target)

    def __repr__(self):
        return "Mission Observe"

    def execute(self, agents_to_observe: list[Agent]) -> None:
        self.agent.observe(agents_to_observe)

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

    def __repr__(self):
        return "Mission Guard"

    def execute(self) -> None:
        pass

    def change(self, new_mission) -> None:
        pass

    def complete(self) -> None:
        self.remove_mission_status()

    def abort(self) -> None:
        self.remove_mission_status()

    def remove_agent_from_mission(self, agent: Agent) -> None:
        pass


class Return(Mission):
    """
    Agents returning to base and then starting maintenance
    OR
    Merchants going to their target dock to deliver goods.
    """
    def __init__(self, agent: Agent, target: Point, base=None):
        super().__init__(agent, target)
        if base is None:
            base = agent.base.location
        agent.generate_route(base)

    def __repr__(self):
        return "Mission Return"

    def execute(self) -> None:
        outcome = self.agent.move_through_route()
        if outcome == "Reached End Of Route":
            self.agent.enter_base()
        elif outcome == "Spent Turn Movement":
            pass
        else:
            raise ValueError(f"Unknown Outcome for Travelling - {outcome}")

    def change(self, new_mission) -> None:
        pass

    def complete(self) -> None:
        self.remove_mission_status()

    def abort(self) -> None:

        self.remove_mission_status()

    def remove_agent_from_mission(self, agent: Agent) -> None:
        if agent == self.agent:
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

    def __repr__(self):
        return "Mission Holding"

    def execute(self) -> None:
        pass

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
        agent.generate_route(target)

    def __repr__(self):
        return "Mission Depart"

    def execute(self) -> None:
        outcome = self.agent.move_through_route()
        if outcome == "Reached End Of Route":
            self.agent.leave_world()
        elif outcome == "Spent Turn Movement":
            pass
        else:
            raise ValueError(f"Unknown Outcome for Travelling - {outcome}")

    def change(self, new_mission) -> None:
        pass

    def complete(self) -> None:

        self.remove_mission_status()

    def abort(self) -> None:

        self.remove_mission_status()

    def remove_agent_from_mission(self, agent: Agent) -> None:
        if agent == self.agent:
            self.abort()
        else:
            raise ValueError(f"Agent {agent.agent_id} is not a part of {self}")
