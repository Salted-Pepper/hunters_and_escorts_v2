from flask import Blueprint, render_template, request
import settings
import time
from jinja2 import Environment

import constants as cs
import constant_coords as ccs

env = Environment()
env.policies['json.dumps_kwargs'] = {'sort_keys': False}

views = Blueprint('views', __name__)

last_settings_update = None
last_zone_assignment_update = None
last_r_o_e_update = None
last_target_rule_update = None
last_oob_update = None


@views.route('/', methods=['GET', 'POST'])
def simulation():
    landmass_to_plot = [poly.output_dict() for poly in cs.world.landmasses] + [ccs.CHINA.output_dict()]
    bases_to_plot = [base.output_dict() for manager in cs.world.managers for base in manager.bases]
    data = {"plot_polygons": landmass_to_plot,
            "plot_bases": bases_to_plot,
            "min_lon": cs.MIN_LONG,
            "max_lon": cs.MAX_LONG,
            "min_lat": cs.MIN_LAT,
            "max_lat": cs.MAX_LAT,
            "agents": [agent.to_dict() for agent in cs.world.all_agents],
            }
    return render_template("simulation.html", **data)


@views.route('/settings', methods=['GET', 'POST'])
def settings_page():
    global last_settings_update

    if request.method == "POST":
        data = request.form
        iterations = data.get('iter_time')
        time_delta = data.get('time_delta')
        china_esc = data.get('china_esc')
        coalition_esc = data.get('coalition_esc')
        show_sim = data.get('show-sim')
        plot_type = data.get('receptor-type')

        print(f"Updating Settings...")
        settings.simulation_period = float(iterations)
        settings.time_delta = float(time_delta)
        settings.CHINA_ESCALATION_LEVELS = int(china_esc)
        settings.COALITION_SELECTED_LEVEL = int(coalition_esc)
        settings.PLOTTING_MODE = bool(show_sim)
        settings.RECEPTOR_PLOT_PARAMETER = plot_type

        last_settings_update = time.time()

    current_settings = {"iter_time": settings.simulation_period,
                        "time_delta": settings.time_delta,
                        "china_esc": settings.CHINA_SELECTED_LEVEL,
                        "coa_esc": settings.COALITION_SELECTED_LEVEL,
                        "show_sim": settings.PLOTTING_MODE,
                        "receptor_type": settings.RECEPTOR_PLOT_PARAMETER,
                        }

    check_if_updated(current_settings, last_settings_update)

    return render_template("settings.html", **current_settings)


@views.route('/assignment', methods=['GET', 'POST'])
def assignment():
    global last_zone_assignment_update
    current_rules = {"china": settings.zone_assignment_hunter,
                     "coalition": settings.zone_assignment_coalition}

    if request.method == "POST":
        data = request.form

        print("Updating Zone Assignment...")
        hunter_dict = settings.zone_assignment_hunter
        coalition_dict = settings.zone_assignment_coalition

        for agent in hunter_dict:
            for zone in hunter_dict[agent]:
                old_val = hunter_dict[agent][zone]
                new_val = float(data.get(f"select-{agent}-{zone}"))
                hunter_dict[agent][zone] = new_val
                if old_val != new_val:
                    print(f"Setting {agent} - {zone} to {hunter_dict[agent][zone]}")

        for agent in coalition_dict:
            for zone in coalition_dict[agent]:
                old_val = coalition_dict[agent][zone]
                new_val = float(data.get(f"select-{agent}-{zone}"))
                coalition_dict[agent][zone] = new_val
                if old_val != new_val:
                    print(f"Setting {agent} - {zone} to {coalition_dict[agent][zone]}")

        last_zone_assignment_update = time.time()

    check_if_updated(current_rules, last_zone_assignment_update)

    return render_template("assignment.html", **current_rules)


@views.route('/rules-of-engagement', methods=['GET', 'POST'])
def r_o_e():
    global last_r_o_e_update
    escalation_level = settings.COALITION_SELECTED_LEVEL
    current_rules = {'current_roe': settings.coalition_r_o_e_rules,
                     'min_roe_values': settings.min_r_o_e[escalation_level],
                     'escalation_level': escalation_level}

    if request.method == "POST":
        rules = settings.coalition_r_o_e_rules
        data = request.form

        print("Updating Rules of Engagement...")
        for agent in rules:
            for zone in rules[agent]:
                old_value = rules[agent][zone]
                new_value = int(data.get(f"select-{agent}-{zone}"))
                if old_value != new_value:
                    print(f"Settings {agent}-{zone} to {new_value}")
                rules[agent][zone] = new_value

        last_r_o_e_update = time.time()

    check_if_updated(current_rules, last_r_o_e_update)

    return render_template("r_o_e.html", **current_rules)


@views.route('/targeting', methods=['GET', 'POST'])
def targeting():
    global last_target_rule_update
    current_rules = {'target_rules': settings.hunter_target_rules}

    if request.method == "POST":
        rules = settings.hunter_target_rules
        data = request.form

        print("Updating Hunter Targeting Rules...")
        for hunter_agent in rules:
            for coa_agent in rules[hunter_agent]:
                old_value = rules[hunter_agent][coa_agent]
                new_value = data.get(f"check-{hunter_agent}-{coa_agent}")
                new_value = True if new_value == "on" else False

                if old_value != new_value:
                    print(f"Setting {hunter_agent}-{coa_agent} to {new_value}")
                rules[hunter_agent][coa_agent] = new_value

        last_target_rule_update = time.time()

    check_if_updated(current_rules, last_target_rule_update)

    return render_template("/targeting.html", **current_rules)


@views.route('/order-of-battle', methods=['GET', 'POST'])
def o_o_b():
    global last_oob_update
    current_rules = {'merchant_info': settings.MERCHANT_INFO,
                     'country_info': settings.merchant_country_distribution}

    if request.method == "POST":
        rules = settings.MERCHANT_INFO
        country_dist = settings.merchant_country_distribution
        data = request.form

        print("Updating OOB data...")
        for merchant_type in rules:
            new_value = float(data.get(f"oob-{merchant_type}"))
            old_value = rules[merchant_type]
            if new_value != old_value:
                print(f"Settings {merchant_type}- to {new_value}")
            rules[merchant_type]["arrivals"] = new_value

        for country in country_dist:
            value = float(data.get(f"select-{country}"))
            country_dist[country] = value

        normalise_country_dist()

        last_oob_update = time.time()

    check_if_updated(current_rules, last_oob_update)

    return render_template("/oob.html", **current_rules)


def check_if_updated(rule_dict, last_update) -> None:
    current_time = time.time()
    if last_update is not None and current_time - last_update < 1:
        rule_dict['update'] = True
    else:
        rule_dict['update'] = False


def normalise_country_dist():
    country_dist = settings.merchant_country_distribution
    total = sum([country_dist[c] for c in country_dist.keys()])
    for key in country_dist:
        if total > 0:
            country_dist[key] = country_dist[key] / total
        else:
            country_dist[key] = 1 / len(country_dist)
