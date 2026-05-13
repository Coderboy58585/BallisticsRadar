# Game Radar Intercept Simulator

A small, offline Python app for estimating and tracking simulated in-game projectiles on a 2D radar display. It predicts projectile motion and computes game-only interception points from a protected base.

This project is intentionally simulation-only. It does not connect to cameras, sensors, external telemetry, game memory, real-world radar, or any weapon system.

## Why Python?

Python is the best starting point for this app because the main work is geometry, prediction, UI iteration, and tests. C++ would make sense later if this becomes a game-engine plugin, needs very high frame rates, or must integrate with an existing C++ codebase.

## Features

- 2D radar-style Tkinter app with synthetic projectile tracks.
- Larger projectile catalog with artillery rockets, GMLRS-style rockets, mortar bombs, artillery shells, guided/glide bombs, cruise missiles, loitering drones, and anti-radiation missiles.
- Defense catalog with gun systems, missile interceptors, and a directed-energy option, all with ammo, year category, compatibility, and power costs.
- Year-categorized public-name-inspired radar choices from 1935 early-warning sets through modern AESA/EASA-style systems, including VHF, UHF, S-band, C-band, X-band, and J-band-style roles.
- More than 1,000 combined projectile, defense, radar, and enemy/vehicle/EW profiles. Public names are used for game flavor; stats are fictional.
- Terrain maps that affect radar range, clutter, projectile drag, terrain masking, and ground movement.
- Eight modes: sandbox, projectile pilot, waves, budget waves, ground assault, linked defense, story, and nuclear plant.
- Story-mode HQ phone calls with sound cues, optional Windows speech, operator orders, and random incidents.
- Standalone nuclear powerplant mode with its own reactor graphics, coolant pump trains, control rods, steam pressure, turbine load, grid demand, SCRAM, alarms, and plant events. It does not run radar, enemies, missiles, or EW.
- Random operational events such as mortar waves, drone swarms, SEAD raids, ground pushes, ghost-track storms, and radiological alerts.
- Spawnable aircraft, ground vehicles, launchers, stealth units, and EW units.
- Placeable radar sites that extend coverage around the map.
- Linked defense mode where interceptor launches require a compatible radar/defense pairing.
- Random radar sweep-stuck faults that can open a wire-repair minigame.
- Fictional electronic warfare with jamming fields, intermittent visibility, ghost tracks, burn-through, decoys, EMCON, and EW power management.
- Radar damage in specific modes from anti-radiation missiles.
- Radar display styles now change by radar architecture: early analog PPI, mechanical sweep, fixed-lobe early-warning, height-finder, pulse-Doppler range-rate, PESA sector scan, and AESA multi-beam displays.
- Built-in Windows sound cues for launches, waves, interceptions, HQ calls, manual cannon fire, plant alarms, pump trips, ghost tracks, and radar damage.
- Categorized radar years, decades, eras, and sensor types, including 1930s early-warning sets, 1940s fire-control radars, 1950s height-finders, 1960s VHF search systems, 1970s pulse-Doppler systems, 1980s PESA-style systems, 1990s/2000s 3D radars, AESA-style systems, and EASA/AESA training aliases.
- Height-aware radar tracks with abstract altitude, vertical speed, elevation coverage, beam width, and height-accuracy behavior.
- Track smoothing and velocity estimation from noisy game-coordinate observations.
- Constant-velocity intercept solver with robust no-solution handling.
- Optional interceptor deployment in the simulation.
- Player-projectile mode with WASD or arrow-key steering.
- Score and base-health tracking.
- Unit tests for tracking and interception math.
- No third-party dependencies for the app itself.

## Quick Start

```powershell
python -m pip install -e .
python -m game_radar.app
```

If Windows cannot find `python`, use the full path shown by your Python install:

```powershell
& "C:\Users\dacia\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m game_radar.app
```

You can also run the installed shortcut if your Python Scripts folder is on PATH:

```powershell
game-radar
```

## Run Tests

```powershell
python -m unittest discover -s tests
```

## Controls

- Choose `Sandbox` for manual one-at-a-time spawning with no automatic waves.
- Choose `Projectile Pilot` or click `Play As Projectile` to steer the selected projectile type with WASD or arrow keys.
- Choose `Waves` to fight timed enemy waves.
- Choose `Budget Waves` to buy radar/defense actions with points while waves scale up.
- Choose `Ground Assault` for vehicle-heavy waves where ground units pressure the site.
- Choose `Linked Defense` for waves where radar/defense compatibility matters.
- Choose `Story` for HQ calls, audible orders, and random incidents.
- Choose `Nuclear Plant` to run the standalone reactor panel with no radar battle running underneath.
- Choose a display style to change the radar presentation.
- Use the circular on-scope softkeys for launch, intercept, cannon, EW, and HQ actions without leaving the radar view.
- Toggle `Sound` if you want the operator cue tones on or off.
- Pick a map to change terrain effects.
- Pick a radar and click `Install / Switch Radar`; in budget waves, radar switches cost points.
- Choose a missile type and click `Launch Single Round`; ammo prevents spam.
- Filter projectiles, defenses, and enemies by decade as well as role/class/group.
- Choose an enemy type and click `Spawn Single Enemy` to add one aircraft, launcher, ground vehicle, stealth unit, or EW unit.
- Choose an interceptor type and click `Deploy Best Intercept` to target the nearest tracked projectile.
- Click `Strike Nearest Enemy` to launch an interceptor at the nearest enemy.
- Pick an EW action and click `Use EW Power`; actions spend radar-dependent EW power instead of using cooldowns.
- Click on the radar screen to place a manual aim point, then use `Manual Cannon Fire` with cannon-class defenses only.
- Turn on `Arm Right-Click Cannon`, then hold/right-drag on the radar screen to aim and fire cannon-class defenses manually.
- Turn on `Place Radar On Click`, then click the map to add the selected radar as a placed radar site.
- If the radar repair board opens, press the wire buttons in the displayed sequence to restore the radar.
- In `Story`, use `Answer HQ Phone` to accept HQ orders and trigger the next scenario step.
- In `Nuclear Plant`, use `Insert Rods`, `Withdraw`, `Pump A`, `Pump B`, `SCRAM`, `Vent`, `Load Up`, and `Load Down` to control the reactor panel.
- Adjust the interceptor speed slider to override the selected interceptor's default speed.
- Score increases for interceptions and enemy kills, and drops when hostile projectiles or enemies reach the base.

## Modes

- `Sandbox`: no automatic spawns. Manual buttons create single missiles, enemies, EW units, and interceptors.
- `Projectile Pilot`: you fly one projectile toward the base while the base fires interceptors at you.
- `Waves`: enemies spawn in waves; later waves can include radar jammers and EW aircraft.
- `Budget Waves`: waves get harder, kills award points, and radar/defense choices cost points.
- `Ground Assault`: vehicle-heavy attacks with ground speed affected by terrain.
- `Linked Defense`: wave mode with strict radar-to-defense compatibility, points, and placeable radar positioning.
- `Story`: HQ calls the radar site with changing orders, surprise events, and sound cues. Click `Answer HQ Phone` when it rings.
- `Nuclear Plant`: standalone plant operator mode. Manage rods, coolant pump trains, steam pressure, turbine load, grid demand, venting, and SCRAM with no enemies, missiles, radar tracks, or EW.

## Radar And Weapon Categories

The catalog is grouped by decade and role instead of being one giant list. Radar profiles carry a year, decade, era, sensor type, antenna type, scan pattern, HUD style, band label, category, strengths, weaknesses, scan-rate modifier, low-altitude behavior, stealth-detection modifier, jamming resistance, tracking precision, beam width, elevation coverage, and height accuracy. Weapons and defenses are categorized by decade and role, including cannons, missiles, lasers, rockets, mortars, artillery, bombs, cruise missiles, drones, anti-radiation missiles, aircraft, ground vehicles, launchers, stealth units, and EW units.

Radar year/decade categories are:

- `1930s`
- `1940s`
- `1950s`
- `1960s`
- `1970s`
- `1980s`
- `1990s`
- `2000s`
- `2010s`
- `2020s+`

## Radar Screens

The radar screen is architecture-aware. AESA-style radars do not use a rotating sweep; they draw multiple electronic beams and a glass tactical grid. PESA-style radars draw full circular range rings plus electronic sector lobes. Pulse-Doppler sets use a range-rate style grid. Height-finders emphasize altitude. Early radars draw a coarse analog scope. Soviet/Russian-style radars use green symbology with Russian-language range, azimuth, height, and target labels.

The public names are for game flavor and operator readability. Values are intentionally fictional balance numbers, not real tactical performance data.

## Story And Events

Story mode adds HQ phone calls, audible operator cues, and staged orders. Random events can interrupt normal play with mortar barrages, drone swarms, SEAD pressure, ground pushes, radiological interference, and fake tracks. These events are designed to keep the radar-operator feel while staying inside synthetic game-coordinate simulation.

## Nuclear Plant Mode

Nuclear plant mode is a game panel, not a real plant model. Reactor power, temperature, coolant, steam pressure, turbine load, generator output, grid demand, control rods, pump trains, feedwater flow, alarms, blackout state, vibration, and containment integrity interact as simplified simulation variables. SCRAM drops power quickly, venting reduces pressure and temperature at a coolant cost, and poor coolant/load balance can trigger alarms.

## Electronic Warfare

EW is modeled as fictional game logic only. Jammers create local noise, lower track confidence, and can generate ghost tracks. Stealth/EW units can fade in and out of visibility. Defender EW actions consume radar power:

- `ECCM Sweep`: clears ghost tracks and lowers jamming for a short period.
- `Burn Through`: improves track confidence and reveals intermittent targets.
- `Decoy Emitters`: reduces anti-radiation missile damage.
- `EMCON Silence`: reduces emissions, making radar-seeking missiles less reliable while shrinking radar coverage.

Each radar has different EW power capacity and recharge behavior.

## Simulation Notes

The simulation uses abstract game physics: acceleration toward max speed, simple drag, altitude/vertical-speed tracking, terrain-following bonuses, terrain masking, elevation coverage, beam width, clutter, track confidence, jamming noise, intermittent stealth, and anti-radiation behavior against the radar site. It is designed to feel like a radar-operator game, not to model real sensor or weapon performance.

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
