# Security Policy

This project is a local, offline game simulation. It is not designed for real-world sensing, targeting, radar processing, or control of physical systems.

Public-name-inspired radar, missile, vehicle, EW, nuclear plant, and defense labels are used only as game flavor. The generated catalog stats, terrain effects, HUD styles, height tracking, sounds, plant behavior, and EW behavior are fictional balance values and should not be treated as real technical performance data.

## Scope

Supported security expectations:

- The app does not make network requests.
- The app does not execute shell commands.
- The app does not load plugins, pickle files, or arbitrary code.
- The app does not read game memory, camera feeds, radar feeds, serial devices, or external telemetry.
- The app uses synthetic game-coordinate data generated inside the simulation.
- The nuclear plant mode is an abstract game UI and is not a plant operations guide or engineering model.
- Optional HQ speech uses a local Windows speech bridge if available; it does not call any web service.

## Reporting

If this project is published to GitHub, report security issues through private repository contact channels or GitHub private vulnerability reporting if enabled.

## Design Boundary

Keep future contributions inside fictional, in-game simulation use. Do not add real sensor integrations, real targeting workflows, real reactor operations workflows, or code that controls physical devices.
