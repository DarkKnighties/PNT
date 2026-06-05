import time

import rclpy

from rclpy.node import Node

from geometry_msgs.msg import Twist


class StopNode(Node):

    def __init__(self):

        super().__init__("stop_node")

        self.cmd_vel_pub = self.create_publisher(
            Twist,
            "/cmd_vel",
            10
        )

    def stop_robot(self):

        twist = Twist()

        for _ in range(20):

            self.cmd_vel_pub.publish(twist)

            time.sleep(0.05)

    def emergency_stop(self):

        self.stop_robot()