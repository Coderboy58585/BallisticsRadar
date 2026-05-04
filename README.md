# Game Radar Intercept Simulator

A small, offline Python app for estimating and tracking simulated in-game projectiles on a 2D radar display. It predicts projectile motion and computes game-only interception points from a protected base.

This project is intentionally simulation-only. It does not connect to cameras, sensors, external telemetry, game memory, real-world radar, or any weapon system.

## Why Python?

Python is the best starting point for this app because the main work is geometry, prediction, UI iteration, and tests. C++ would make sense later if this becomes a game-engine plugin, needs very high frame rates, or must integrate with an existing C++ codebase.

## Features

- 2D radar-style Tkinter app with synthetic projectile tracks.
- Multiple projectile profiles: rocket, mortar shell, drone, plasma bolt.
- Track smoothing and velocity estimation from noisy game-coordinate observations.
- Constant-velocity intercept solver with robust no-solution handling.
- Optional interceptor deployment in the simulation.
- Unit tests for tracking and interception math.
- No third-party dependencies for the app itself.

## Quick Start

```powershell
python -m pip install -e .
game-radar
```

You can also run the module directly after installing:

```powershell
python -m game_radar.app
```

## Run Tests

```powershell
python -m unittest discover -s tests
```

## Project Layout

- `src/game_radar/models.py` - immutable vector and projectile data models.
- `src/game_radar/intercept.py` - intercept solution math.
- `src/game_radar/tracker.py` - radar track estimation and prediction.
- `src/game_radar/simulation.py` - simulation world and projectile spawning.
- `src/game_radar/app.py` - Tkinter radar UI.

## Security Notes

- No network access.
- No shell command execution.
- No `eval`, `exec`, pickle loading, or plugin loading.
- Inputs are constrained to in-app controls and validated dataclass values.
- Intended for fictional, in-game coordinates only.
