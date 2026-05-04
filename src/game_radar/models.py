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

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("projectile profile name is required")
        if self.speed <= 0:
            raise ValueError("projectile speed must be positive")
        if self.turn_rate < 0:
            raise ValueError("turn rate cannot be negative")
        if self.radar_cross_section <= 0:
            raise ValueError("radar cross section must be positive")


@dataclass(slots=True)
class Projectile:
    projectile_id: int
    profile: ProjectileProfile
    position: Vector2
    velocity: Vector2
    active: bool = True

    def step(self, dt: float) -> None:
        if dt <= 0:
            raise ValueError("dt must be positive")
        self.position = self.position + self.velocity * dt


@dataclass(slots=True)
class Interceptor:
    interceptor_id: int
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
