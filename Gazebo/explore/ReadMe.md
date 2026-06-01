# 🤖 TurtleBot3 Autonomous Exploration Dashboard

A browser-based control and monitoring dashboard for autonomous TurtleBot3 exploration using ROS2, SLAM Toolbox, Nav2, and `explore_lite`. The backend manages the entire robotics stack as a set of supervised subprocesses, while the frontend connects directly to ROS2 over WebSocket via `roslibjs`.

---

## Project Structure

```text
turtlebot_web_dashboard_screen/
├── backend/
│   ├── app.py              # Flask server — HTTP API + static file serving
│   └── system_manager.py   # Robotics stack lifecycle manager
└── frontend/
    ├── index.html          # Dashboard UI
    ├── style.css           # Dashboard styling
    └── script.js           # ROS2 WebSocket client + UI logic
```

---

## How It Works

### Backend (`app.py` + `system_manager.py`)

The Flask app is the single entry point. On startup, it immediately calls `manager.start_system()`, which boots the entire robotics stack in a fixed sequence before the HTTP server begins accepting requests.

**`SystemManager`** owns all subprocesses in a dictionary keyed by name (`"gazebo"`, `"slam"`, `"nav2"`, `"rosbridge"`, `"video_server"`, `"exploration"`). It also initialises a live `rclpy` node (`StopNode`) at construction time — this node holds a persistent `/cmd_vel` publisher used exclusively for hard velocity stops.

#### Stack Startup Sequence

`start_system()` launches processes in this strict order with deliberate sleep gaps:

| Step | Process | Wait After |
|------|---------|------------|
| 1 | Gazebo (`turtlebot3_world.launch.py`) | 10 seconds |
| 2 | SLAM Toolbox (`online_async_launch.py`, sim time) | 5 seconds |
| 3 | Nav2 (`navigation_launch.py`, sim time) | 10 seconds |
| 4 | ROSBridge WebSocket server | 2 seconds |
| 5 | Web Video Server | 2 seconds |

The waits exist because each layer depends on the one before it being fully initialised. SLAM needs Gazebo's sensor topics, Nav2 needs the map from SLAM, and ROSBridge needs the full ROS2 graph to be active before the browser can connect.

All subprocesses inherit a copy of the current environment with `TURTLEBOT3_MODEL=waffle` injected, ensuring every ROS2 node spawned uses the correct robot model.

#### Exploration Lifecycle

**Starting** (`start_exploration`):
- If an exploration process already exists and is still running (checked via `poll()`), it returns immediately — prevents duplicate launches.
- If a stale (already-exited) process entry exists, it is cleaned up first.
- Waits 5 seconds before launching `explore_lite`, giving Nav2 costmaps time to settle after any prior stop.
- Launches `explore.launch.py` from the `explore_lite` package as a new subprocess.

**Stopping** (`stop_exploration`):
- Sends `SIGINT` to the `explore_lite` process (clean ROS2 shutdown signal).
- Waits up to 5 seconds for graceful exit.
- If the process doesn't exit in time, force-kills it with `SIGKILL`.
- The `finally` block guarantees the process entry is removed from the dict regardless of how shutdown went.

#### Emergency Stop

`emergency_stop()` is a two-stage hard halt:
1. Calls `stop_exploration()` to kill the `explore_lite` process.
2. Calls `stop_node.stop_robot()`, which publishes 20 zero-velocity `Twist` messages to `/cmd_vel` at 50ms intervals (1 second total). The repetition ensures the robot's controller receives and acts on the stop command even under message drop conditions.

This is intentionally **not exposed as a dashboard button** — it is called internally by `shutdown_system()` before tearing down the stack, ensuring the robot is halted before ROS2 nodes go offline.

#### Shutdown Sequence

`shutdown_system()` first calls `emergency_stop()`, then tears down processes in reverse dependency order:

```
video_server → rosbridge → nav2 → slam → gazebo
```

Each process receives `SIGINT` with a 5-second timeout before the loop moves on. Finally, `rclpy.shutdown()` cleans up the embedded ROS2 context.

---

### Frontend (`index.html` + `script.js` + `style.css`)

The frontend is a static single-page dashboard served by Flask. It does **not** communicate with the robot through Flask after initial page load — all live robot data flows directly from the browser to ROS2 via ROSBridge WebSocket.

#### ROS2 Connection (`script.js`)

`connectROS()` creates a `ROSLIB.Ros` instance connecting to `ws://localhost:9090` (the ROSBridge port). Three events are handled:

- **`connection`** — updates the status dot to green/pulsing, sets the label to "Connected", and calls `subscribeToMap()` to begin receiving occupancy grid data.
- **`error`** — sets the dot red, updates the label.
- **`close`** — sets the dot red with "Reconnecting...", then calls `connectROS()` again after 2 seconds. This means the dashboard will automatically reconnect if ROSBridge restarts.

#### Map Rendering

`subscribeToMap()` subscribes to the `/map` topic (`nav_msgs/OccupancyGrid`). Each time the SLAM Toolbox publishes an updated map, `renderMap()` is called.

The renderer draws onto a fixed `800×800` canvas, scaling each grid cell to fill the canvas proportionally. Cell values are mapped to colours:

| Value | Meaning | Colour |
|-------|---------|--------|
| `-1` | Unknown | `#1a2a35` (dark teal) |
| `0` | Free space | `#e8f0f5` (near white) |
| `1–100` | Occupied | `#00ffff` (cyan) |

The Y-axis is flipped (`drawY = height - y`) to correct for the ROS convention where the map origin is at the bottom-left.

#### Camera Feed

The camera image is an `<img>` tag pointing to `http://localhost:8080/stream?topic=/camera/image_raw`. This is a live MJPEG stream served by the `web_video_server` node — no JavaScript polling or WebSocket is involved for video, it is handled natively by the browser.

#### Dashboard Controls

| Button | HTTP call | What happens |
|--------|-----------|--------------|
| START EXPLORATION | `GET /start_exploration` | Launches `explore_lite` (with 5s warmup) |
| STOP EXPLORATION | `GET /stop_exploration` | SIGINT → explore_lite, then SIGKILL if needed |
| SHUTDOWN SYSTEM | `GET /shutdown` | Emergency stop → reverse-order stack teardown |

Each button updates the UI status indicators immediately on click, then confirms or shows an error based on the response.

---

## Flask API Reference

| Endpoint | Method | Action | Response |
|----------|--------|--------|----------|
| `/` | GET | Serves `index.html` | HTML |
| `/<path>` | GET | Serves static frontend files | File |
| `/start_exploration` | GET | Starts `explore_lite` | `{"message": "Exploration Started"}` |
| `/stop_exploration` | GET | Stops `explore_lite` | `{"message": "Exploration Stopped"}` |
| `/emergency_stop` | GET | Hard stop (exploration + velocity zero) | `{"message": "Emergency Stop Activated"}` |
| `/shutdown` | GET | Full stack teardown | `"System Shutdown"` (plain text) |

> The `/emergency_stop` endpoint is active in the backend but not surfaced in the dashboard UI. `shutdown` calls it internally.

---

## ROS2 Topics & Services Used

| Topic / Service | Type | Direction | Used By |
|----------------|------|-----------|---------|
| `/map` | `nav_msgs/OccupancyGrid` | Subscribe | Frontend map renderer |
| `/camera/image_raw` | `sensor_msgs/Image` | Subscribe | `web_video_server` → browser |
| `/cmd_vel` | `geometry_msgs/Twist` | Publish | `StopNode` (emergency stop) |
| ROSBridge WebSocket | — | Bidirectional | `roslibjs` ↔ ROS2 |

---

## Running the Dashboard

```bash
cd turtlebot_web_dashboard_screen/backend
python3 app.py
```

Flask runs on `http://0.0.0.0:5000`. Open `http://localhost:5000` in a browser. The robotics stack starts automatically — expect approximately **30 seconds** before everything is fully initialised (the sum of all startup waits).

> **Note:** Source your ROS2 workspace before running so `ros2` commands and all packages are on the path.

```bash
source /opt/ros/humble/setup.bash
source ~/your_ws/install/setup.bash
python3 app.py
```

---

## Additional Install Requirements

Beyond the packages listed in the main README, this dashboard requires `explore_lite` for autonomous frontier exploration:

```bash
sudo apt install ros-humble-explore-lite -y
```

And the SLAM Toolbox if not already installed:

```bash
sudo apt install ros-humble-slam-toolbox -y
```

---

## Known Behaviours

**Stop then restart spins in place** — after stopping exploration, Nav2's costmaps retain stale frontier data. If restarted too quickly, `explore_lite` may issue a spin-in-place recovery instead of navigating to a new frontier. The 5-second delay in `start_exploration` mitigates this, but clearing the Nav2 costmaps explicitly after stopping (via the `/global_costmap/clear_entirely_global_costmap` service) is the more robust fix.

**Shutdown does not call `rclpy.shutdown()`** — the current `shutdown_system()` clears `self.processes` but the `rclpy.shutdown()` call was removed. This means the embedded `StopNode` context is not formally cleaned up. For a development/demo context this is fine since the process exits anyway, but it is worth noting.

**Camera feed requires Gazebo camera plugin** — the `web_video_server` will only stream if the TurtleBot3 waffle model's camera plugin is active and publishing to `/camera/image_raw`. If the feed is black, check that the topic is being published with `ros2 topic list`.