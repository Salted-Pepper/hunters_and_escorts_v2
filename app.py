import time
import json

import settings
from website import create_app
from flask_socketio import SocketIO
import webbrowser

import constants as cs
from world import World
from tracker import export_agent_data
import event_statistics

app = create_app()
socket = SocketIO(app)

world_data = {}
weather_data = {}
events = []


def check_if_simulating() -> None:
    print("Setting up simulation")
    while True:
        if cs.simulation_running:
            take_time_step(cs.world)
        else:
            time.sleep(1)


def set_up_simulation():
    """
    Initiates the information for the simulation, such as world creation etc.
    """
    print("Initiated World")
    world = World()
    cs.world = world


@socket.on('connect')
def handle_connect():
    global socket
    print('Client connected')
    if not cs.client_connected:
        socket.start_background_task(check_if_simulating)
        cs.client_connected = True


@socket.on('disconnect')
def handle_disconnect():
    export_agent_data()


@socket.on('start')
def start_simulation():
    cs.world.update_to_simulation_settings()
    cs.simulation_running = True
    cs.world.time_delta = settings.time_delta
    settings.simulation_end_time += settings.simulation_period
    settings.turn_periods.append(settings.simulation_end_time)
    settings.number_of_turns += 1
    cs.world.merchant_manager.generate_this_period_arrivals()


def take_time_step(world: World):
    global socket
    world.simulate_step()
    save_time_step(world)
    get_time_info(world.world_time)
    if world.world_time >= settings.simulation_end_time:
        cs.simulation_running = False
        send_ready_signal()


def save_time_step(world) -> None:
    global world_data
    global weather_data
    world_data[round(world.world_time, 2)] = {"agents": [agent.to_dict() for agent in world.all_agents],
                                              "weather": [receptor.to_dict() for
                                                          receptor in world.receptor_grid.receptors]}


def send_ready_signal():
    global socket
    export_agent_data()
    print("Finished computing simulation period.")
    socket.emit('completed_simulation', settings.simulation_end_time)
    settings.merchants_initiated = False


@socket.on('request_timestamp_data')
def get_time_info(timestamp) -> None:
    global world_data
    global events
    timestamp = round(timestamp, 3)

    if timestamp < 0:
        timestamps = world_data.keys()
        if len(timestamps) > 0:
            timestamp = max(timestamps)

    if timestamp not in world_data.keys():
        return

    time_data = world_data[timestamp]
    agents = time_data['agents']
    weather = time_data['weather']
    socket.emit('update_time', timestamp)
    if timestamp >= 0:
        socket.emit('update_plot', agents)
        socket.emit('update_weather', weather)
        socket.emit('update_logs', json.dumps(events))
        return


@socket.on('request-update-statistics')
def update_statistics(attackers, targets):
    global events
    print(f"Received request to update statistics\n{attackers}\n{targets}")
    filtered_logs = event_statistics.update_figures(events, attackers, targets)
    socket.emit('updated_statistics')
    socket.emit('filtered_logs', json.dumps(filtered_logs))


def save_event(event: dict):
    global events
    if cs.world.world_time < 0:
        return

    events.append(event)


def start_app():
    global socket
    set_up_simulation()
    webbrowser.open("http://127.0.0.1:5000/settings")
    socket.run(app, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
