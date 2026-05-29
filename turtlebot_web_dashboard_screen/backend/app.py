from flask import Flask, send_from_directory
import subprocess
import os
import time

app = Flask(__name__, static_folder='../frontend')

# =========================
# GLOBAL VARIABLES
# =========================

system_started = False

gazebo_process = None
rosbridge_process = None
video_process = None

# =========================
# START ROBOTICS STACK
# =========================

def start_robotics_stack():

    global system_started
    global gazebo_process
    global rosbridge_process
    global video_process

    if system_started:
        return

    print("\nStarting Robotics Stack...\n")

    os.environ["TURTLEBOT3_MODEL"] = "waffle"

    # Launch Gazebo + TurtleBot3

    gazebo_process = subprocess.Popen(

        """
        source /opt/ros/humble/setup.bash &&
        export TURTLEBOT3_MODEL=waffle &&
        ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
        """,

        shell=True,
        executable="/bin/bash"
    )

    print("Gazebo Started")

    time.sleep(5)

    # Launch rosbridge websocket

    rosbridge_process = subprocess.Popen(

        """
        source /opt/ros/humble/setup.bash &&
        ros2 launch rosbridge_server rosbridge_websocket_launch.xml
        """,

        shell=True,
        executable="/bin/bash"
    )

    print("Rosbridge Started")

    time.sleep(2)

    # Launch web video server

    video_process = subprocess.Popen(

        """
        source /opt/ros/humble/setup.bash &&
        ros2 run web_video_server web_video_server
        """,

        shell=True,
        executable="/bin/bash"
    )

    print("Video Server Started")

    system_started = True

    print("\nSystem Ready.\n")

# =========================
# SHUTDOWN ROBOTICS STACK
# =========================

@app.route('/shutdown')
def shutdown_system():

    global gazebo_process
    global rosbridge_process
    global video_process
    global system_started

    print("\nShutting Down System...\n")

    try:

        if gazebo_process:
            gazebo_process.terminate()

        if rosbridge_process:
            rosbridge_process.terminate()

        if video_process:
            video_process.terminate()

        # Extra cleanup

        subprocess.Popen(
            "pkill -f gzserver",
            shell=True
        )

        subprocess.Popen(
            "pkill -f gzclient",
            shell=True
        )

        subprocess.Popen(
            "pkill -f ros2",
            shell=True
        )

        system_started = False

        return "Robotics System Shutdown Complete"

    except Exception as e:

        return f"Error: {e}"

# =========================
# MAIN ROUTES
# =========================

@app.route('/')
def index():

    start_robotics_stack()

    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):

    return send_from_directory(app.static_folder, path)

# =========================
# START FLASK
# =========================

if __name__ == '__main__':

    app.run(
        host='0.0.0.0',
        port=5000
    )