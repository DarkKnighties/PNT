# TODO

- [x] Update `explore copy/frontend/index.html` to implement RViz-style robot trail
  - [x] Add global `robotX`, `robotY`, `robotYaw`
  - [x] Add global `robotTrail`, `lastTrailX`, `lastTrailY`
  - [x] Subscribe to `/odom` (`nav_msgs/msg/Odometry`)
  - [x] Append trail points only if distance > 0.05m; cap to 1000 points
  - [x] In `renderMap(msg)`, after drawing occupancy grid, draw continuous trail using world→map→canvas conversion recomputed every frame
  - [x] Do not modify existing map rendering logic or add robot marker



