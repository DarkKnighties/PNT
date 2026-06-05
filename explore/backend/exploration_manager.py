import subprocess
import signal

class ExplorationManager:

    def __init__(self):

        self.process = None
        self.running = False

    def start(self):

        if self.running:
            return "Exploration already running"

        self.process = subprocess.Popen(
            [
                "ros2",
                "launch",
                "explore_lite",
                "explore.launch.py"
            ]
        )

        self.running = True

        return "Exploration started"

    def stop(self):

        if not self.running:
            return "Exploration not running"

        self.process.send_signal(signal.SIGINT)

        self.process.wait()

        self.running = False

        return "Exploration stopped"

    def status(self):

        return {
            "running": self.running
        }