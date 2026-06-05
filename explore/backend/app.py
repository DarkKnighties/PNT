import threading
import webbrowser
import os
import subprocess
from datetime import datetime

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

@app.route("/save_map", methods=["POST"]) 
def save_map():

    try:
        # timestamped base name
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        name = f"map_{ts}"

        # target directory: PNT/explore/maps
        maps_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'maps'))
        os.makedirs(maps_dir, exist_ok=True)

        base_path = os.path.join(maps_dir, name)

        # Call nav2 map saver CLI
        cmd = [
            'ros2', 'run', 'nav2_map_server', 'map_saver_cli', '-f', base_path
        ]

        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if proc.returncode != 0:
            return jsonify({
                "success": False,
                "error": proc.stderr.strip() or "map_saver_cli failed"
            }), 500

        # Determine produced files (yaml + image)
        yaml_path = base_path + '.yaml'
        image_path = base_path + '.pgm'
        if not os.path.exists(image_path):
            alt = base_path + '.png'
            if os.path.exists(alt):
                image_path = alt

        return jsonify({
            "success": True,
            "name": name,
            "yaml": yaml_path,
            "image": image_path
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==========================================
# MAP LIBRARY API
# ==========================================

@app.route("/maps", methods=["GET"])
def list_maps():
    """Return array of saved maps (both .yaml and .pgm present). Newest first."""
    try:
        maps_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'maps'))
        if not os.path.isdir(maps_dir):
            return jsonify([])

        entries = []
        for fn in os.listdir(maps_dir):
            if not fn.endswith('.yaml'):
                continue
            base = fn[:-5]
            pgm = base + '.pgm'
            pgm_path = os.path.join(maps_dir, pgm)
            yaml_path = os.path.join(maps_dir, fn)
            if os.path.isfile(pgm_path) and os.path.isfile(yaml_path):
                mtime = os.path.getmtime(pgm_path)
                entries.append({
                    'name': base,
                    'yaml': fn,
                    'image': pgm,
                    'mtime': mtime
                })

        # sort newest first
        entries.sort(key=lambda e: e['mtime'], reverse=True)
        for e in entries:
            del e['mtime']

        return jsonify(entries)

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route('/maps/<path:filename>', methods=['GET'])
def serve_map_file(filename):
    """Serve the requested map file from the maps directory."""
    try:
        maps_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'maps'))
        safe_name = os.path.basename(filename)
        target = os.path.join(maps_dir, safe_name)
        if not os.path.isfile(target):
            return jsonify({'error': 'file not found'}), 404
        return send_from_directory(maps_dir, safe_name)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route('/maps/<map_name>', methods=['DELETE'])
def delete_map(map_name):
    """Delete both .pgm and .yaml files for the given map base name."""
    try:
        base = os.path.basename(map_name)
        maps_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'maps'))
        pgm = os.path.join(maps_dir, base + '.pgm')
        yaml = os.path.join(maps_dir, base + '.yaml')

        removed_any = False
        errors = []

        if os.path.isfile(pgm):
            try:
                os.remove(pgm)
                removed_any = True
            except Exception as e:
                errors.append(str(e))

        if os.path.isfile(yaml):
            try:
                os.remove(yaml)
                removed_any = True
            except Exception as e:
                errors.append(str(e))

        if not removed_any:
            return jsonify({"success": False, "error": "map not found"}), 404

        if errors:
            return jsonify({"success": False, "error": '; '.join(errors)}), 500

        return jsonify({"success": True})

    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


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