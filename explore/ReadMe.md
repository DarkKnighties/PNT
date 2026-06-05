# TurtleBot3 Autonomous Navigation Dashboard

## Overview

This project provides a modern web-based operator dashboard for monitoring and controlling a TurtleBot3 running autonomous exploration using ROS 2.

The dashboard combines:

* Live occupancy grid visualization
* Real-time camera feed
* Exploration controls
* Telemetry monitoring
* Robot pose tracking
* System health monitoring
* Event logging

The interface is designed to resemble a lightweight Autonomous Mobile Robot (AMR) control station rather than a traditional robotics demo panel.

---

# Features

## Autonomous Navigation

The dashboard allows operators to:

* Start autonomous exploration
* Stop autonomous exploration
* Monitor exploration progress
* Track map coverage
* View exploration statistics

Exploration commands are forwarded to the backend through Flask endpoints and executed using Explore Lite.

---

## Live Occupancy Grid Map

The dashboard subscribes to:

```text
/map
```

through ROSBridge and renders:

* Unknown space
* Free space
* Occupied cells

The map updates continuously as SLAM progresses.

Displayed metrics include:

* Coverage percentage
* Known map cells
* Map update count

---

## Live Camera Feed

The dashboard displays a real-time camera stream from:

```text
/camera/image_raw
```

using a web video server.

The camera feed provides visual awareness during both autonomous and teleoperation modes.

---

## Robot Pose Tracking

The dashboard subscribes to:

```text
/odom
```

and displays:

* Position X
* Position Y
* Yaw Angle
* Cardinal Heading

Heading is automatically calculated from odometry orientation.

Example:

```text
Pos X     2.341
Pos Y    -1.087
Yaw      87.2°
Heading  N
```

---

## System Telemetry

The telemetry panel displays:

### ROSBridge Status

* Offline
* Online
* Reconnecting

### Exploration State

* Idle
* Starting
* Running
* Stopped

### Robot Status

* Active
* Moving

### Navigation Status

* Ready

### SLAM Status

* Running

### Map Coverage

Calculated from occupancy grid data.

---

## Mission Status

The mission panel displays:

* Current operating mode
* Exploration coverage
* Map update count
* Command count

These values are updated in real time during operation.

---

## Event Logging

The dashboard maintains a live event log containing:

* ROS connection events
* Exploration start events
* Exploration stop events
* Shutdown events
* Error messages
* Status changes

The newest entries are automatically displayed.

---

## Subsystem Monitoring

The right panel provides quick visibility into:

* Gazebo
* SLAM Toolbox
* Nav2
* ROSBridge
* Video Server
* Explore Lite

Subsystem states are displayed using status indicators.

---

# Dashboard Layout

```text
┌─────────────────────────────────────────────────────────────┐
│                       TOP STATUS BAR                        │
├──────────────┬──────────────────────────────┬───────────────┤
│              │                              │               │
│ Telemetry    │          Occupancy Map       │  Subsystems   │
│              │                              │               │
├──────────────┤──────────────────────────────├───────────────┤
│ Mission      │          Camera Feed         │    Metrics    │
│              │                              │               │
├──────────────┤──────────────────────────────├───────────────┤
│ Position     │          Controls            │     Robot     │
│              │                              │               │
├──────────────┤──────────────────────────────┤               │
│ Event Log    │        Shutdown System       │               │
└──────────────┴──────────────────────────────┴───────────────┘
```

---

# ROS Topics

## Subscribed Topics

### Occupancy Grid

```text
/map
```

Type:

```text
nav_msgs/OccupancyGrid
```

Used for map rendering and coverage calculation.

---

### Odometry

```text
/odom
```

Type:

```text
nav_msgs/Odometry
```

Used for robot position and heading updates.

---

## Camera Feed

```text
/camera/image_raw
```

Used for live camera visualization.

---

# Backend Endpoints

## Start Exploration

```http
GET /start_exploration
```

Starts autonomous exploration.

---

## Stop Exploration

```http
GET /stop_exploration
```

Stops autonomous exploration.

---

## Shutdown System

```http
GET /shutdown
```

Terminates the robotics stack and shuts down active services.

---

# Future Enhancements

## Teleoperation Mode

Planned features include:

* Autonomous ↔ Teleop mode selector
* Velocity control panel
* Speed adjustment slider
* Safety interlocks preventing simultaneous teleop and autonomous control

When Teleop mode is enabled:

1. Exploration will automatically stop.
2. Robot velocity will be reset to zero.
3. Manual control panel will become available.

---

## AMR-Oriented Improvements

Planned additions:

* Robot orientation arrow on map
* Coverage heatmap
* Mission queue
* Docking status
* Battery monitoring
* Localization confidence
* Multi-robot support

---

# Technology Stack

Frontend:

* HTML5
* CSS3
* JavaScript

Communication:

* ROSBridge
* ROSLIB.js

Backend:

* Flask

Robotics:

* ROS 2 Humble
* Nav2
* SLAM Toolbox
* Explore Lite
* TurtleBot3 Waffle

Simulation:

* Gazebo

---

# Author

Developed as part of an Autonomous Mobile Robot (AMR) dashboard and exploration platform for TurtleBot3.
