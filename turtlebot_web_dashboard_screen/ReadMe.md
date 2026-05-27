# 🖥️ TurtleBot3 Web Dashboard — Screen Button Version

### ROS2 Humble + Gazebo + Button-Based Teleoperation System

This project creates a touchscreen-friendly TurtleBot3 dashboard controlled using on-screen buttons.

Built using:
- ROS2 Humble
- Gazebo
- rosbridge_server
- roslibjs
- Flask
- HTML/CSS/JavaScript

---

# 📖 Features

- On-screen movement buttons
- Mobile support
- Touchscreen support
- Speed slider
- Emergency stop
- Live camera stream
- ROS2 WebSocket communication

---

# 🧠 System Architecture

```text
Button Click
↓
JavaScript Event
↓
publishVelocity()
↓
rosbridge_server
↓
ROS2 /cmd_vel
↓
Gazebo Robot
```

---

# 📁 Folder Structure

```text
turtlebot_web_dashboard_screen/
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

# 🎮 Control Layout

```text
        Forward

Left      STOP      Right

       Backward
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

    document.getElementById('linear').innerHTML = linear.toFixed(2);

    document.getElementById('angular').innerHTML = angular.toFixed(2);
}

const forwardBtn = document.getElementById('forwardBtn');

forwardBtn.onmousedown = function () {

    linear = speed;
    angular = 0;

    publishVelocity();
};

forwardBtn.onmouseup = function () {

    linear = 0;
    angular = 0;

    publishVelocity();
};

const backwardBtn = document.getElementById('backwardBtn');

backwardBtn.onmousedown = function () {

    linear = -speed;
    angular = 0;

    publishVelocity();
};

backwardBtn.onmouseup = function () {

    linear = 0;
    angular = 0;

    publishVelocity();
};

const leftBtn = document.getElementById('leftBtn');

leftBtn.onmousedown = function () {

    linear = 0;
    angular = speed;

    publishVelocity();
};

leftBtn.onmouseup = function () {

    linear = 0;
    angular = 0;

    publishVelocity();
};

const rightBtn = document.getElementById('rightBtn');

rightBtn.onmousedown = function () {

    linear = 0;
    angular = -speed;

    publishVelocity();
};

rightBtn.onmouseup = function () {

    linear = 0;
    angular = 0;

    publishVelocity();
};

const stopBtn = document.getElementById('stopBtn');

stopBtn.onclick = function () {

    linear = 0;
    angular = 0;

    publishVelocity();
};
```

---

# 📱 Mobile Support

This project supports:
- touchscreens
- tablets
- phones

using:
```text
ontouchstart
ontouchend
```

---

# ⚠️ Troubleshooting

## Buttons Not Working

Run:

```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

---

## No Camera Feed

```bash
ros2 topic list | grep camera
```

Make sure:

```bash
export TURTLEBOT3_MODEL=waffle
```