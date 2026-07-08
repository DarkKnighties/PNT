import math
import threading
import time

import rclpy

from rclpy.action import ActionClient
from rclpy.node import Node

from geometry_msgs.msg import PoseWithCovarianceStamped
from geometry_msgs.msg import PoseStamped

from nav2_msgs.action import NavigateToPose
from action_msgs.msg import GoalStatus


class MissionController(Node):

    def __init__(self):
        super().__init__("mission_controller")
        self.get_logger().info("Initializing MissionController node...")

        self.initial_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped,
            "/initialpose",
            10
        )

        self.nav_to_pose_client = ActionClient(
            self,
            NavigateToPose,
            "/navigate_to_pose"
        )

        self._goal_handle = None
        self._goal_lock = threading.Lock()

        self.navigation_state = "idle"
        self.current_goal = None
        self.last_feedback = None
        self.last_result = None

        self._goal_owner = None
        self._route_thread = None
        self._route_stop_requested = False
        self._route_pause_sec = 0.5
        self._waypoint_id_counter = 1

        self.waypoints = []
        self.route_state = "idle"
        self.route_message = ""
        self.active_waypoint_index = None
        self.completed_waypoint_indices = []
        self.route_failure = None
        self.get_logger().info("MissionController node initialized successfully.")

    # ==========================================
    # INITIAL POSE
    # ==========================================

    def set_initial_pose(self, x, y, yaw):
        self.get_logger().info(f"Setting initial pose to: x={x}, y={y}, yaw={yaw}")
        msg = PoseWithCovarianceStamped()

        msg.header.frame_id = "map"
        msg.header.stamp = self.get_clock().now().to_msg()

        msg.pose.pose.position.x = float(x)
        msg.pose.pose.position.y = float(y)
        msg.pose.pose.position.z = 0.0

        qz = math.sin(float(yaw) / 2.0)
        qw = math.cos(float(yaw) / 2.0)

        msg.pose.pose.orientation.z = qz
        msg.pose.pose.orientation.w = qw

        msg.pose.covariance[0] = 0.25
        msg.pose.covariance[7] = 0.25
        msg.pose.covariance[35] = 0.06853891945200942

        for _ in range(5):
            self.initial_pose_pub.publish(msg)
            time.sleep(0.05)

        self.navigation_state = "localized"
        self.get_logger().info("Initial pose successfully published and local state set to localized.")

        return {
            "success": True,
            "message": "Initial pose published",
            "pose": {
                "x": float(x),
                "y": float(y),
                "yaw": float(yaw),
            }
        }

    # ==========================================
    # NAVIGATE TO GOAL
    # ==========================================

    def navigate_to(self, x, y, yaw=0.0):
        self.get_logger().info(f"navigate_to received manual request: x={x}, y={y}, yaw={yaw}")
        return self._send_navigation_goal(
            x,
            y,
            yaw,
            owner="manual"
        )

    def _send_navigation_goal(self, x, y, yaw=0.0, owner="manual"):
        self.get_logger().info(f"Sending navigation goal. Owner: {owner}. Targets: x={x}, y={y}, yaw={yaw}")
        if not self.nav_to_pose_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().error("NavigateToPose action server unavailable!")
            return {
                "success": False,
                "error": "NavigateToPose action server unavailable"
            }

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()

        goal_msg.pose.header.frame_id = "map"
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()

        goal_msg.pose.pose.position.x = float(x)
        goal_msg.pose.pose.position.y = float(y)
        goal_msg.pose.pose.position.z = 0.0

        qz = math.sin(float(yaw) / 2.0)
        qw = math.cos(float(yaw) / 2.0)

        goal_msg.pose.pose.orientation.z = qz
        goal_msg.pose.pose.orientation.w = qw

        with self._goal_lock:
            self.navigation_state = "sending"
            self.current_goal = {
                "x": float(x),
                "y": float(y),
                "yaw": float(yaw),
            }
            self.last_feedback = None
            self.last_result = None
            self._goal_owner = owner

        print("\n==================================================")
        print("SEND_GOAL START")
        print(f"OWNER: {owner}")
        print(f"TARGET: ({x:.3f}, {y:.3f}, {yaw:.3f})")
        print(f"NAV STATE BEFORE SEND: {self.navigation_state}")
        print("==================================================")

        send_goal_future = self.nav_to_pose_client.send_goal_async(
            goal_msg,
            feedback_callback=self._feedback_callback
        )

        print("SEND_GOAL: send_goal_async() returned")
        print(f"SEND_GOAL: future object = {send_goal_future}")

        timeout_time = time.time() + 5.0

        last_log = time.time()

        while (
            not send_goal_future.done() and
            time.time() < timeout_time
        ):
            if time.time() - last_log > 1.0:
                print(
                    f"SEND_GOAL: waiting for goal response "
                    f"(done={send_goal_future.done()})"
                )
                self.get_logger().info("Still waiting for action goal response from server...")
                last_log = time.time()

            time.sleep(0.05)

        print(
            f"SEND_GOAL: future completed = "
            f"{send_goal_future.done()}"
        )
        
        goal_handle = send_goal_future.result() if send_goal_future.done() else None


        print(f"SEND_GOAL: goal_handle = {goal_handle}")
        
        if goal_handle is None:
            self.get_logger().error("Action goal response timed out.")
            with self._goal_lock:
                self.navigation_state = "failed"
                self.last_result = {
                    "status": "timeout"
                }
                self._goal_owner = None
            return {
                "success": False,
                "error": "Timed out waiting for NavigateToPose response"
            }

        if not goal_handle.accepted:
            self.get_logger().warn("Action goal was REJECTED by server.")
            with self._goal_lock:
                self.navigation_state = "rejected"
                self.last_result = {
                    "status": "rejected"
                }
                self._goal_owner = None
            return {
                "success": False,
                "error": "Navigation goal rejected"
            }

        self.get_logger().info("Action goal ACCEPTED by server.")
        with self._goal_lock:
            self._goal_handle = goal_handle
            self.navigation_state = "navigating"

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_callback)

        return {
            "success": True,
            "message": "Navigation goal accepted",
            "goal": self.current_goal
        }

    def cancel_navigation(self):
        self.get_logger().info("Cancel requested for current navigation goal.")
        with self._goal_lock:
            if self._goal_handle is None:
                self.get_logger().warn("Cancel requested, but self._goal_handle is None.")
                return {
                    "success": False,
                    "error": "No active navigation goal"
                }

            cancel_future = self._goal_handle.cancel_goal_async()

        timeout_time = time.time() + 5.0

        while (
            not cancel_future.done() and
            time.time() < timeout_time
        ):
            time.sleep(0.05)

        cancel_response = cancel_future.result() if cancel_future.done() else None

        if cancel_response is None:
            self.get_logger().error("Cancel request timed out or failed to return response.")
            return {
                "success": False,
                "error": "Cancel request failed"
            }

        self.get_logger().info("Cancel response successfully processed.")
        with self._goal_lock:
            self.navigation_state = "canceled"

        return {
            "success": True,
            "message": "Navigation goal canceled"
        }

    # ==========================================
    # WAYPOINTS
    # ==========================================

    def add_waypoint(self, x, y, yaw=0.0, index=None):
        self.get_logger().info(f"Adding waypoint: x={x}, y={y}, yaw={yaw}, index={index}")
        with self._goal_lock:
            if self.route_state == "running":
                self.get_logger().warn("Rejected adding waypoint: route is currently running.")
                return {
                    "success": False,
                    "error": "Cannot edit waypoints while route is running"
                }

            waypoint = {
                "id": self._waypoint_id_counter,
                "x": float(x),
                "y": float(y),
                "yaw": float(yaw),
            }
            self._waypoint_id_counter += 1

            if index is None or index < 0 or index > len(self.waypoints):
                self.waypoints.append(waypoint)
            else:
                self.waypoints.insert(index, waypoint)

        return {
            "success": True,
            "message": "Waypoint added",
            "waypoint": waypoint,
            "route_status": self.get_route_status()
        }

    def delete_waypoint(self, index):
        self.get_logger().info(f"Deleting waypoint at index: {index}")
        with self._goal_lock:
            if self.route_state == "running":
                self.get_logger().warn("Rejected deleting waypoint: route is currently running.")
                return {
                    "success": False,
                    "error": "Cannot edit waypoints while route is running"
                }

            if index < 0 or index >= len(self.waypoints):
                self.get_logger().error(f"Invalid delete index: {index}")
                return {
                    "success": False,
                    "error": "Invalid waypoint index"
                }

            removed = self.waypoints.pop(index)

        return {
            "success": True,
            "message": "Waypoint deleted",
            "waypoint": removed,
            "route_status": self.get_route_status()
        }

    def move_waypoint_up(self, index):
        self.get_logger().info(f"Moving waypoint up from index: {index}")
        with self._goal_lock:
            if self.route_state == "running":
                return {
                    "success": False,
                    "error": "Cannot edit waypoints while route is running"
                }

            if index <= 0 or index >= len(self.waypoints):
                return {
                    "success": False,
                    "error": "Invalid waypoint index"
                }

            self.waypoints[index - 1], self.waypoints[index] = (
                self.waypoints[index],
                self.waypoints[index - 1]
            )

        return {
            "success": True,
            "message": "Waypoint moved up",
            "route_status": self.get_route_status()
        }

    def move_waypoint_down(self, index):
        self.get_logger().info(f"Moving waypoint down from index: {index}")
        with self._goal_lock:
            if self.route_state == "running":
                return {
                    "success": False,
                    "error": "Cannot edit waypoints while route is running"
                }

            if index < 0 or index >= len(self.waypoints) - 1:
                return {
                    "success": False,
                    "error": "Invalid waypoint index"
                }

            self.waypoints[index], self.waypoints[index + 1] = (
                self.waypoints[index + 1],
                self.waypoints[index]
            )

        return {
            "success": True,
            "message": "Waypoint moved down",
            "route_status": self.get_route_status()
        }

    def insert_waypoint(self, x, y, yaw=0.0, index=0):
        self.get_logger().info(f"Inserting waypoint at explicit index {index}: x={x}, y={y}")
        return self.add_waypoint(x, y, yaw, index=index)

    def clear_waypoints(self):
        self.get_logger().info("Clearing all waypoints.")
        with self._goal_lock:
            if self.route_state == "running":
                self.get_logger().warn("Rejected clearing waypoints: route is currently running.")
                return {
                    "success": False,
                    "error": "Cannot clear waypoints while route is running"
                }

            self.waypoints = []
            self.active_waypoint_index = None
            self.completed_waypoint_indices = []
            self.route_failure = None

            if self.route_state != "running":
                self.route_state = "idle"
                self.route_message = ""

        return {
            "success": True,
            "message": "Waypoints cleared",
            "route_status": self.get_route_status()
        }

    def get_waypoints(self):
        with self._goal_lock:
            return {
                "success": True,
                "waypoints": self._serialize_waypoints_locked()
            }

    # ==========================================
    # ROUTE EXECUTION
    # ==========================================

    def start_route(self):
        self.get_logger().info("start_route triggered.")
        with self._goal_lock:
            if self.route_state == "running":
                self.get_logger().warn("Route start ignored: route is already running.")
                return {
                    "success": False,
                    "error": "Route already running"
                }

            if len(self.waypoints) == 0:
                self.get_logger().error("Route start failed: no waypoints queued.")
                return {
                    "success": False,
                    "error": "No waypoints available"
                }

            self.route_state = "running"
            self.route_message = "Route execution started"
            self.active_waypoint_index = 0
            self.completed_waypoint_indices = []
            self.route_failure = None
            self._route_stop_requested = False

            self.get_logger().info(f"Spawning execution thread for total waypoints: {len(self.waypoints)}")
            self._route_thread = threading.Thread(
                target=self._execute_route,
                daemon=True
            )
            self._route_thread.start()

        return {
            "success": True,
            "message": "Route started",
            "route_status": self.get_route_status()
        }

    def stop_route(self):
        self.get_logger().info("stop_route triggered. Halting thread and cancelling active actions.")
        with self._goal_lock:
            self._route_stop_requested = True

        try:
            self.cancel_navigation()
        except Exception as e:
            self.get_logger().error(f"Error calling cancel_navigation inside stop_route: {e}")
            pass

        with self._goal_lock:
            self.waypoints = []
            self.route_state = "idle"
            self.route_message = "Route stopped"
            self.active_waypoint_index = None
            self.completed_waypoint_indices = []
            self.route_failure = None
            self._route_thread = None

        self.get_logger().info("Route stopped safely.")
        return {
            "success": True,
            "message": "Route stopped",
            "route_status": self.get_route_status()
        }

    def get_route_status(self):
        with self._goal_lock:
            return {
                "success": True,
                "route_state": self.route_state,
                "message": self.route_message,
                "active_waypoint_index": self.active_waypoint_index,
                "completed_waypoint_indices": list(self.completed_waypoint_indices),
                "failure": self.route_failure,
                "editing_locked": self.route_state == "running",
                "waypoints": self._serialize_waypoints_locked()
            }

    def _execute_route(self):
        self.get_logger().info("Route execution thread started loop.")
        while True:
            with self._goal_lock:
                if self._route_stop_requested:
                    self.get_logger().info("Execution thread detected stop request. Exiting thread.")
                    return

                if self.active_waypoint_index is None:
                    self.route_state = "idle"
                    self.route_message = ""
                    self.get_logger().info("active_waypoint_index is None. Exiting loop.")
                    return

                if self.active_waypoint_index >= len(self.waypoints):
                    self.route_state = "completed"
                    self.route_message = "Route completed"
                    self.get_logger().info("All waypoints reached successfully! Route completed.")
                    self.active_waypoint_index = None
                    self._route_thread = None
                    return

                waypoint = dict(self.waypoints[self.active_waypoint_index])
                current_index = self.active_waypoint_index

            self.get_logger().info(f"Route Thread: processing waypoint [{current_index}] id={waypoint.get('id')}")
            send_result = self._send_navigation_goal(
                waypoint["x"],
                waypoint["y"],
                waypoint.get("yaw", 0.0),
                owner="route"
            )

            if not send_result.get("success"):
                self.get_logger().error(f"Route Thread failed sending goal for waypoint [{current_index}].")
                with self._goal_lock:
                    self.route_state = "failed"
                    self.route_message = send_result.get("error", "Failed to send waypoint goal")
                    self.route_failure = {
                        "index": current_index,
                        "waypoint": waypoint,
                        "reason": send_result.get("error", "Failed to send waypoint goal")
                    }
                    self.active_waypoint_index = current_index
                    self._route_thread = None
                return

            final_state = self._wait_for_navigation_terminal_state()
            self.get_logger().info(f"Route Thread: Navigation terminal state caught: '{final_state}'")

            with self._goal_lock:
                if self._route_stop_requested:
                    self.get_logger().info("Route Thread: Stop requested while evaluating terminal state.")
                    return

                if final_state == "succeeded":
                    if current_index not in self.completed_waypoint_indices:
                        self.completed_waypoint_indices.append(current_index)

                    self.active_waypoint_index = current_index + 1
                    self.route_message = f"Waypoint {current_index + 1} reached"
                    self.get_logger().info(f"Successfully reached waypoint index {current_index}.")

                elif final_state in ["failed", "rejected", "aborted", "unknown"]:
                    self.route_state = "failed"
                    self.route_message = f"Waypoint {current_index + 1} failed"
                    self.route_failure = {
                        "index": current_index,
                        "waypoint": waypoint,
                        "reason": final_state
                    }
                    self.active_waypoint_index = current_index
                    self._route_thread = None
                    self.get_logger().error(f"Route aborted at index {current_index} due to navigation failure.")
                    return

                elif final_state == "canceled":
                    if self._route_stop_requested:
                        return
                    self.route_state = "stopped"
                    self.route_message = f"Route stopped at waypoint {current_index + 1}"
                    self.active_waypoint_index = current_index
                    self._route_thread = None
                    self.get_logger().warn(f"Route was canceled externally at index {current_index}.")
                    return

                else:
                    self.route_state = "failed"
                    self.route_message = f"Waypoint {current_index + 1} failed"
                    self.route_failure = {
                        "index": current_index,
                        "waypoint": waypoint,
                        "reason": final_state
                    }
                    self.active_waypoint_index = current_index
                    self._route_thread = None
                    self.get_logger().error(f"Route caught unhandled fallback error status '{final_state}' at index {current_index}.")
                    return

            time.sleep(self._route_pause_sec)

    def _wait_for_navigation_terminal_state(self):
        terminal_states = [
            "succeeded",
            "failed",
            "canceled",
            "rejected",
            "unknown",
            "aborted"
        ]

        while True:
            with self._goal_lock:
                if self._route_stop_requested:
                    return "canceled"

                current_state = self.navigation_state

            if current_state in terminal_states:
                return current_state

            time.sleep(0.1)

    def _serialize_waypoints_locked(self):
        serialized = []

        for i, waypoint in enumerate(self.waypoints):
            state = "pending"

            if i in self.completed_waypoint_indices:
                state = "completed"
            elif self.active_waypoint_index == i and self.route_state == "running":
                state = "current"

            serialized.append({
                "index": i,
                "id": waypoint["id"],
                "x": waypoint["x"],
                "y": waypoint["y"],
                "yaw": waypoint.get("yaw", 0.0),
                "state": state
            })

        return serialized

    # ==========================================
    # STATUS
    # ==========================================

    def get_navigation_status(self):
        with self._goal_lock:
            return {
                "state": self.navigation_state,
                "goal": self.current_goal,
                "feedback": self.last_feedback,
                "result": self.last_result,
            }

    # ==========================================
    # CALLBACKS
    # ==========================================

    def _feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback

        with self._goal_lock:
            self.last_feedback = {
                "distance_remaining": float(feedback.distance_remaining),
                "navigation_time_sec": (
                    float(feedback.navigation_time.sec) +
                    float(feedback.navigation_time.nanosec) / 1e9
                ),
            }
        self.get_logger().debug(f"Feedback: distance remaining = {feedback.distance_remaining:.2f}")

    def _result_callback(self, future):
        self.get_logger().info("Action result callback received from server.")
        result = future.result()

        if result is None:
            self.get_logger().error("Action result callback future resolved to None!")
            with self._goal_lock:
                self.navigation_state = "failed"
                self.last_result = {
                    "status": "unknown"
                }
                self._goal_handle = None
                self._goal_owner = None
            return

        status = result.status

        status_map = {
            GoalStatus.STATUS_SUCCEEDED: "succeeded",
            GoalStatus.STATUS_ABORTED: "failed",
            GoalStatus.STATUS_CANCELED: "canceled",
        }

        state = status_map.get(status, "unknown")
        self.get_logger().info(f"Action goal complete. Underlying code: {status} mapped to state: '{state}'")

        with self._goal_lock:
            self.navigation_state = state
            self.last_result = {
                "status": state
            }

            if state in ["succeeded", "failed", "canceled", "unknown"]:
                self._goal_handle = None
                self._goal_owner = None