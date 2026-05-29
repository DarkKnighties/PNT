from flask import Flask
from flask import send_from_directory
from flask import jsonify

from system_manager import SystemManager

# ==========================================
# CREATE FLASK APP
# ==========================================

app = Flask(

    __name__,
    static_folder='../frontend'

)

# ==========================================
# CREATE SYSTEM MANAGER
# ==========================================

manager = SystemManager()

# ==========================================
# START ROBOTICS STACK
# ==========================================

manager.start_system()

# ==========================================
# SERVE FRONTEND
# ==========================================

@app.route('/')
def index():

    return send_from_directory(

        app.static_folder,
        'index.html'

    )

@app.route('/<path:path>')
def static_files(path):

    return send_from_directory(

        app.static_folder,
        path

    )

# ==========================================
# START EXPLORATION
# ==========================================

@app.route('/start_exploration')

def start_exploration():

    manager.start_exploration()

    return jsonify({

        "message": "Exploration Started"

    })

# ==========================================
# STOP EXPLORATION
# ==========================================

@app.route('/stop_exploration')

def stop_exploration():

    manager.stop_exploration()

    return jsonify({

        "message": "Exploration Stopped"

    })

# ==========================================
# EMERGENCY STOP
# ==========================================

@app.route('/emergency_stop')

def emergency_stop():

    manager.emergency_stop()

    return jsonify({

        "message": "Emergency Stop Activated"

    })

# ==========================================
# SHUTDOWN SYSTEM
# ==========================================

@app.route('/shutdown')

def shutdown():

    manager.shutdown_system()

    return "System Shutdown"

# ==========================================
# MAIN
# ==========================================

if __name__ == '__main__':

    app.run(

        host='0.0.0.0',
        port=5000,
        debug=False

    )