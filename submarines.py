from abc import abstractmethod

from agents import Agent
from bases import Base


class Submarine(Agent):
    def __init__(self, manager, model: str, base: Base):
        super().__init__(manager, model, base)
        self.agent_type = "sub"

    @abstractmethod
    def initiate_model(self) -> None:
        pass

    def set_agent_attributes(self) -> None:
        pass

    def surface_detection(self, agent: Agent) -> bool:
        pass

    def air_detection(self, agent: Agent) -> bool:
        pass

    def sub_detection(self, agent: Agent) -> bool:
        pass

    def observe(self, agents: list[Agent]) -> None:
        pass

    def track(self, target: Agent) -> None:
        pass

    def attempt_to_attack(self, target) -> None:
        pass

    def attack(self, target, ammo, attacker_skill) -> None:
        pass
