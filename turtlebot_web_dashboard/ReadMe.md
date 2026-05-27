# 🤖 TurtleBot3 Web Control Dashboard with Camera Streaming

### Beginner-Friendly ROS2 Humble + Gazebo + Web Robotics Project

> Control a simulated TurtleBot3 robot directly from a browser using keyboard teleoperation, live camera streaming, WebSockets, ROS2 topics, and Gazebo simulation.

---

# 📖 Table of Contents

1. Project Overview  
2. Final System Architecture  
3. Technologies Used  
4. Installation Guide  
5. Folder Structure  
6. Source Code  
7. Launch Instructions  
8. System Workflow  
9. Debugging Commands  
10. Troubleshooting  
11. Future Improvements  

---

# 1. Project Overview

This project creates a robotics web dashboard for a TurtleBot3 Waffle robot using:

- ROS2 Humble
- Gazebo
- rosbridge_server
- roslibjs
- Flask
- HTML/CSS/JavaScript

Features:

- Keyboard teleoperation
- Browser-based control
- Camera feed streaming
- Emergency stop
- Velocity display
- Speed slider
- Gazebo simulation

---

# 2. Final System Architecture

```text
Browser
↓
JavaScript + roslibjs
↓
WebSocket (ws://localhost:9090)
↓
rosbridge_server
↓
ROS2 Topics
↓
Gazebo Simulation
↓
TurtleBot3 Waffle
```

---

# 3. Technologies Used

| Technology | Purpose |
|---|---|
| ROS2 Humble | Robotics middleware |
| Gazebo | Robot simulation |
| TurtleBot3 Waffle | Robot model |
| rosbridge_server | WebSocket bridge |
| roslibjs | ROS communication in browser |
| Flask | Web server |
| web_video_server | Camera streaming |

---

# 4. Installation Guide

## Install ROS2 Humble

```bash
sudo apt update
sudo apt install ros-humble-desktop-full -y
```

Add ROS2 sourcing permanently:

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

---

## Install TurtleBot3 Packages

```bash
sudo apt install \
ros-humble-turtlebot3* \
ros-humble-dynamixel-sdk \
-y
```

---

## Set TurtleBot Model

```bash
echo 'export TURTLEBOT3_MODEL=waffle' >> ~/.bashrc
source ~/.bashrc
```

---

## Install rosbridge + Video Server

```bash
sudo apt install \
ros-humble-rosbridge-suite \
ros-humble-web-video-server \
python3-flask \
-y
```

---

# 5. Folder Structure

```text
turtlebot_web_dashboard/
│
├── backend/
│   └── app.py
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── scripts/
│   └── start.sh
│
└── README.md
```

---

# 6. Source Code

## backend/app.py

```python
from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='../frontend')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## frontend/index.html

```html
<!DOCTYPE html>
<html>

<head>

    <title>TurtleBot Dashboard</title>

    <link rel="stylesheet" href="style.css">

    <script src="https://cdn.jsdelivr.net/npm/roslib/build/roslib.min.js"></script>

</head>

<body>

<div class="container">

    <h1>TurtleBot3 Web Dashboard</h1>

    <div class="status">

        <p>Connection:
            <span id="connection">Disconnected</span>
        </p>

        <p>Linear Velocity:
            <span id="linear">0.0</span>
        </p>

        <p>Angular Velocity:
            <span id="angular">0.0</span>
        </p>

    </div>

    <div class="controls">

        <p>W / ↑ → Forward</p>
        <p>S / ↓ → Backward</p>
        <p>A / ← → Rotate Left</p>
        <p>D / → → Rotate Right</p>

    </div>

    <div class="slider">

        <input
            type="range"
            id="speedSlider"
            min="0.05"
            max="1.0"
            step="0.05"
            value="0.2">

    </div>

    <button id="stopButton">
        EMERGENCY STOP
    </button>

    <div class="camera">

        <img
            src="http://localhost:8080/stream?topic=/camera/image_raw"
            id="cameraFeed">

    </div>

</div>

<script src="script.js"></script>

</body>
</html>
```

---

## frontend/style.css

```css
body {
    background: #121212;
    color: white;
    font-family: Arial;
}

.container {
    width: 80%;
    margin: auto;
}

.status,
.controls,
.slider,
.camera {
    background: #1e1e1e;
    padding: 20px;
    margin-top: 20px;
    border-radius: 10px;
}

#stopButton {
    width: 100%;
    height: 60px;
    background: red;
    color: white;
    border: none;
}
```

---

## frontend/script.js

```javascript
const ros = new ROSLIB.Ros({
    url: 'ws://localhost:9090'
});

const cmdVel = new ROSLIB.Topic({
    ros: ros,
    name: '/cmd_vel',
    messageType: 'geometry_msgs/Twist'
});

let linear = 0;
let angular = 0;

const speedSlider = document.getElementById('speedSlider');

let speed = parseFloat(speedSlider.value);

speedSlider.oninput = function () {
    speed = parseFloat(this.value);
};

function publishVelocity() {

    const twist = new ROSLIB.Message({

        linear: {
            x: linear,
            y: 0,
            z: 0
        },

        angular: {
            x: 0,
            y: 0,
            z: angular
        }

    });

    cmdVel.publish(twist);
}

document.addEventListener('keydown', function(event) {

    switch(event.key.toLowerCase()) {

        case 'w':
        case 'arrowup':
            linear = speed;
            angular = 0;
            break;

        case 's':
        case 'arrowdown':
            linear = -speed;
            angular = 0;
            break;

        case 'a':
        case 'arrowleft':
            linear = 0;
            angular = speed;
            break;

        case 'd':
        case 'arrowright':
            linear = 0;
            angular = -speed;
            break;
    }

    publishVelocity();
});

document.addEventListener('keyup', function() {

    linear = 0;
    angular = 0;

    publishVelocity();
});
```

---

# 7. Launch Instructions

## Terminal 1

```bash
export TURTLEBOT3_MODEL=waffle

ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

---

## Terminal 2

```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

---

## Terminal 3

```bash
ros2 run web_video_server web_video_server
```

---

## Terminal 4

```bash
cd turtlebot_web_dashboard/backend

python3 app.py
```

---

# 8. System Workflow

```text
Keyboard Input
↓
JavaScript Event
↓
roslibjs
↓
WebSocket
↓
rosbridge_server
↓
ROS2 Topic (/cmd_vel)
↓
Gazebo Plugin
↓
Robot Motion
```

---

# 9. Debugging Commands

## List ROS Topics

```bash
ros2 topic list
```

---

## Check Velocity Messages

```bash
ros2 topic echo /cmd_vel
```

---

## Check Camera Topics

```bash
ros2 topic list | grep camera
```

---

## Check LiDAR

```bash
ros2 topic echo /scan
```

---

## Check TF Tree

```bash
ros2 topic echo /tf
```

---

# 10. Troubleshooting

## No Camera Feed

Check:

```bash
ros2 topic list | grep camera
```

If no camera topics appear:

```bash
export TURTLEBOT3_MODEL=waffle
```

Restart Gazebo completely.

---

## WebSocket Not Connecting

Run:

```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

Check port:

```bash
netstat -tulnp | grep 9090
```

---

## Robot Not Moving

Check:

```bash
ros2 topic echo /cmd_vel
```

If Twist messages appear:
- frontend works
- Gazebo plugin issue exists

---

## Gazebo Freezing

Kill all Gazebo processes:

```bash
pkill -9 gzserver
pkill -9 gzclient
```

Restart.

---

# 11. Future Improvements

- SLAM Toolbox
- Navigation2
- Autonomous navigation
- RViz integration
- YOLO object detection
- Mobile controls
- Gamepad support
- Multi-robot simulation

---

# Final Notes

This project teaches real robotics architecture:

- ROS2 communication
- Distributed systems
- Robot teleoperation
- Simulation environments
- Web-to-robot networking

This is the foundation for:
- autonomous robots
- warehouse AMRs
- drones
- humanoid robots
