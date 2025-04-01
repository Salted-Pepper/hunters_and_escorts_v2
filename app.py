import time
import json

import settings
from website import create_app
from flask_socketio import SocketIO
import webbrowser

import constants as cs
from world import World

app = create_app()
socket = SocketIO(app)

agent_data = {}
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


@socket.on('start')
def start_simulation():
    cs.simulation_running = True
    cs.world.time_delta = settings.time_delta
    settings.simulation_end_time += settings.simulation_period


def take_time_step(world: World):
    global socket
    world.simulate_step()
    save_time_step(world)
    get_time_info(world.world_time)
    if world.world_time >= settings.simulation_end_time:
        cs.simulation_running = False
        send_ready_signal()


def save_time_step(world) -> None:
    global agent_data
    agent_data[world.world_time] = {"agents": [agent.to_dict() for agent in world.all_agents]}


def send_ready_signal():
    global socket
    print("Finished computing simulation period.")
    socket.emit('completed_simulation', settings.simulation_end_time)


@socket.on('request_timestamp_data')
def get_time_info(timestamp) -> None:
    global agent_data
    global events
    print(f"Requested data for {timestamp}")
    time_data = agent_data[timestamp]
    agents = time_data['agents']
    socket.emit('update_plot', agents)
    socket.emit('update_time', timestamp)
    socket.emit('update_logs', json.dumps(events))


def save_event(event: dict):
    global events
    events.append(event)


def start_app():
    global socket
    set_up_simulation()
    webbrowser.open("http://127.0.0.1:5000/settings")
    socket.run(app, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
