// =========================
// CONNECT TO ROSBRIDGE
// =========================

const ros = new ROSLIB.Ros({
    url: 'ws://localhost:9090'
});

// =========================
// CONNECTION STATUS
// =========================

ros.on('connection', function () {

    document.getElementById('connection').innerHTML = 'Connected';

    console.log("Connected to ROSBridge");

});

ros.on('error', function () {

    document.getElementById('connection').innerHTML = 'Error';

    console.log("ROSBridge Error");

});

ros.on('close', function () {

    document.getElementById('connection').innerHTML = 'Closed';

    console.log("ROSBridge Connection Closed");

});

// =========================
// CREATE /cmd_vel PUBLISHER
// =========================

const cmdVel = new ROSLIB.Topic({

    ros: ros,

    name: '/cmd_vel',

    messageType: 'geometry_msgs/Twist'

});

// =========================
// VELOCITY VARIABLES
// =========================

let linear = 0;
let angular = 0;

// =========================
// SPEED SLIDER
// =========================

const speedSlider = document.getElementById('speedSlider');

let speed = parseFloat(speedSlider.value);

speedSlider.oninput = function () {

    speed = parseFloat(this.value);

};

// =========================
// PUBLISH VELOCITY FUNCTION
// =========================

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

    // Update UI

    document.getElementById('linear').innerHTML =
        linear.toFixed(2);

    document.getElementById('angular').innerHTML =
        angular.toFixed(2);
}

// =========================
// CONTINUOUS PUBLISHING LOOP
// =========================

// Publish at 10 Hz

setInterval(function () {

    publishVelocity();

}, 100);

// =========================
// BUTTON REFERENCES
// =========================

const forwardBtn = document.getElementById('forwardBtn');

const backwardBtn = document.getElementById('backwardBtn');

const leftBtn = document.getElementById('leftBtn');

const rightBtn = document.getElementById('rightBtn');

const stopBtn = document.getElementById('stopBtn');

// =========================
// FORWARD BUTTON
// =========================

forwardBtn.onmousedown = function () {

    linear = speed;
    angular = 0;

};

forwardBtn.onmouseup = stopRobot;

forwardBtn.onmouseleave = stopRobot;

// Mobile

forwardBtn.ontouchstart = function () {

    linear = speed;
    angular = 0;

};

forwardBtn.ontouchend = stopRobot;

// =========================
// BACKWARD BUTTON
// =========================

backwardBtn.onmousedown = function () {

    linear = -speed;
    angular = 0;

};

backwardBtn.onmouseup = stopRobot;

backwardBtn.onmouseleave = stopRobot;

// Mobile

backwardBtn.ontouchstart = function () {

    linear = -speed;
    angular = 0;

};

backwardBtn.ontouchend = stopRobot;

// =========================
// LEFT BUTTON
// =========================

leftBtn.onmousedown = function () {

    linear = 0;
    angular = speed;

};

leftBtn.onmouseup = stopRobot;

leftBtn.onmouseleave = stopRobot;

// Mobile

leftBtn.ontouchstart = function () {

    linear = 0;
    angular = speed;

};

leftBtn.ontouchend = stopRobot;

// =========================
// RIGHT BUTTON
// =========================

rightBtn.onmousedown = function () {

    linear = 0;
    angular = -speed;

};

rightBtn.onmouseup = stopRobot;

rightBtn.onmouseleave = stopRobot;

// Mobile

rightBtn.ontouchstart = function () {

    linear = 0;
    angular = -speed;

};

rightBtn.ontouchend = stopRobot;

// =========================
// STOP ROBOT FUNCTION
// =========================

function stopRobot() {

    linear = 0;
    angular = 0;

}

// =========================
// STOP BUTTON
// =========================

stopBtn.onclick = function () {

    stopRobot();

};

// =========================
// SHUTDOWN SYSTEM BUTTON
// =========================

document.getElementById('shutdownSystem').onclick =
function () {

    // Stop robot before shutdown

    stopRobot();

    // Close ROS websocket cleanly

    ros.close();

    fetch('/shutdown')

        .then(response => response.text())

        .then(data => {

            alert(data);

        })

        .catch(error => {

            alert("Shutdown Failed");

            console.log(error);

        });

};