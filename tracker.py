import app
import constants as cs

USED_TIME = {"Weather": 0,
             "Travel": 0,
             "Track": 0,
             "Observe": 0,
             "Guard": 0,
             "Return": 0,
             "Holding": 0,
             "Attack": 0,
             "Depart": 0}


def display_times() -> None:
    global USED_TIME

    for key, value in USED_TIME.items():
        print(f"{key}: {value}")
        USED_TIME[key] = 0


class Event:
    def __init__(self, text: str, event_type: str):
        self.text = text
        self.event_type = event_type
        self.time = cs.world.world_time
        self.record_event()

    def record_event(self) -> None:
        app.save_event({'text': self.text,
                      'event_type': self.event_type,
                      'time': self.time})
