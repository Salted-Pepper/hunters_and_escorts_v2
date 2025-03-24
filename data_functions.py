import json
import constants as cs


def get_chinese_navy_data() -> dict:
    with open("data/chinese_ships.json") as file:
        data = json.load(file)

    data_dict = {}
    for model in data:
        name = model.pop("name")
        data_dict[name] = model

    cs.CHINA_NAVY_DATA = data_dict
    return data_dict
