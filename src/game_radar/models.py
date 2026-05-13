from __future__ import annotations

from dataclasses import dataclass
from math import hypot


@dataclass(frozen=True, slots=True)
class Vector2:
    x: float
    y: float

    def __add__(self, other: Vector2) -> Vector2:
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2) -> Vector2:
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vector2:
        return Vector2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> Vector2:
        return self * scalar

    def __truediv__(self, scalar: float) -> Vector2:
        if scalar == 0:
            raise ZeroDivisionError("cannot divide Vector2 by zero")
        return Vector2(self.x / scalar, self.y / scalar)

    def dot(self, other: Vector2) -> float:
        return self.x * other.x + self.y * other.y

    def magnitude(self) -> float:
        return hypot(self.x, self.y)

    def normalized(self) -> Vector2:
        length = self.magnitude()
        if length == 0:
            return Vector2(0.0, 0.0)
        return self / length

    def distance_to(self, other: Vector2) -> float:
        return (self - other).magnitude()

    def clamp(self, min_x: float, max_x: float, min_y: float, max_y: float) -> Vector2:
        return Vector2(
            min(max(self.x, min_x), max_x),
            min(max(self.y, min_y), max_y),
        )


ZERO = Vector2(0.0, 0.0)


@dataclass(frozen=True, slots=True)
class ProjectileProfile:
    name: str
    speed: float
    turn_rate: float
    radar_cross_section: float
    color: str
    damage: int = 1
    score_value: int = 10
    cost: int = 10
    ammo: int = 8
    role: str = "missile"
    terrain_following: bool = False
    radar_seeking: bool = False
    acceleration: float = 0.0
    max_speed: float = 0.0
    altitude_profile: str = "medium"
    cruise_altitude: float = 1200.0
    ballistic_apogee: float = 4500.0
    year: int = 2020
    decade: str = "2020s+"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("projectile profile name is required")
        if self.speed <= 0:
            raise ValueError("projectile speed must be positive")
        if self.turn_rate < 0:
            raise ValueError("turn rate cannot be negative")
        if self.radar_cross_section <= 0:
            raise ValueError("radar cross section must be positive")
        if self.damage <= 0:
            raise ValueError("projectile damage must be positive")
        if self.score_value < 0:
            raise ValueError("projectile score value cannot be negative")
        if self.cost < 0:
            raise ValueError("projectile cost cannot be negative")
        if self.ammo < 0:
            raise ValueError("projectile ammo cannot be negative")
        if self.acceleration < 0:
            raise ValueError("projectile acceleration cannot be negative")
        if self.max_speed < 0:
            raise ValueError("projectile max speed cannot be negative")
        if not self.altitude_profile:
            raise ValueError("projectile altitude profile is required")
        if self.cruise_altitude < 0:
            raise ValueError("projectile cruise altitude cannot be negative")
        if self.ballistic_apogee < 0:
            raise ValueError("projectile ballistic apogee cannot be negative")
        if self.year < 1900:
            raise ValueError("projectile year must be a catalog year")
        if not self.decade:
            raise ValueError("projectile decade is required")


@dataclass(frozen=True, slots=True)
class InterceptorProfile:
    name: str
    speed: float
    blast_radius: float
    color: str
    ammo: int = 10
    cost: int = 20
    power_cost: float = 0.0
    category: str = "missile"
    year: int = 2020
    decade: str = "2020s+"
    compatible_radars: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("interceptor profile name is required")
        if self.speed <= 0:
            raise ValueError("interceptor speed must be positive")
        if self.blast_radius <= 0:
            raise ValueError("interceptor blast radius must be positive")
        if self.ammo < 0:
            raise ValueError("interceptor ammo cannot be negative")
        if self.cost < 0:
            raise ValueError("interceptor cost cannot be negative")
        if self.power_cost < 0:
            raise ValueError("interceptor power cost cannot be negative")
        if self.year < 1900:
            raise ValueError("interceptor year must be a catalog year")
        if not self.decade:
            raise ValueError("interceptor decade is required")


@dataclass(frozen=True, slots=True)
class EnemyProfile:
    name: str
    speed: float
    launch_interval: float
    health: int
    score_value: int
    color: str
    projectile_names: tuple[str, ...]
    jammer_radius: float = 0.0
    jammer_strength: float = 0.0
    ghost_rate: float = 0.0
    platform: str = "air"
    can_damage_base: bool = False
    standoff_radius: float = 120.0
    stealth_period: float = 0.0
    stealth_duration: float = 0.0
    radar_damage: int = 0
    signature: float = 1.0
    altitude: float = 1200.0
    year: int = 2020
    decade: str = "2020s+"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("enemy profile name is required")
        if self.speed <= 0:
            raise ValueError("enemy speed must be positive")
        if self.launch_interval <= 0:
            raise ValueError("enemy launch interval must be positive")
        if self.health <= 0:
            raise ValueError("enemy health must be positive")
        if self.score_value < 0:
            raise ValueError("enemy score value cannot be negative")
        if not self.projectile_names:
            raise ValueError("enemy must have at least one projectile type")
        if self.jammer_radius < 0:
            raise ValueError("jammer radius cannot be negative")
        if self.jammer_strength < 0:
            raise ValueError("jammer strength cannot be negative")
        if self.ghost_rate < 0:
            raise ValueError("ghost rate cannot be negative")
        if self.standoff_radius < 0:
            raise ValueError("standoff radius cannot be negative")
        if self.stealth_period < 0:
            raise ValueError("stealth period cannot be negative")
        if self.stealth_duration < 0:
            raise ValueError("stealth duration cannot be negative")
        if self.radar_damage < 0:
            raise ValueError("radar damage cannot be negative")
        if self.signature <= 0:
            raise ValueError("enemy signature must be positive")
        if self.altitude < 0:
            raise ValueError("enemy altitude cannot be negative")
        if self.year < 1900:
            raise ValueError("enemy year must be a catalog year")
        if not self.decade:
            raise ValueError("enemy decade is required")


@dataclass(frozen=True, slots=True)
class RadarProfile:
    name: str
    range: float
    noise: float
    ew_power: float
    ew_regen: float
    terrain_resistance: float
    health: int
    cost: int
    color: str
    abilities: tuple[str, ...]
    era: str = "modern"
    sensor_type: str = "mechanical"
    band: str = "multi-band"
    category: str = "search"
    pros: tuple[str, ...] = ()
    cons: tuple[str, ...] = ()
    scan_rate: float = 1.0
    low_altitude_factor: float = 1.0
    stealth_detection: float = 0.0
    jamming_resistance: float = 0.0
    tracking_precision: float = 1.0
    year: int = 2020
    decade: str = "2020s+"
    antenna_type: str = "array"
    scan_pattern: str = "mechanical"
    hud_style: str = "western"
    height_accuracy: float = 1.0
    elevation_coverage: float = 60.0
    beam_width: float = 2.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("radar profile name is required")
        if self.range <= 0:
            raise ValueError("radar range must be positive")
        if self.noise <= 0:
            raise ValueError("radar noise must be positive")
        if self.ew_power <= 0:
            raise ValueError("EW power must be positive")
        if self.ew_regen < 0:
            raise ValueError("EW regen cannot be negative")
        if not 0 <= self.terrain_resistance <= 1:
            raise ValueError("terrain resistance must be in [0, 1]")
        if self.health <= 0:
            raise ValueError("radar health must be positive")
        if self.cost < 0:
            raise ValueError("radar cost cannot be negative")
        if not self.era:
            raise ValueError("radar era is required")
        if not self.sensor_type:
            raise ValueError("radar sensor type is required")
        if not self.band:
            raise ValueError("radar band is required")
        if not self.category:
            raise ValueError("radar category is required")
        if self.scan_rate <= 0:
            raise ValueError("radar scan rate must be positive")
        if self.low_altitude_factor <= 0:
            raise ValueError("radar low-altitude factor must be positive")
        if self.stealth_detection < 0:
            raise ValueError("radar stealth detection cannot be negative")
        if self.jamming_resistance < 0:
            raise ValueError("radar jamming resistance cannot be negative")
        if self.tracking_precision <= 0:
            raise ValueError("radar tracking precision must be positive")
        if self.year < 1900:
            raise ValueError("radar year must be realistic for radar history")
        if not self.decade:
            raise ValueError("radar decade is required")
        if not self.antenna_type:
            raise ValueError("radar antenna type is required")
        if not self.scan_pattern:
            raise ValueError("radar scan pattern is required")
        if not self.hud_style:
            raise ValueError("radar HUD style is required")
        if self.height_accuracy <= 0:
            raise ValueError("radar height accuracy must be positive")
        if self.elevation_coverage <= 0:
            raise ValueError("radar elevation coverage must be positive")
        if self.beam_width <= 0:
            raise ValueError("radar beam width must be positive")


@dataclass(frozen=True, slots=True)
class MapProfile:
    name: str
    radar_range_mult: float
    clutter: float
    projectile_drag: float
    ground_speed_mult: float
    terrain_shadow: float
    color: str
    description: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("map profile name is required")
        if self.radar_range_mult <= 0:
            raise ValueError("radar range multiplier must be positive")
        if self.clutter < 0:
            raise ValueError("clutter cannot be negative")
        if self.projectile_drag < 0:
            raise ValueError("projectile drag cannot be negative")
        if self.ground_speed_mult <= 0:
            raise ValueError("ground speed multiplier must be positive")
        if not 0 <= self.terrain_shadow <= 1:
            raise ValueError("terrain shadow must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class EWActionProfile:
    name: str
    cost: float
    duration: float
    effect: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("EW action name is required")
        if self.cost < 0:
            raise ValueError("EW action cost cannot be negative")
        if self.duration < 0:
            raise ValueError("EW action duration cannot be negative")


@dataclass(slots=True)
class Projectile:
    projectile_id: int
    profile: ProjectileProfile
    position: Vector2
    velocity: Vector2
    owner: str = "enemy"
    launcher_enemy_id: int | None = None
    launcher_platform: str = ""
    player_controlled: bool = False
    altitude: float = 0.0
    vertical_velocity: float = 0.0
    active: bool = True

    def step(self, dt: float) -> None:
        if dt <= 0:
            raise ValueError("dt must be positive")
        self.position = self.position + self.velocity * dt
        self.altitude = max(0.0, self.altitude + self.vertical_velocity * dt)


@dataclass(slots=True)
class Enemy:
    enemy_id: int
    profile: EnemyProfile
    position: Vector2
    velocity: Vector2
    next_launch_at: float
    health: int
    altitude: float = 0.0
    vertical_velocity: float = 0.0
    revealed_until: float = 0.0
    active: bool = True

    def step(self, dt: float) -> None:
        if dt <= 0:
            raise ValueError("dt must be positive")
        self.position = self.position + self.velocity * dt
        self.altitude = max(0.0, self.altitude + self.vertical_velocity * dt)


@dataclass(slots=True)
class Interceptor:
    interceptor_id: int
    profile: InterceptorProfile
    target_kind: str
    target_id: int
    position: Vector2
    velocity: Vector2
    intercept_point: Vector2
    time_remaining: float
    active: bool = True

    def step(self, dt: float) -> None:
        if dt <= 0:
            raise ValueError("dt must be positive")
        self.position = self.position + self.velocity * dt
        self.time_remaining -= dt
        if self.time_remaining <= 0:
            self.active = False


@dataclass(slots=True)
class RadarSite:
    site_id: int
    profile: RadarProfile
    position: Vector2
    health: int
    bearing_degrees: float = 90.0
    auto_scan: bool = True
    active: bool = True
