// Connect to ROSBridge WebSocket

const ros = new ROSLIB.Ros({
    url: 'ws://localhost:9090'
});

// Connection Status

ros.on('connection', function () {

    document.getElementById('connection').innerHTML = 'Connected';

});

ros.on('error', function () {

    document.getElementById('connection').innerHTML = 'Error';

});

ros.on('close', function () {

    document.getElementById('connection').innerHTML = 'Closed';

});

// Create /cmd_vel publisher

const cmdVel = new ROSLIB.Topic({

    ros: ros,
    name: '/cmd_vel',
    messageType: 'geometry_msgs/Twist'

});

// Velocity Variables

let linear = 0;
let angular = 0;

// Speed Slider

const speedSlider = document.getElementById('speedSlider');

let speed = parseFloat(speedSlider.value);

speedSlider.oninput = function () {

    speed = parseFloat(this.value);

};

// Function to publish velocity

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

// =========================
// BUTTON CONTROLS
// =========================

// Forward Button

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

// Backward Button

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

// Left Button

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

// Right Button

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

// STOP Button

const stopBtn = document.getElementById('stopBtn');

stopBtn.onclick = function () {

    linear = 0;
    angular = 0;

    publishVelocity();
};

// =========================
// MOBILE TOUCH SUPPORT
// =========================

// Forward

forwardBtn.ontouchstart = function () {

    linear = speed;
    angular = 0;

    publishVelocity();
};

forwardBtn.ontouchend = function () {

    linear = 0;
    angular = 0;

    publishVelocity();
};

// Backward

backwardBtn.ontouchstart = function () {

    linear = -speed;
    angular = 0;

    publishVelocity();
};

backwardBtn.ontouchend = function () {

    linear = 0;
    angular = 0;

    publishVelocity();
};

// Left

leftBtn.ontouchstart = function () {

    linear = 0;
    angular = speed;

    publishVelocity();
};

leftBtn.ontouchend = function () {

    linear = 0;
    angular = 0;

    publishVelocity();
};

// Right

rightBtn.ontouchstart = function () {

    linear = 0;
    angular = -speed;

    publishVelocity();
};

rightBtn.ontouchend = function () {

    linear = 0;
    angular = 0;

    publishVelocity();
};