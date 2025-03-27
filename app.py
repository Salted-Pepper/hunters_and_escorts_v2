import time

import settings
from website import create_app
from flask_socketio import SocketIO
import webbrowser

import constants as cs
from world import World

app = create_app()
socket = SocketIO(app)


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
    if not cs.simulation_running:
        socket.start_background_task(check_if_simulating)


@socket.on('start')
def start_simulation():
    cs.simulation_running = True
    cs.world.time_delta = settings.time_delta
    settings.simulation_end_time += settings.simulation_period


def take_time_step(world: World):
    global socket
    if world.world_time >= settings.simulation_end_time:
        cs.simulation_running = False
    world.simulate_step()
    agents = world.all_agents
    socket.emit('update_plot', [agent.to_dict() for agent in agents])
    socket.emit('update_time', world.world_time)


def send_log(event: object):
    # TODO: Push Logs Through this
    global socket
    socket.emit('update_logs', event)


def start_app():
    global socket
    set_up_simulation()
    webbrowser.open("http://127.0.0.1:5000/settings")
    socket.run(app, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)



