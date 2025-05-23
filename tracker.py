import app
import constants as cs
import pandas as pd
import datetime
import xlsxwriter

import settings

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
events = []


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


def create_dataframe_from_events() -> pd.DataFrame:
    global events
    records = []
    for event in events:
        records.append({"country": event.agent.country,
                        "asset": event.agent.agent_type,
                        "service": event.agent.service,
                        "model": event.agent.model,
                        "period": event.sim_period,
                        "event_type": extract_event_type(event.event_type),
                        })

    return pd.DataFrame.from_records(records)


def extract_event_type(event_type: str):
    upper_event = event_type.upper()
    if "DESTROYED" in upper_event:
        return "Destroyed"
    elif "SEIZED" in upper_event:
        return "Seized"
    elif "ARRIVED" in upper_event and "DAMAGED" in upper_event:
        return "Arrived (Damaged)"
    elif "CTL" in upper_event:
        return "CTL"
    elif "ARRIVED" in upper_event:
        return "Arrived"
    else:
        print(f"Unmapped event type - {upper_event}")
        return event_type


def row_and_column_to_cell(row: int, col: int) -> str:
    """
    Format row and column as integers to cell - works up to 676 columns (ZZ)
    E.g. 3, 5 becomes F3
    :param row: Row # Starting at 0
    :param col: Col # Starting at 0 (NOTE in Excel rows start at 0 but this is to allow index matching with the writer)
    :return:
    """
    if col > 675:
        raise ValueError(f"Exceeding Column limit (675 columns).")

    alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

    first_letter = ""
    second_letter = alphabet[col % len(alphabet)]

    if col > len(alphabet):
        index = col // len(alphabet)
        first_letter = alphabet[index - 1]

    return first_letter + second_letter + str(row + 1)


def export_agent_data():
    df = create_dataframe_from_events()
    path = 'logs/event_output' + str(datetime.datetime.now()).replace(':', '.') + '.xlsx'
    num_periods = settings.number_of_turns

    workbook = xlsxwriter.Workbook(path)

    models = df["model"].unique()
    outcomes = df["event_type"].unique()

    headers = ["Service", "Model", "Outcome", "Count"]

    for period in range(num_periods):
        period_sheet = workbook.add_worksheet(f"Period {period}")
        for index, header in enumerate(headers):
            cell = row_and_column_to_cell(0, col=index)
            period_sheet.write(cell, header)

        current_row = 1

        for model in models:
            for outcome in outcomes:
                data = df[(df["model"] == model) & (df["event_type"] == outcome) & (df["period"] == period+1)]
                count = len(data.index)
                if count == 0:
                    continue

                service = data["service"].values[0]

                service_cell = row_and_column_to_cell(current_row, col=0)
                model_cell = row_and_column_to_cell(current_row, col=1)
                outcome_cell = row_and_column_to_cell(current_row, col=2)
                count_cell = row_and_column_to_cell(current_row, col=3)

                period_sheet.write(service_cell, service)
                period_sheet.write(model_cell, model)
                period_sheet.write(outcome_cell, outcome)
                period_sheet.write(count_cell, count)
                current_row += 1

    cumulative_sheet = workbook.add_worksheet("Cumulative")
    for index, header in enumerate(headers):
        cell = row_and_column_to_cell(0, col=index)
        cumulative_sheet.write(cell, header)
    current_row = 1
    for model in models:
        for outcome in outcomes:
            data = df[(df["model"] == model) & (df["event_type"] == outcome)]
            count = len(data.index)
            if count == 0:
                continue

            service = data["service"].values[0]

            service_cell = row_and_column_to_cell(current_row, col=0)
            model_cell = row_and_column_to_cell(current_row, col=1)
            outcome_cell = row_and_column_to_cell(current_row, col=2)
            count_cell = row_and_column_to_cell(current_row, col=3)

            cumulative_sheet.write(service_cell, service)
            cumulative_sheet.write(model_cell, model)
            cumulative_sheet.write(outcome_cell, outcome)
            cumulative_sheet.write(count_cell, count)
            current_row += 1

    workbook.close()


class Event:
    def __init__(self, text: str, event_type: str, agent, agent_event_name: str, attacker=None, attacker_event_name: str= None):
        self.agent = agent
        self.attacker = attacker
        self.agent_event_name = agent_event_name
        self.attacker_event_name = attacker_event_name
        self.text = text
        self.event_type = event_type
        self.time = round(cs.world.world_time, 3)
        self.sim_period = settings.number_of_turns
        self.record_event()

    def record_event(self) -> None:
        app.save_event({'text': self.text,
                        'event_type': self.event_type,
                        'time': self.time,
                        'period': self.sim_period,
                        'agent_event_name': self.agent_event_name,
                        'attacker_event_name': self.attacker_event_name})
        global events
        events.append(self)
