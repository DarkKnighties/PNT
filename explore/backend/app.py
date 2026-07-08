import threading
import webbrowser
import os
import subprocess
from datetime import datetime

from flask import Flask
from flask import send_from_directory
from flask import jsonify
from flask import request

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
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        name = f"map_{ts}"

        maps_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'maps'))
        os.makedirs(maps_dir, exist_ok=True)

        base_path = os.path.join(maps_dir, name)

        cmd = [
            'ros2', 'run', 'nav2_map_server', 'map_saver_cli', '-f', base_path
        ]

        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if proc.returncode != 0:
            return jsonify({
                "success": False,
                "error": proc.stderr.strip() or "map_saver_cli failed"
            }), 500

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

        entries.sort(key=lambda e: e['mtime'], reverse=True)
        for e in entries:
            del e['mtime']

        return jsonify(entries)

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route('/maps/<path:filename>', methods=['GET'])
def serve_map_file(filename):
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


# ==========================================
# LOAD MAP
# ==========================================

def _pgm_dimensions(pgm_path):
    with open(pgm_path, 'rb') as f:
        magic = f.readline().decode('ascii').strip()
        line = f.readline().decode('ascii').strip()
        while line.startswith('#'):
            line = f.readline().decode('ascii').strip()
        parts = line.split()
        return int(parts[0]), int(parts[1])


@app.route("/load_map", methods=["POST"])
def load_map():

    try:

        data = request.get_json(silent=True) or {}
        map_name = data.get("map")

        if not map_name:
            return jsonify({"success": False, "error": "No map provided"}), 400

        maps_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'maps')
        )
        yaml_path = os.path.join(maps_dir, map_name + '.yaml')
        pgm_path  = os.path.join(maps_dir, map_name + '.pgm')

        if not os.path.isfile(yaml_path):
            return jsonify({"success": False, "error": f"Map not found: {map_name}"}), 404

        import yaml
        with open(yaml_path, 'r') as f:
            meta = yaml.safe_load(f)

        resolution = float(meta.get('resolution', 0.05))
        origin     = meta.get('origin', [0.0, 0.0, 0.0])

        if os.path.isfile(pgm_path):
            width, height = _pgm_dimensions(pgm_path)
        else:
            width, height = 0, 0

        stack.load_map(map_name)

        return jsonify({
            "success":     True,
            "loaded_map":  map_name,
            "info": {
                "resolution": resolution,
                "width":      width,
                "height":     height,
                "origin_x":   float(origin[0]),
                "origin_y":   float(origin[1]),
                "origin_yaw": float(origin[2]) if len(origin) > 2 else 0.0,
            }
        })
    

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==========================================
# MAP IMAGE (PGM → PNG for browser)
# ==========================================

@app.route('/map_image/<map_name>', methods=['GET'])
def map_image(map_name):
    try:
        base     = os.path.basename(map_name)
        maps_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'maps')
        )
        pgm_path = os.path.join(maps_dir, base + '.pgm')
        png_path = os.path.join(maps_dir, base + '.png')

        if os.path.isfile(png_path):
            from flask import send_file
            return send_file(png_path, mimetype='image/png')

        if not os.path.isfile(pgm_path):
            return jsonify({'error': 'Map image not found'}), 404

        try:
            from PIL import Image
        except ImportError:
            return send_from_directory(maps_dir, base + '.pgm',
                                       mimetype='image/x-portable-graymap')

        import io
        img = Image.open(pgm_path).convert('L')

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)

        from flask import send_file
        return send_file(buf, mimetype='image/png')

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==========================================
# LOCALIZE (AMCL stub)
# ==========================================

@app.route('/localize', methods=['POST'])
def localize():
    return jsonify({'success': False, 'message': 'Localization not yet implemented'}), 501


# ==========================================
# UNLOAD MAP
# ==========================================

@app.route("/unload_map", methods=["POST"])
def unload_map():

    try:

        stack.unload_map()

        return jsonify(

            {
                "success": True
            }

        )

    except Exception as e:

        return jsonify(

            {
                "success": False,
                "error": str(e)
            }

        ), 500


@app.route("/shutdown")
def shutdown():

    stack.shutdown_system()

    return "System Shutdown"

# ==========================================
# SET INITIAL POSE
# ==========================================

@app.route("/set_initial_pose", methods=["POST"])
def set_initial_pose():

    try:

        data = request.get_json(silent=True) or {}

        x = data.get("x")
        y = data.get("y")
        yaw = data.get("yaw", 0.0)

        if x is None or y is None:
            return jsonify({
                "success": False,
                "error": "x and y are required"
            }), 400

        result = stack.set_initial_pose(x, y, yaw)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# NAVIGATE TO GOAL
# ==========================================

@app.route("/navigate_to", methods=["POST"])
def navigate_to():

    try:

        data = request.get_json(silent=True) or {}

        x = data.get("x")
        y = data.get("y")
        yaw = data.get("yaw", 0.0)

        if x is None or y is None:
            return jsonify({
                "success": False,
                "error": "x and y are required"
            }), 400

        result = stack.navigate_to(x, y, yaw)

        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# CANCEL NAVIGATION
# ==========================================

@app.route("/cancel_navigation", methods=["POST"])
def cancel_navigation():

    try:

        result = stack.cancel_navigation()

        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# NAVIGATION STATUS
# ==========================================

@app.route("/navigation_status", methods=["GET"])
def navigation_status():

    try:

        return jsonify(
            stack.get_navigation_status()
        )

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# WAYPOINT APIS
# ==========================================

@app.route("/waypoints", methods=["GET"])
def get_waypoints():

    try:

        return jsonify(
            stack.get_waypoints()
        )

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/waypoints/add", methods=["POST"])
def add_waypoint():

    try:

        data = request.get_json(silent=True) or {}

        x = data.get("x")
        y = data.get("y")
        yaw = data.get("yaw", 0.0)

        if x is None or y is None:
            return jsonify({
                "success": False,
                "error": "x and y are required"
            }), 400

        result = stack.add_waypoint(x, y, yaw)

        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/waypoints/insert", methods=["POST"])
def insert_waypoint():

    try:

        data = request.get_json(silent=True) or {}

        x = data.get("x")
        y = data.get("y")
        yaw = data.get("yaw", 0.0)
        index = data.get("index")

        if x is None or y is None or index is None:
            return jsonify({
                "success": False,
                "error": "x, y, and index are required"
            }), 400

        result = stack.insert_waypoint(x, y, yaw, int(index))

        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/waypoints/delete", methods=["POST"])
def delete_waypoint():

    try:

        data = request.get_json(silent=True) or {}

        index = data.get("index")

        if index is None:
            return jsonify({
                "success": False,
                "error": "index is required"
            }), 400

        result = stack.delete_waypoint(int(index))

        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/waypoints/move_up", methods=["POST"])
def move_waypoint_up():

    try:

        data = request.get_json(silent=True) or {}

        index = data.get("index")

        if index is None:
            return jsonify({
                "success": False,
                "error": "index is required"
            }), 400

        result = stack.move_waypoint_up(int(index))

        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/waypoints/move_down", methods=["POST"])
def move_waypoint_down():

    try:

        data = request.get_json(silent=True) or {}

        index = data.get("index")

        if index is None:
            return jsonify({
                "success": False,
                "error": "index is required"
            }), 400

        result = stack.move_waypoint_down(int(index))

        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/waypoints/clear", methods=["POST"])
def clear_waypoints():

    try:

        result = stack.clear_waypoints()

        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# ROUTE APIS
# ==========================================

@app.route("/start_route", methods=["POST"])
def start_route():

    try:

        if not stack.localization_active:
            return jsonify({
                "success": False,
                "error": "Localization is not active"
            }), 400

        result = stack.start_route()

        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/stop_route", methods=["POST"])
def stop_route():

    try:

        result = stack.stop_route()

        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/route_status", methods=["GET"])
def route_status():

    try:

        return jsonify(
            stack.get_route_status()
        )

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    def open_dashboard():

        try:

            subprocess.Popen(

                [
                    "xdg-open",
                    "http://localhost:5000"
                ],

                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL

            )

        except Exception as e:

            print(f"Failed to open browser: {e}")

    threading.Timer(

        2.0,
        open_dashboard

    ).start()

    app.run(

        host="0.0.0.0",
        port=5000,
        debug=False

    )