// Connect to rosbridge websocket

const ros = new ROSLIB.Ros({
    url: 'ws://localhost:9090'
});

// Connection status

ros.on('connection', function () {
    document.getElementById('connection').innerHTML = 'Connected';
});

ros.on('error', function () {
    document.getElementById('connection').innerHTML = 'Error';
});

ros.on('close', function () {
    document.getElementById('connection').innerHTML = 'Closed';
});

// Create publisher for /cmd_vel

const cmdVel = new ROSLIB.Topic({
    ros: ros,
    name: '/cmd_vel',
    messageType: 'geometry_msgs/Twist'
});

// Velocity values

let linear = 0.0;
let angular = 0.0;

// Speed slider

const speedSlider = document.getElementById('speedSlider');

let speed = parseFloat(speedSlider.value);

speedSlider.oninput = function () {
    speed = parseFloat(this.value);
};

// Publish velocity

function publishVelocity() {

    const twist = new ROSLIB.Message({

        linear: {
            x: linear,
            y: 0.0,
            z: 0.0
        },

        angular: {
            x: 0.0,
            y: 0.0,
            z: angular
        }

    });

    cmdVel.publish(twist);

    document.getElementById('linear').innerHTML = linear;
    document.getElementById('angular').innerHTML = angular;
}

// Keyboard controls

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

// Stop robot when key released

document.addEventListener('keyup', function() {
    linear = 0;
    angular = 0;
    publishVelocity();
});

// Emergency stop button

document.getElementById('stopButton').onclick = function() {

    linear = 0;
    angular = 0;

    publishVelocity();
};