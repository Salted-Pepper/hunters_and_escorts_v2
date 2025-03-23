import os
if not os.path.exists("logs"):
    os.makedirs("logs")

from app import start_app

start_app()
