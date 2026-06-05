import threading
import webbrowser

from flask import Flask
from flask import send_from_directory
from flask import jsonify

from robot_stack import RobotStack


# ==========================================
# CREATE FLASK APP
# ==========================================

app = Flask(

    __name__,
    static_folder="../frontend"

)

# ==========================================
# CREATE ROBOT STACK
# ==========================================

stack = RobotStack()

# ==========================================
# START ROBOTICS STACK
# ==========================================

stack.start_system()

# ==========================================
# FRONTEND
# ==========================================

@app.route("/")
def index():

    return send_from_directory(

        app.static_folder,
        "index.html"

    )


@app.route("/<path:path>")
def static_files(path):

    return send_from_directory(

        app.static_folder,
        path

    )

# ==========================================
# ENABLE AUTONOMY
# ==========================================

@app.route("/start_exploration")
def start_exploration():

    stack.enable_autonomy()

    return jsonify(

        {
            "message": "Autonomous Mode Enabled"
        }

    )

# ==========================================
# DISABLE AUTONOMY
# ==========================================

@app.route("/stop_exploration")
def stop_exploration():

    stack.disable_autonomy()

    return jsonify(

        {
            "message": "Autonomous Mode Disabled"
        }

    )

# ==========================================
# EMERGENCY STOP
# ==========================================

@app.route("/emergency_stop")
def emergency_stop():

    stack.emergency_stop()

    return jsonify(

        {
            "message": "Emergency Stop Activated"
        }

    )

# ==========================================
# STATUS API
# ==========================================

@app.route("/status")
def status():

    return jsonify(

        stack.get_status()

    )

# ==========================================
# SHUTDOWN
# ==========================================

@app.route("/shutdown")
def shutdown():

    stack.shutdown_system()

    return "System Shutdown"

# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    threading.Timer(

        1.5,

        lambda: webbrowser.open(
            "http://localhost:5000"
        )

    ).start()

    app.run(

        host="0.0.0.0",
        port=5000,
        debug=False

    )