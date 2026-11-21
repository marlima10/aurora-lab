"""Durably deliver due reminders to each user's Jarvis inbox."""
import os
import time
from store import Store

store = Store(os.environ.get('DB_PATH', '/data/jarvis.sqlite3'))
while True:
    store.tick()
    time.sleep(15)
