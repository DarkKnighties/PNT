# 🤖 ROS2 + Gazebo Robotics Web Dashboards

This repository contains robotics web dashboard projects using ROS2, Gazebo, rosbridge_server, and roslibjs.

## Repository Structure

```text
PNT/
├── README.md
├── turtlebot_web_dashboard_keyboard/
│   └── README.md
└── turtlebot_web_dashboard_screen/
    └── README.md
```

## Technologies Used

- ROS2 Humble
- Gazebo
- TurtleBot3
- rosbridge_server
- roslibjs
- Flask
- HTML/CSS/JavaScript

## Installation

### Install ROS2

```bash
sudo apt update
sudo apt install ros-humble-desktop-full -y
```

### Install TurtleBot3

```bash
sudo apt install ros-humble-turtlebot3* -y
```

### Set Robot Model

```bash
echo 'export TURTLEBOT3_MODEL=waffle' >> ~/.bashrc
source ~/.bashrc
```

### Install rosbridge + video server

```bash
sudo apt install \
ros-humble-rosbridge-suite \
ros-humble-web-video-server \
python3-flask \
-y
```

## System Architecture

```text
Browser
↓
JavaScript + roslibjs
↓
WebSocket
↓
rosbridge_server
↓
ROS2
↓
Gazebo
↓
Robot
```
