from __future__ import annotations

import pandas as pd
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import settings
import constants as cs

country_palette = {"China": "indianred",
                   "USA": "marineblue",
                   "Taiwan": "forestgreen",
                   "Japan": "antiquewhite",
                   "All": "gray"}


def get_turn_bounds(turn) -> tuple[float, float]:
    min_bound = settings.turn_periods[turn - 1]
    max_bound = settings.turn_periods[turn]
    return min_bound, max_bound


def compute_by_turn_losses(df: pd.DataFrame) -> None:
    num_turns = settings.number_of_turns
    df = df.loc[df["Destroyed"]]

    records = []

    for turn in range(1, num_turns + 1):
        min_bound, max_bound = get_turn_bounds(turn)
        filtered_data = df[(df["time"] > min_bound) & (df["time"] <= max_bound)]

        for agent_type in cs.EVENT_NAMES:
            losses = len(filtered_data[filtered_data["agent_event_name"] == agent_type].index)
            if losses > 0:
                records.append({'turn': turn,
                                'agent': agent_type,
                                'losses': losses})

    data = pd.DataFrame.from_records(records)

    plt.figure(figsize=(6, 4))
    plot = sns.barplot(data, x="agent", y="losses", hue="turn")
    plot.set(xlabel="Agent Type", ylabel="Destroyed")
    plot.tick_params(axis='x', rotation=30)
    fig = plot.get_figure()
    fig.subplots_adjust(bottom=0.2)
    fig.savefig("website/static/assets/turn-losses.png")


def compute_by_country_losses(df: pd.DataFrame) -> None:
    records = []
    for country in df["Country"].unique():
        for agent_type in df["agent_type"].unique():
            count = len(df[(df["Country"] == country) & (df["agent_type"] == agent_type)].index)
            if count > 0:
                records.append({"Country": country, "losses": count, "agent_type": agent_type})

    data = pd.DataFrame.from_records(records)

    plt.figure(figsize=(6, 4))
    plot = sns.barplot(data, x="Country", y="losses", hue="agent_type")
    plot.set(xlabel="Country", ylabel="Destroyed")
    plot.tick_params(axis='x', rotation=30)
    fig = plot.get_figure()
    fig.subplots_adjust(bottom=0.2)
    fig.savefig("website/static/assets/country-losses.png")


def compute_loss_causes(df: pd.DataFrame, attackers: list[str], targets: list[str]) -> None:
    records = []

    df = df[(df["agent_event_name"].isin(targets)) &
            (df["attacker_event_name"].isin(attackers))]

    for attacker_type in df["attacker_type"].unique():
        for country in df["Attacker Country"].unique():
            count = len(df[(df["attacker_type"] == attacker_type) & 
                           (df["Attacker Country"] == country)].index)
            if count > 0:
                records.append({"attacker_type": attacker_type, "country": country, "losses": count})

    for country in df["Attacker Country"].unique():
        overall_losses = sum([r["losses"] for r in records if r["country"] == country])
        records.insert(0, {"attacker_type": "Total", "losses": overall_losses, "country": country})

    data = pd.DataFrame.from_records(records)

    plt.figure(figsize=(6, 4))
    plot = sns.barplot(data, x="attacker_type", y="losses", hue="country", palette=country_palette)
    plot.set(xlabel="Attacker Type", ylabel="Losses")
    plot.tick_params(axis='x', rotation=30)
    fig = plot.get_figure()
    fig.subplots_adjust(bottom=0.2)
    fig.savefig("website/static/assets/losses-cause.png")


def get_related_logs(events: list[dict], attackers: list[str], targets: list[str]) -> list[dict]:
    filtered_events = []
    for event in events:
        if event['agent_event_name'] in targets and event['attacker_event_name'] in attackers:
            filtered_events.append(event)

    return filtered_events


def get_agent_type(agent: str) -> str:
    if agent is None:
        return ""
    elif agent == "CN Ship" or agent == "Escort":
        return "Ship"
    elif "Submarine" in agent:
        return "Submarine"
    elif "Aircraft" in agent:
        return "Aircraft"
    else:
        return "Merchant"


def get_agent_country(row: pd.Series, agent_role) -> str:

    if agent_role == "defender":
        if row["agent_event_name"].startswith("CN"):
            return "China"

        if "TW" in row["text"]:
            return "Taiwan"
        elif "US" in row["text"]:
            return "USA"
        elif "JP" in row["text"]:
            return "Japan"
        else:
            return "Market"

    elif agent_role == "attacker":
        if row["attacker_event_name"] is None:
            return ""
        elif row["attacker_event_name"].startswith("CN"):
            return "China"

        if "TW" in row["text"]:
            return "Taiwan"
        elif "US" in row["text"]:
            return "USA"
        elif "JP" in row["text"]:
            return "Japan"
        else:
            return "Market"


def preprocess_events(events: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame.from_records(events)
    df["Destroyed"] = df['event_type'].apply(lambda x: True if "Destroyed" in x or "seized" in x else False)
    df["Country"] = df.apply(lambda x: get_agent_country(x, "defender"), axis=1)
    df["Attacker Country"] = df.apply(lambda x: get_agent_country(x, "attacker"), axis=1)
    df["agent_type"] = df["agent_event_name"].apply(get_agent_type)
    df["attacker_type"] = df["attacker_event_name"].apply(get_agent_type)

    return df


def update_figures(events: list[dict], attackers: list[str], targets: list[str]) -> None | list[dict]:
    if len(events) == 0:
        return

    df = preprocess_events(events)
    compute_by_turn_losses(df)
    compute_by_country_losses(df)
    compute_loss_causes(df, attackers, targets)
    return get_related_logs(events, attackers, targets)
