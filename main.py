import os
import datetime

if not os.path.exists("logs"):
    os.makedirs("logs")

date = datetime.date.today()
today_logs = os.path.join(os.getcwd(), 'logs/mission_log_' + str(date) + '.log')
if os.path.exists(today_logs):
    os.remove(today_logs)

from app import start_app

start_app()
