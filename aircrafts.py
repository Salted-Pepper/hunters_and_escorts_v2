from agents import Agent
from bases import Base


class Aircraft(Agent):
    def __init__(self, manager, model: str, base: Base):
        super().__init__(manager, model, base)

    def initiate_model(self) -> None:
        pass

    def surface_detection(self, agent: Agent) -> bool:
        pass

    def air_detection(self, agent: Agent) -> bool:
        pass

    def sub_detection(self, agent: Agent) -> bool:
        pass

    def observe(self, agents: list[Agent]) -> None:
        pass
