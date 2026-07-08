import subprocess
import signal
import time
import os
import threading

import rclpy
from rclpy.executors import MultiThreadedExecutor

from explore_controller import ExploreController
from stop_node import StopNode
from mission_controller import MissionController



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

        self.mission = MissionController()

        # ==========================================
        # ROS EXECUTOR
        # ==========================================

        self.executor = MultiThreadedExecutor()

        self.executor.add_node(self.stop_node)
        self.executor.add_node(self.explorer.node)
        self.executor.add_node(self.mission)

        self.executor_thread = threading.Thread(
            target=self.executor.spin,
            daemon=True
        )

        self.executor_thread.start()

        # ==========================================
        # MISSION MODE STATE
        # ==========================================

        self.loaded_map = None

        self.localization_active = False

        self.map_server_running = False

        self.amcl_running = False


    # ==========================================
    # SET INITIAL POSE
    # ==========================================

    def set_initial_pose(self, x, y, yaw):

        result = self.mission.set_initial_pose(x, y, yaw)

        if result.get("success"):
            self.localization_active = True
            self.amcl_running = True

        return result

    # ==========================================
    # NAVIGATE TO GOAL
    # ==========================================

    def navigate_to(self, x, y, yaw=0.0):

        return self.mission.navigate_to(x, y, yaw)

    # ==========================================
    # CANCEL NAVIGATION
    # ==========================================

    def cancel_navigation(self):

        return self.mission.cancel_navigation()

    # ==========================================
    # NAVIGATION STATUS
    # ==========================================

    def get_navigation_status(self):

        return self.mission.get_navigation_status()

    # ==========================================
    # WAYPOINTS
    # ==========================================

    def get_waypoints(self):

        return self.mission.get_waypoints()

    def add_waypoint(self, x, y, yaw=0.0, index=None):

        return self.mission.add_waypoint(x, y, yaw, index=index)

    def delete_waypoint(self, index):

        return self.mission.delete_waypoint(index)

    def move_waypoint_up(self, index):

        return self.mission.move_waypoint_up(index)

    def move_waypoint_down(self, index):

        return self.mission.move_waypoint_down(index)

    def insert_waypoint(self, x, y, yaw=0.0, index=0):

        return self.mission.insert_waypoint(x, y, yaw, index=index)

    def clear_waypoints(self):

        return self.mission.clear_waypoints()

    def start_route(self):

        return self.mission.start_route()

    def stop_route(self):

        return self.mission.stop_route()

    def get_route_status(self):

        return self.mission.get_route_status()

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

            env=ROS_ENV,

            start_new_session=True

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

    # STOP SLAM

    # ==========================================

    def stop_slam(self):


        if "slam" not in self.processes:

            print("SLAM Toolbox not running")

            return True

        process = self.processes["slam"]

        print("Stopping SLAM Toolbox...")

        try:

            # Kill the entire process group (ros2 launch + async_slam_toolbox_node child)

            pgid = os.getpgid(process.pid)

            os.killpg(pgid, signal.SIGINT)

            process.wait(timeout=10)

        except subprocess.TimeoutExpired:

            print(

                "SLAM Toolbox did not exit after SIGINT."

            )

            try:

                print(

                    "Force killing SLAM Toolbox..."

                )

                pgid = os.getpgid(process.pid)

                os.killpg(pgid, signal.SIGKILL)

                process.wait(timeout=5)

            except Exception as kill_error:

                print(

                    f"Failed to kill SLAM Toolbox: {kill_error}"

                )

                return False

        except Exception as e:

            print(

                f"Unexpected error stopping SLAM: {e}"

            )

            return False

        # Verify process actually died

        if process.poll() is None:

            print(

                "SLAM process still appears alive!"

            )

            return False

        # Remove from process table only after confirmed shutdown

        if "slam" in self.processes:

            del self.processes["slam"]

        print("SLAM Toolbox stopped")

        time.sleep(2)

        return True




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
    # START LOCALIZATION (AMCL)
    # ==========================================

    def start_localization(self, yaml_path):

        self.launch_process(

            "localization",

            [
                "ros2",
                "launch",
                "nav2_bringup",
                "localization_launch.py",
                f"map:={yaml_path}",
                "use_sim_time:=True"
            ]

        )

        print(f"Localization launched using: {yaml_path}")

        

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
    # LOAD MAP
    # ==========================================

    def load_map(self, map_name):

        print()
        print("===================================")
        print("MISSION MODE - LOAD MAP")
        print("===================================")

        self.disable_autonomy()

        # --------------------------------------
        # Stop SLAM Toolbox
        # --------------------------------------

        self.stop_slam()

        # --------------------------------------
        # Build YAML path
        # --------------------------------------

        maps_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "maps"
            )
        )

        yaml_path = os.path.join(
            maps_dir,
            map_name + ".yaml"
        )

        if not os.path.isfile(yaml_path):

            print(f"Map YAML not found: {yaml_path}")

            return False

        # --------------------------------------
        # Start Localization Stack
        # --------------------------------------

        self.start_localization(yaml_path)

        # --------------------------------------
        # Mission State
        # --------------------------------------

        self.loaded_map = map_name

        self.localization_active = False

        self.map_server_running = True

        self.amcl_running = True

        print()
        print("===================================")
        print("MISSION MODE READY")
        print("===================================")
        print(f"Loaded Map: {map_name}")
        print(f"YAML: {yaml_path}")

        return True


    # ==========================================
    # UNLOAD MAP
    # ==========================================

    def unload_map(self):

        print()
        print("===================================")
        print("MISSION MODE - UNLOAD MAP")
        print("===================================")

        old_map = self.loaded_map

        self.loaded_map = None

        self.localization_active = False

        self.map_server_running = False

        self.amcl_running = False

        print(f"Unloaded map: {old_map}")

        return True

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
                self.processes["video_server"].poll() is None,

            "loaded_map": self.loaded_map,

            "localization_active": self.localization_active,

            "map_server": self.map_server_running,

            "amcl": self.amcl_running,

            "navigation": self.get_navigation_status(),

            "route": self.get_route_status()

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

        try:
            self.mission.stop_route()
        except Exception:
            pass

        try:
            self.mission.cancel_navigation()
        except Exception:
            pass


        shutdown_order = [

            "video_server",
            "rosbridge",
            "localization",
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

                pgid = os.getpgid(process.pid)

                os.killpg(pgid, signal.SIGINT)

                process.wait(timeout=5)

            except subprocess.TimeoutExpired:

                print(f"{name} did not exit after SIGINT. Force killing...")

                pgid = os.getpgid(process.pid)

                os.killpg(pgid, signal.SIGKILL)

                process.wait(timeout=5)

            except Exception as e:

                print(

                    f"Failed to stop {name}: {e}"

                )

        self.processes.clear()

        try:

            self.executor.shutdown()

        except Exception:

            pass

        try:

            rclpy.shutdown()

        except Exception:

            pass

        print("\nSYSTEM OFFLINE\n")
