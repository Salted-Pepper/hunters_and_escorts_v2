
from points import Point
import settings


class Base:
    def __init__(self, name: str, location: Point, agent_share: float, icon: str = "Harbour"):
        self.name = name
        self.location = location
        self.agent_share = agent_share
        self.icon = icon

        self.current_served_agent = None
        self.stationed_agents = []
        self.maintenance_queue = []
        self.maintenance_prep_time = 0.1

    def __str__(self):
        return self.name

    def output_dict(self) -> dict:
        return {"name": self.name,
                "x": self.location.x,
                "y": self.location.y,
                "icon": self.icon,
                "stalled": len(self.stationed_agents)}

    def receive_agent(self, agent) -> None:
        if not agent.CTL:
            self.stationed_agents.append(agent)
            self.maintenance_queue.append(agent)

    # def start_serve_next_agent(self):
    #     if len(self.maintenance_queue) > 0:
    #         self.current_served_agent = self.maintenance_queue.pop(0)
    #     else:
    #         self.current_served_agent = None
    #
    # def finish_maintenance_agent(self):
    #     self.current_served_agent.complete_maintenance()
    #     self.start_serve_next_agent()

    def serve_agents(self) -> None:
        serving_time = settings.time_delta
        agents_to_remove = []

        for agent in self.maintenance_queue:
            if agent.remaining_maintenance_time <= serving_time:
                agent.remaining_maintenance_time = 0
                agent.complete_maintenance()
                agents_to_remove.append(agent)
            else:
                agent.remaining_maintenance_time -= serving_time

        self.maintenance_queue = [a for a in self.maintenance_queue if a not in agents_to_remove]

        # serving_time = settings.time_delta
        # while serving_time > 0:
        #     if self.current_served_agent is not None:
        #         # Either complete ship maintenance
        #         if self.current_served_agent.remaining_maintenance_time <= serving_time:
        #             serving_time = self.complete_agent_service(serving_time)
        #         # Or continue part of the ship service
        #         else:
        #             self.current_served_agent.remaining_maintenance_time -= serving_time
        #             return
        #     # No Ship is currently served, but queue existing
        #     elif len(self.maintenance_queue) > 0:
        #         self.start_serve_next_agent()
        #         serving_time -= self.maintenance_prep_time
        #     # Nothing to serve
        #     else:
        #         return

    # def complete_agent_service(self, serving_time: float) -> float:
    #     serving_time -= self.current_served_agent.remaining_maintenance_time
    #     self.current_served_agent.remaining_maintenance_time = 0
    #     self.finish_maintenance_agent()
    #     return serving_time
