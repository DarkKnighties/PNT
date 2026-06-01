import subprocess
import signal
import time
import os

import rclpy

from rclpy.node import Node

from geometry_msgs.msg import Twist

# ==========================================
# ROS ENVIRONMENT VARIABLES
# ==========================================

ROS_ENV = os.environ.copy()

ROS_ENV["TURTLEBOT3_MODEL"] = "waffle"

# ==========================================
# EMERGENCY STOP NODE
# ==========================================

class StopNode(Node):

    def __init__(self):

        super().__init__('stop_node')

        self.publisher = self.create_publisher(

            Twist,
            '/cmd_vel',
            10

        )

    # ==========================================
    # STOP ROBOT
    # ==========================================

    def stop_robot(self):

        twist = Twist()

        twist.linear.x = 0.0
        twist.angular.z = 0.0

        for _ in range(20):

            self.publisher.publish(twist)

            time.sleep(0.05)

# ==========================================
# SYSTEM MANAGER
# ==========================================

class SystemManager:

    def __init__(self):

        self.processes = {}

        rclpy.init(args=None)

        self.stop_node = StopNode()

    # ==========================================
    # START GAZEBO
    # ==========================================

    def start_gazebo(self):

        print("Starting Gazebo...")

        self.processes["gazebo"] = subprocess.Popen(

            [
                "ros2",
                "launch",
                "turtlebot3_gazebo",
                "turtlebot3_world.launch.py"
            ],

            env=ROS_ENV

        )

        print("Gazebo Started")

    # ==========================================
    # START SLAM
    # ==========================================

    def start_slam(self):

        print("Starting SLAM Toolbox...")

        self.processes["slam"] = subprocess.Popen(

            [
                "ros2",
                "launch",
                "slam_toolbox",
                "online_async_launch.py",
                "use_sim_time:=True"
            ],

            env=ROS_ENV

        )

        print("SLAM Toolbox Started")

    # ==========================================
    # START NAV2
    # ==========================================

    def start_nav2(self):

        print("Starting Nav2...")

        self.processes["nav2"] = subprocess.Popen(

            [
                "ros2",
                "launch",
                "nav2_bringup",
                "navigation_launch.py",
                "use_sim_time:=True"
            ],

            env=ROS_ENV

        )

        print("Nav2 Started")

    # ==========================================
    # START ROSBRIDGE
    # ==========================================

    def start_rosbridge(self):

        print("Starting ROSBridge...")

        self.processes["rosbridge"] = subprocess.Popen(

            [
                "ros2",
                "launch",
                "rosbridge_server",
                "rosbridge_websocket_launch.xml"
            ],

            env=ROS_ENV

        )

        print("ROSBridge Started")

    # ==========================================
    # START VIDEO SERVER
    # ==========================================

    def start_video_server(self):

        print("Starting Video Server...")

        self.processes["video_server"] = subprocess.Popen(

            [
                "ros2",
                "run",
                "web_video_server",
                "web_video_server"
            ],

            env=ROS_ENV

        )

        print("Video Server Started")

    # ==========================================
    # START EXPLORATION
    # ==========================================

    def start_exploration(self):

        if "exploration" in self.processes:

            existing = self.processes["exploration"]

            if existing.poll() is None:

                print("Exploration already running")

                return

            else:

                del self.processes["exploration"]

        print("Preparing Exploration Startup...")

        time.sleep(5)

        print("Starting Exploration...")

        self.processes["exploration"] = subprocess.Popen(

            [
                "ros2",
                "launch",
                "explore_lite",
                "explore.launch.py"
            ],

            env=ROS_ENV

        )

        print("Exploration Started")

    # ==========================================
    # STOP EXPLORATION
    # ==========================================

    def stop_exploration(self):

        if "exploration" not in self.processes:

            print("Exploration not running")

            return

        print("Stopping Exploration...")

        process = self.processes["exploration"]

        try:

            process.send_signal(signal.SIGINT)

            process.wait(timeout=5)

        except subprocess.TimeoutExpired:

            print("Force killing exploration")

            process.kill()

        except Exception as e:

            print(f"Exploration shutdown error: {e}")

        finally:

            if "exploration" in self.processes:

                del self.processes["exploration"]

        print("Exploration Stopped")


    # ==========================================
    # EMERGENCY STOP
    # ==========================================

    def emergency_stop(self):

        print("\n===================================")
        print("EMERGENCY STOP ACTIVATED")
        print("===================================\n")

        # Stop exploration first

        self.stop_exploration()

        # Hard velocity stop

        self.stop_node.stop_robot()

        print("Robot Halted")

    # ==========================================
    # START ENTIRE SYSTEM
    # ==========================================

    def start_system(self):

        print("\n===================================")
        print("STARTING AUTONOMOUS ROBOTICS STACK")
        print("===================================\n")

        self.start_gazebo()

        print("Waiting for Gazebo initialization...")

        time.sleep(10)

        self.start_slam()

        print("Waiting for SLAM Toolbox...")

        time.sleep(5)

        self.start_nav2()

        print("Waiting for Nav2 activation...")

        time.sleep(10)

        self.start_rosbridge()

        time.sleep(2)

        self.start_video_server()

        time.sleep(2)

        print("\n===================================")
        print("ROBOTICS STACK READY")
        print("===================================\n")

    # ==========================================
    # SHUTDOWN ENTIRE SYSTEM
    # ==========================================

    def shutdown_system(self):

        print("\n===================================")
        print("SHUTTING DOWN SYSTEM")
        print("===================================\n")

        self.emergency_stop()

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

                print(f"{name} stopped")

            except Exception as e:

                print(f"Failed to stop {name}: {e}")

        self.processes.clear()