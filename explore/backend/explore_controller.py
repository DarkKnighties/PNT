import os
import time
import signal
import subprocess

import rclpy

from rclpy.node import Node

from std_msgs.msg import Bool

from tf2_ros import Buffer
from tf2_ros import TransformListener

ROS_ENV = os.environ.copy()
ROS_ENV["TURTLEBOT3_MODEL"] = "waffle"


class ExploreControlNode(Node):

    def __init__(self):
        super().__init__("explore_control_node")

        self.resume_pub = self.create_publisher(
            Bool,
            "/explore/resume",
            10,
        )

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def robot_pose_available(self):
        try:
            self.tf_buffer.lookup_transform(
                "map",
                "base_link",
                rclpy.time.Time(),
            )
            return True
        except Exception:
            return False

    def wait_for_robot_pose(self, timeout=20):
        start_time = time.time()

        while time.time() - start_time < timeout:
            rclpy.spin_once(self, timeout_sec=0.1)

            if self.robot_pose_available():
                return True

        return False

    def pause(self):
        msg = Bool()
        msg.data = False

        for i in range(5):
            print(f"[EXPLORE] PAUSE publish {i+1}/5")
            self.resume_pub.publish(msg)
            time.sleep(0.05)

    def resume(self):
        msg = Bool()
        msg.data = True

        for i in range(5):
            print(f"[EXPLORE] RESUME publish {i+1}/5")
            self.resume_pub.publish(msg)
            time.sleep(0.05)


class ExploreController:

    def __init__(self):
        if not rclpy.ok():
            rclpy.init(args=None)

        self.node = ExploreControlNode()
        self.process = None
        self.launched = False
        self.running = False

    def process_alive(self):
        if self.process is None:
            return False
        return self.process.poll() is None

    def launch(self):
        if self.launched:
            print(
                "[EXPLORE] launch() ignored "
                "(already launched)"
            )
            return True

        print()
        print("========== EXPLORE LAUNCH ==========")
        print("Checking Robot Pose...")

        if not self.node.wait_for_robot_pose():
            print("Robot pose unavailable")
            return False

        print("Robot pose available")

        self.process = subprocess.Popen(
            [
                "ros2",
                "launch",
                "explore_lite",
                "explore.launch.py",
            ],
            env=ROS_ENV,
        )

        print(f"[EXPLORE] PID = {self.process.pid}")

        self.launched = True
        time.sleep(3)

        print(
            f"[EXPLORE] alive = "
            f"{self.process_alive()}"
        )

        return True

    def enable(self):
        print()
        print("========== ENABLE ==========")
        print(
            f"launched={self.launched} "
            f"running={self.running}"
        )

        if self.process is not None:
            poll = self.process.poll()
            print(f"process.poll()={poll}")

            if poll is not None:
                print("[EXPLORE] process exited")
                self.process = None
                self.launched = False
                self.running = False

        if not self.launched:
            success = self.launch()
            print(f"launch returned {success}")

            if not success:
                return False

            self.running = True
            return True

        print("[EXPLORE] sending resume")
        self.node.resume()

        print(
            f"[EXPLORE] alive after resume = "
            f"{self.process_alive()}"
        )

        self.running = True
        return True

    def disable(self):
        print()
        print("========== DISABLE ==========")
        print(
            f"launched={self.launched} "
            f"running={self.running}"
        )

        if not self.launched:
            return

        if self.process is not None:
            print(
                f"process.poll()="
                f"{self.process.poll()}"
            )

        print("[EXPLORE] sending pause")
        self.node.pause()

        print(
            f"[EXPLORE] alive after pause = "
            f"{self.process_alive()}"
        )

        self.running = False

    def shutdown(self):
        print()
        print("========== SHUTDOWN ==========")

        if not self.launched:
            return

        self.disable()

        try:
            if self.process:
                print("[EXPLORE] SIGINT")
                self.process.send_signal(signal.SIGINT)
                self.process.wait(timeout=5)
        except Exception as e:
            print(f"[EXPLORE] shutdown error: {e}")

            try:
                self.process.kill()
            except Exception:
                pass

        self.process = None
        self.launched = False
        self.running = False

    def status(self):
        return {
            "launched": self.launched,
            "running": self.running,
            "process_alive": self.process_alive(),
        }

