import app
import constants as cs
import json

USED_TIME = {"Weather": 0,
             "Travel": 0,
             "Track": 0,
             "Observe": 0,
             "Guard": 0,
             "Return": 0,
             "Holding": 0,
             "Attack": 0,
             "Depart": 0}

agent_data = {}


def display_times() -> None:
    global USED_TIME

    for key, value in USED_TIME.items():
        print(f"{key}: {value}")
        USED_TIME[key] = 0


def log_event(service: str, event_type):
    global agent_data
    if cs.world.world_time < 0:
        return
    service = f"{service} {event_type}"
    agent_data[service] = agent_data.get(service, 0) + 1


def export_agent_data():
    global agent_data
    print(agent_data)
    with open('logs/event_output.txt', 'w') as file:
        file.write(json.dumps(agent_data))


class Event:
    def __init__(self, text: str, event_type: str):
        self.text = text
        self.event_type = event_type
        self.time = round(cs.world.world_time, 3)
        self.record_event()

    def record_event(self) -> None:
        app.save_event({'text': self.text,
                        'event_type': self.event_type,
                        'time': self.time})
