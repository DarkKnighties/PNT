// ========================================
// GLOBAL ROS OBJECT
// ========================================

let ros = null;

// ========================================
// CONNECT TO ROSBRIDGE
// ========================================

function connectROS() {

    if (ros !== null) {

        try {

            ros.close();

        } catch (e) {

            console.log(e);

        }

    }

    ros = new ROSLIB.Ros({

        url: 'ws://localhost:9090'

    });

    // ========================================
    // CONNECTION SUCCESS
    // ========================================

    ros.on('connection', function () {

        console.log("Connected to ROSBridge");

        const el = document.getElementById('connection');
        el.innerHTML = 'Connected';
        el.classList.add('ok');

        const dot = document.getElementById('connectionDot');
        if (dot) dot.classList.add('connected');

        subscribeToMap();

    });

    // ========================================
    // CONNECTION ERROR
    // ========================================

    ros.on('error', function (error) {

        console.log("ROSBridge Error");

        const el = document.getElementById('connection');
        el.innerHTML = 'Error';
        el.classList.remove('ok');

        const dot = document.getElementById('connectionDot');
        if (dot) dot.classList.remove('connected');

    });

    // ========================================
    // CONNECTION CLOSED
    // ========================================

    ros.on('close', function () {

        console.log("ROSBridge Closed");

        const el = document.getElementById('connection');
        el.innerHTML = 'Reconnecting...';
        el.classList.remove('ok');

        const dot = document.getElementById('connectionDot');
        if (dot) dot.classList.remove('connected');

        setTimeout(function () {

            connectROS();

        }, 2000);

    });

}

// ========================================
// INITIAL CONNECTION
// ========================================

connectROS();

// ========================================
// START EXPLORATION
// ========================================

document.getElementById(
    'startExploration'
).onclick = function () {

    console.log("Starting Exploration");

    const el = document.getElementById('explorationState');
    el.innerHTML = 'STARTING';
    el.classList.remove('ok');

    fetch('/start_exploration')

        .then(response => response.json())

        .then(data => {

            console.log(data);

            el.innerHTML = 'RUNNING';
            el.classList.add('ok');

            const dot = document.getElementById('explorationDot');
            if (dot) dot.classList.add('connected');

        })

        .catch(error => {

            console.log(error);

            el.innerHTML = 'ERROR';

        });

};

// ========================================
// STOP EXPLORATION
// ========================================

document.getElementById(
    'stopExploration'
).onclick = function () {

    console.log("Stopping Exploration");

    fetch('/stop_exploration')

        .then(response => response.json())

        .then(data => {

            console.log(data);

            const el = document.getElementById('explorationState');
            el.innerHTML = 'STOPPED';
            el.classList.remove('ok');

            const dot = document.getElementById('explorationDot');
            if (dot) dot.classList.remove('connected');

        })

        .catch(error => {

            console.log(error);

            document.getElementById(
                'explorationState'
            ).innerHTML = 'ERROR';

        });

};

// ========================================
// SHUTDOWN SYSTEM
// ========================================

document.getElementById(
    'shutdownSystem'
).onclick = function () {

    console.log("Shutting Down System");

    document.getElementById('connection').innerHTML = 'Shutting Down';
    document.getElementById('explorationState').innerHTML = 'OFFLINE';

    const dots = document.querySelectorAll('.status-dot');
    dots.forEach(d => d.classList.remove('connected'));

    fetch('/shutdown')

        .then(response => response.text())

        .then(data => {

            console.log(data);

            alert(data);

        })

        .catch(error => {

            console.log(error);

            alert("Shutdown Failed");

        });

};

// ========================================
// MAP RENDERER
// ========================================

const canvas = document.getElementById('mapCanvas');

const ctx = canvas.getContext('2d');

canvas.width = 800;
canvas.height = 800;

// ========================================
// MAP SUBSCRIBER
// ========================================

function subscribeToMap() {

    const mapTopic = new ROSLIB.Topic({

        ros: ros,

        name: '/map',

        messageType: 'nav_msgs/OccupancyGrid'

    });

    mapTopic.subscribe(function(message) {

        renderMap(message);

    });

}

// ========================================
// RENDER MAP
// ========================================

function renderMap(message) {

    const width = message.info.width;

    const height = message.info.height;

    const data = message.data;

    ctx.clearRect(

        0,
        0,
        canvas.width,
        canvas.height

    );

    const scaleX = canvas.width / width;

    const scaleY = canvas.height / height;

    for (let y = 0; y < height; y++) {

        for (let x = 0; x < width; x++) {

            const i = x + (y * width);

            const value = data[i];

            // Unknown
            if (value === -1) {

                ctx.fillStyle = '#1a2a35';

            }

            // Free
            else if (value === 0) {

                ctx.fillStyle = '#e8f0f5';

            }

            // Occupied
            else {

                ctx.fillStyle = '#00ffff';

            }

            const drawY = height - y;

            ctx.fillRect(

                x * scaleX,
                drawY * scaleY,
                scaleX,
                scaleY

            );

        }

    }

}