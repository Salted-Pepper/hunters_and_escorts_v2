import app
import constants as cs
import pandas as pd

USED_TIME = {"Weather": 0,
             "Travel": 0,
             "Track": 0,
             "Observe": 0,
             "Observe-Moving": 0,
             "Observe-Filtering": 0,
             "Observe-Distance": 0,
             "Observe-Validation": 0,
             "Validation-Coalition": 0,
             "Validation-China": 0,
             "Observe-Detecting": 0,
             "Observe-Tracking": 0,
             "Observe-Pheromones": 0,
             "Guard": 0,
             "Return": 0,
             "Holding": 0,
             "Attack": 0,
             "Depart": 0,
             }

agent_data = {}


def display_times() -> None:
    global USED_TIME

    for key, value in USED_TIME.items():
        print(f"{key}: {value}")
        USED_TIME[key] = 0


def log_event(service: str, model: str, event_type):
    global agent_data
    if cs.world.world_time < 0:
        return
    service = f"{service} - {model} - {event_type}"
    agent_data[service] = agent_data.get(service, 0) + 1


def export_agent_data():
    global agent_data
    if len(agent_data) == 0:
        return

    records = []
    for key, value in agent_data.items():
        service, model, event = key.split(' - ')
        records.append({'service': service,
                        'model': model,
                        'event': event,
                        'count': value})

    df = pd.DataFrame.from_records(records)
    df = df.sort_values(['service', 'event', 'model'])
    try:
        df.to_csv('logs/event_output.csv', index=False)
    except PermissionError:
        print(f"Unable to write the output CSV as the file is already open.")


class Event:
    def __init__(self, text: str, event_type: str, agent_event_name: str, attacker_event_name: str = None):
        self.agent = agent_event_name
        self.attacker = attacker_event_name
        self.text = text
        self.event_type = event_type
        self.time = round(cs.world.world_time, 3)
        self.record_event()

    def record_event(self) -> None:
        app.save_event({'text': self.text,
                        'event_type': self.event_type,
                        'time': self.time,
                        'agent_event_name': self.agent,
                        'attacker_event_name': self.attacker})
