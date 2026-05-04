# Security Policy

This project is a local, offline game simulation. It is not designed for real-world sensing, targeting, radar processing, or control of physical systems.

## Scope

Supported security expectations:

- The app does not make network requests.
- The app does not execute shell commands.
- The app does not load plugins, pickle files, or arbitrary code.
- The app does not read game memory, camera feeds, radar feeds, serial devices, or external telemetry.
- The app uses synthetic game-coordinate data generated inside the simulation.

## Reporting

If this project is published to GitHub, report security issues through private repository contact channels or GitHub private vulnerability reporting if enabled.

## Design Boundary

Keep future contributions inside fictional, in-game simulation use. Do not add real sensor integrations, real targeting workflows, or code that controls physical devices.
