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
            raise ValueError(f"Agent {self.agent} mission is already set to {self.agent.mission}!")
        else:
            self.agent.mission = self

        if hasattr(self.target, 'involved_missions'):
            self.target.involved_missions.append(self)

    def remove_mission_status(self) -> None:
        self.agent.mission = None

        if hasattr(self.target, 'involved_missions'):
            self.target.involved_missions.remove(self)

    @abstractmethod
    def execute(self):
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

        if issubclass(type(target), Agent):
            self.location = target.location
        else:
            self.location = target

        agent.generate_route(destination=self.location)

    def execute(self):
        outcome = self.agent.move_through_route()

        if outcome == "Reached End Of Route":
            self.agent.mission = self.next_mission(**self.next_settings)
        elif outcome == "Spent Turn Movement":
            pass
        else:
            raise ValueError(f"Unknown Outcome for Travelling - {outcome}")

    def change(self, new_mission):
        pass

    def complete(self):

        self.remove_mission_status()

    def abort(self):

        self.remove_mission_status()


class Attack(Mission):
    """
    Agents actively looking to attack another agent
    """
    def __init__(self, agent: Agent, target: Agent):
        super().__init__(agent, target)

    def execute(self):
        pass

    def change(self, new_mission):
        pass

    def complete(self):

        self.remove_mission_status()

    def abort(self):

        self.remove_mission_status()


class Track(Mission):
    """
    Agent actively following another agent, which calls in or awaits support.
    """
    def __init__(self, agent: Agent, target: Agent):
        super().__init__(agent, target)

    def execute(self):
        pass

    def change(self, new_mission):
        pass

    def complete(self):

        self.remove_mission_status()

    def abort(self):

        self.remove_mission_status()


class Observe(Mission):
    """
    Agents actively observing their surroundings to locate particular other agents
    """
    def __init__(self, agent: Agent, target: Point):
        super().__init__(agent, target)

    def execute(self):
        pass

    def change(self, new_mission):
        pass

    def complete(self):

        self.remove_mission_status()

    def abort(self):

        self.remove_mission_status()


class Guard(Mission):
    """
    Agents actively guarding a Merchant agent.
    """
    def __init__(self, agent: Agent, target: Agent):
        super().__init__(agent, target)

    def execute(self):
        pass

    def change(self, new_mission):
        pass

    def complete(self):

        self.remove_mission_status()

    def abort(self):

        self.remove_mission_status()


class Return(Mission):
    """
    Agents returning to base and then starting maintenance
    OR
    Merchants going to their target dock to deliver goods.
    """
    def __init__(self, agent: Agent, target: Point):
        super().__init__(agent, target)
        agent.generate_route(agent.base.location)

    def execute(self):
        outcome = self.agent.move_through_route()
        if outcome == "Reached End Of Route":
            self.agent.enter_base()
        elif outcome == "Spent Turn Movement":
            pass
        else:
            raise ValueError(f"Unknown Outcome for Travelling - {outcome}")

    def change(self, new_mission):
        pass

    def complete(self):
        self.remove_mission_status()

    def abort(self):

        self.remove_mission_status()


class Holding(Mission):
    """
    Agents awaiting in the holding zone awaiting further instructions
    (Hunters only)
    """
    def __init__(self, agent: Agent, target: Point):
        super().__init__(agent, target)

    def execute(self):
        pass

    def change(self, new_mission):
        pass

    def complete(self):

        self.remove_mission_status()

    def abort(self):

        self.remove_mission_status()


class Depart(Mission):
    """
    Merchants leaving the world after delivering goods - Merchants ONLY.
    """
    def __init__(self, agent: "Merchant", target: Point):
        super().__init__(agent, target)
        agent.generate_route(target)

    def execute(self):
        outcome = self.agent.move_through_route()
        if outcome == "Reached End Of Route":
            self.agent.leave_world()
        elif outcome == "Spent Turn Movement":
            pass
        else:
            raise ValueError(f"Unknown Outcome for Travelling - {outcome}")

    def change(self, new_mission):
        pass

    def complete(self):

        self.remove_mission_status()

    def abort(self):

        self.remove_mission_status()
