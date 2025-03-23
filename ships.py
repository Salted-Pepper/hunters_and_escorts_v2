import random

import constants as cs
import settings
from agents import Agent
from bases import Base
from points import Point

import missions


class Ship(Agent):
    def __init__(self, manager, model: str, base: Base, ):
        super().__init__(manager, model, base)


class Merchant(Ship):
    def __init__(self, manager, model: str):
        super().__init__(manager, model, None)
        self.entry_point = None
        self.sample_entry_point()
        self.base = self.sample_target_base()
        self.start_delivering_goods()
        self.activated = True

        self.dwt = None
        self.visibility = None
        self.initiate_model()

    def sample_entry_point(self) -> None:
        x = cs.MAX_LAT
        y = random.uniform(cs.MIN_LONG, 30)
        self.entry_point = Point(x, y)

    def sample_target_base(self) -> Base:
        return random.choices(self.manager.bases, weights=[base.agent_share
                                                           if base.agent_share is not None
                                                           else 1 / len(self.manager.bases)
                                                           for base in self.manager.bases])[0]

    def start_delivering_goods(self) -> None:
        self.location = self.entry_point
        self.mission = missions.Return(agent=self, target=self.base.location)

    def initiate_model(self) -> None:
        attribute = settings.MERCHANT_INFO[self.model]
        self.dwt = attribute["DWT"]
        self.set_speed(attribute["Speed (km/h)"])
        self.visibility = attribute["Visibility"]

    def set_speed(self, speed: float) -> None:
        self.speed_max = speed
        self.speed_cruising = speed
        self.speed_current = speed

    def complete_maintenance(self) -> None:
        self.mission = missions.Depart(agent=self, target=self.entry_point)
        self.activated = True

    def leave_world(self) -> None:
        self.mission.complete()
        self.activated = False
        self.manager.active_agents.remove(self)
