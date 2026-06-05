import subprocess
import signal
import time
import os

import rclpy

from explore_controller import ExploreController
from stop_node import StopNode


# ==========================================
# ROS ENVIRONMENT
# ==========================================

ROS_ENV = os.environ.copy()

ROS_ENV["TURTLEBOT3_MODEL"] = "waffle"


# ==========================================
# ROBOT STACK
# ==========================================

class RobotStack:

    def __init__(self):

        self.processes = {}

        if not rclpy.ok():

            rclpy.init(args=None)

        self.stop_node = StopNode()

        self.explorer = ExploreController()

    # ==========================================
    # PROCESS LAUNCHER
    # ==========================================

    def launch_process(

        self,
        key,
        command

    ):

        if key in self.processes:

            process = self.processes[key]

            if process.poll() is None:

                print(f"{key} already running")

                return

        print(f"Starting {key}...")

        self.processes[key] = subprocess.Popen(

            command,

            env=ROS_ENV

        )

        print(f"{key} started")

    # ==========================================
    # START GAZEBO
    # ==========================================

    def start_gazebo(self):

        self.launch_process(

            "gazebo",

            [
                "ros2",
                "launch",
                "turtlebot3_gazebo",
                "turtlebot3_world.launch.py"
            ]

        )

    # ==========================================
    # START SLAM
    # ==========================================

    def start_slam(self):

        self.launch_process(

            "slam",

            [
                "ros2",
                "launch",
                "slam_toolbox",
                "online_async_launch.py",
                "use_sim_time:=True"
            ]

        )

    # ==========================================
    # START NAV2
    # ==========================================

    def start_nav2(self):

        self.launch_process(

            "nav2",

            [
                "ros2",
                "launch",
                "nav2_bringup",
                "navigation_launch.py",
                "use_sim_time:=True"
            ]

        )

    # ==========================================
    # START ROSBRIDGE
    # ==========================================

    def start_rosbridge(self):

        self.launch_process(

            "rosbridge",

            [
                "ros2",
                "launch",
                "rosbridge_server",
                "rosbridge_websocket_launch.xml"
            ]

        )

    # ==========================================
    # START VIDEO SERVER
    # ==========================================

    def start_video_server(self):

        self.launch_process(

            "video_server",

            [
                "ros2",
                "run",
                "web_video_server",
                "web_video_server"
            ]

        )

    # ==========================================
    # START SYSTEM
    # ==========================================

    def start_system(self):

        print("\n===================================")
        print("STARTING ROBOTICS STACK")
        print("===================================\n")

        self.start_gazebo()

        print("Waiting for Gazebo...")
        time.sleep(10)

        self.start_slam()

        print("Waiting for SLAM Toolbox...")
        time.sleep(5)

        self.start_nav2()

        print("Waiting for Nav2...")
        time.sleep(10)

        self.start_rosbridge()

        time.sleep(2)

        self.start_video_server()

        time.sleep(2)

        print("\n===================================")
        print("STACK READY")
        print("===================================\n")

    # ==========================================
    # AUTONOMOUS MODE
    # ==========================================

    def enable_autonomy(self):

        print("\nAUTONOMOUS MODE ENABLED\n")

        self.explorer.enable()

    # ==========================================
    # TELEOP MODE
    # ==========================================

    def disable_autonomy(self):

        print("\nAUTONOMOUS MODE DISABLED\n")

        self.explorer.disable()

        self.stop_node.stop_robot()

    # ==========================================
    # EMERGENCY STOP
    # ==========================================

    def emergency_stop(self):

        print("\n===================================")
        print("EMERGENCY STOP")
        print("===================================\n")

        self.disable_autonomy()

        self.stop_node.emergency_stop()

    # ==========================================
    # STATUS
    # ==========================================

    def get_status(self):

        return {

            "exploration": self.explorer.status(),

            "gazebo":

                "gazebo" in self.processes and
                self.processes["gazebo"].poll() is None,

            "slam":

                "slam" in self.processes and
                self.processes["slam"].poll() is None,

            "nav2":

                "nav2" in self.processes and
                self.processes["nav2"].poll() is None,

            "rosbridge":

                "rosbridge" in self.processes and
                self.processes["rosbridge"].poll() is None,

            "video_server":

                "video_server" in self.processes and
                self.processes["video_server"].poll() is None

        }

    # ==========================================
    # SHUTDOWN
    # ==========================================

    def shutdown_system(self):

        print("\n===================================")
        print("SYSTEM SHUTDOWN")
        print("===================================\n")

        self.emergency_stop()

        self.explorer.shutdown()

        shutdown_order = [

            "video_server",
            "rosbridge",
            "nav2",
            "slam",
            "gazebo"

        ]

        for name in shutdown_order:

            if name not in self.processes:

                continue

            process = self.processes[name]

            print(f"Stopping {name}...")

            try:

                process.send_signal(signal.SIGINT)

                process.wait(timeout=5)

            except Exception as e:

                print(

                    f"Failed to stop {name}: {e}"

                )

        self.processes.clear()

        try:

            rclpy.shutdown()

        except Exception:

            pass

        print("\nSYSTEM OFFLINE\n")