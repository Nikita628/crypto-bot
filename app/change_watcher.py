import os
import time
import subprocess
import signal
import threading
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

class EventHandler(FileSystemEventHandler):
    def __init__(self, process_name, start_command):
        self.process_name = process_name
        self.start_command = start_command
        self.process = subprocess.Popen(start_command, shell=True, preexec_fn=os.setsid)

    def on_modified(self, event):
        if not event.is_directory:
            print(f"File {event.src_path} has been modified")
            self.restart_process()

    def restart_process(self):
        print(f"Restarting {self.process_name}")
        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
        self.process = subprocess.Popen(self.start_command, shell=True, preexec_fn=os.setsid)

def start_watching(paths, process_name, start_command):
    event_handler = EventHandler(process_name, start_command)
    observer = Observer()
    for path in paths:
        observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()

def start_process_in_thread(paths, process_name, start_command):
    thread = threading.Thread(target=start_watching, args=(paths, process_name, start_command))
    thread.daemon = True
    thread.start()
    return thread

if __name__ == "__main__":
    threads = []

    # For the first process (e.g., a bot)
    monitored_paths_bot = ["src/bot", "src/database"]
    process_name_bot = "bot"
    start_command_bot = 'python -u -m debugpy --listen "0.0.0.0:5001" src/bot/main.py'
    threads.append(start_process_in_thread(monitored_paths_bot, process_name_bot, start_command_bot))

    # For the Flask server
    monitored_paths_flask = ["src/api", "src/database"]
    process_name_flask = "flask_server"
    start_command_flask = 'python -u src/api/main.py'
    threads.append(start_process_in_thread(monitored_paths_flask, process_name_flask, start_command_flask))

    # Keep the main script running as long as the threads are alive
    try:
        while any(thread.is_alive() for thread in threads):
            time.sleep(2)
    except KeyboardInterrupt:
        print("Stopping...")
