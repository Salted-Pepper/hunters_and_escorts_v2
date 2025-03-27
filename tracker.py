import app

USED_TIME = {"Weather": 0,
             "Travel": 0,
             "Track": 0,
             "Observe": 0,
             "Guard": 0,
             "Return": 0,
             "Holding": 0,
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
        self.emit_event()

    def emit_event(self) -> None:
        app.send_log({'text': self.text,
                      'event_type': self.event_type})
