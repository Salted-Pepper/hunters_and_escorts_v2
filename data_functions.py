from __future__ import annotations

import json
import math
import pandas as pd

import constants as cs
from ammo import Ammunition


def get_chinese_navy_data() -> dict:
    with open("data/chinese_ships.json") as file:
        data = json.load(file)

    data_dict = {}
    for model in data:
        name = model.pop("name")
        data_dict[name] = model

    cs.CHINA_NAVY_DATA = data_dict
    return data_dict


def get_chinese_aircraft_data() -> dict:
    with open("data/chinese_aircraft.json") as file:
        data = json.load(file)

    data_dict = {}
    for model in data:
        name = model.pop("name")
        data_dict[name] = model

    cs.CHINA_AIR_DATA = data_dict
    return data_dict


def get_coalition_navy_data() -> dict:
    with open("data/coalition_ships.json") as file:
        data = json.load(file)

    data_dict = {}
    for model in data:
        name = model.pop("name")
        data_dict[name] = model

    cs.COALITION_NAVY_DATA = data_dict
    return data_dict


def get_coalition_aircraft_data() -> dict:
    with open("data/coalition_aircraft.json") as file:
        data = json.load(file)

    data_dict = {}
    for model in data:
        name = model.pop("name")
        data_dict[name] = model

    cs.COALITION_AIR_DATA = data_dict
    return data_dict


def get_ammo_info(manager: str) -> list:
    with open("data/ammunition.json") as file:
        data = json.load(file)

    munition_list = []

    for ammo in data:
        if ammo["Attacker Type"] != manager:
            continue

        if ammo["World Weapon Ammunition"] == "INF":
            stock_value = math.inf
        elif ammo["World Weapon Ammunition"] == "":
            stock_value = 1000
        else:
            stock_value = int(ammo["World Weapon Ammunition"])

        munition_list.append(Ammunition(attacker=ammo["Attacker Type"],
                                        attacker_skill=ammo["Attacker Skill"].lower(),
                                        defender=ammo["Defender Type"],
                                        weapon_range=ammo["Weapon Range"],
                                        stock=stock_value))
    return munition_list


def set_attack_probabilities() -> pd.DataFrame:
    global attack_probability_data

    with open("data/attack_probabilities.json") as file:
        data = json.load(file)

    return pd.json_normalize(data)


attack_probability_data = set_attack_probabilities()


def get_attack_probabilities(attack_type, attack_skill, target_type, target_size) -> dict:
    global attack_probability_data
    df: pd.DataFrame = attack_probability_data
    if target_size is None:
        df = df[((df["Attacker Type"] == attack_type) &
                 (df["Attacker Skill"] == attack_skill) &
                 (df["Defender Type"] == target_type) &
                 (df["Defender Skill"].isna()))]
    else:
        df = df[((df["Attacker Type"] == attack_type) &
                 (df["Attacker Skill"] == attack_skill) &
                 (df["Defender Type"] == target_type) &
                 (df["Defender Skill"] == target_size))]

    if len(df) == 0:
        raise ValueError(f"{attack_type=}, "
                         f"{attack_skill=}, "
                         f"{target_type=}, "
                         f"{target_size=}")
    row = df.iloc[0]

    return {"sunk": row["Prob Sunk"],
            "ctl": row["Prob CTL"],
            "nothing": row["Prob Nothing"]}


def parse_string_input(model_data, key, default) -> str | None:
    value = model_data.get(key, default)
    if value is None:
        return value
    else:
        return value.lower()
