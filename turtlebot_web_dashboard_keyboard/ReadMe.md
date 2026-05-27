# ⌨️ TurtleBot3 Web Dashboard — Keyboard Control Version

### ROS2 Humble + Gazebo + Web Teleoperation System

This project creates a browser-based dashboard that controls a simulated TurtleBot3 robot using keyboard input.

Built using:
- ROS2 Humble
- Gazebo
- rosbridge_server
- roslibjs
- Flask
- HTML/CSS/JavaScript

---

# 📖 Features

- WASD keyboard control
- Arrow key support
- Real-time ROS2 communication
- Live camera streaming
- Speed slider
- Emergency stop
- Gazebo simulation
- WebSocket communication

---

# 🧠 System Architecture

```text
Keyboard Input
↓
JavaScript Event
↓
script.js
↓
roslibjs
↓
WebSocket
↓
rosbridge_server
↓
ROS2 /cmd_vel
↓
Gazebo
↓
TurtleBot3 Waffle
```

---

# 📁 Folder Structure

```text
turtlebot_web_dashboard_keyboard/
│
├── backend/
│   └── app.py
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
└── README.md
```

---

# 🚀 Launch Instructions

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
cd backend

python3 app.py
```

---

# 🌐 Open Browser

```text
http://localhost:5000
```

---

# 🎮 Controls

| Key | Action |
|---|---|
| W / ↑ | Forward |
| S / ↓ | Backward |
| A / ← | Rotate Left |
| D / → | Rotate Right |
| Space | Stop |

---

# 📄 backend/app.py

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

# 📄 frontend/index.html

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

        <p>
            Connection:
            <span id="connection">Disconnected</span>
        </p>

        <p>
            Linear Velocity:
            <span id="linear">0.0</span>
        </p>

        <p>
            Angular Velocity:
            <span id="angular">0.0</span>
        </p>

    </div>

    <div class="controls">

        <h2>Controls</h2>

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

# 📄 frontend/style.css

```css
body {
    background: #121212;
    color: white;
    font-family: Arial;
    margin: 0;
}

.container {
    width: 80%;
    margin: auto;
    padding: 20px;
}

.status,
.controls,
.slider,
.camera {
    background: #1e1e1e;
    margin-top: 20px;
    padding: 20px;
    border-radius: 10px;
}

#stopButton {
    width: 100%;
    height: 60px;
    background: red;
    border: none;
    color: white;
    font-size: 20px;
    cursor: pointer;
}

#cameraFeed {
    width: 100%;
}
```

---

# 📄 frontend/script.js

```javascript
const ros = new ROSLIB.Ros({
    url: 'ws://localhost:9090'
});

ros.on('connection', function () {
    document.getElementById('connection').innerHTML = 'Connected';
});

ros.on('error', function () {
    document.getElementById('connection').innerHTML = 'Error';
});

ros.on('close', function () {
    document.getElementById('connection').innerHTML = 'Closed';
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

    document.getElementById('linear').innerHTML = linear;
    document.getElementById('angular').innerHTML = angular;
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