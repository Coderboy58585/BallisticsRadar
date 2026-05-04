from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt

from .models import Vector2


EPSILON = 1e-9


@dataclass(frozen=True, slots=True)
class InterceptSolution:
    point: Vector2
    time: float
    interceptor_velocity: Vector2


def solve_intercept(
    shooter_position: Vector2,
    target_position: Vector2,
    target_velocity: Vector2,
    interceptor_speed: float,
    *,
    max_time: float = 30.0,
) -> InterceptSolution | None:
    """Solve a game-space constant-velocity intercept.

    Returns None when the interceptor cannot catch the target within max_time.
    """
    if interceptor_speed <= 0:
        raise ValueError("interceptor_speed must be positive")
    if max_time <= 0:
        raise ValueError("max_time must be positive")

    relative_position = target_position - shooter_position
    a = target_velocity.dot(target_velocity) - interceptor_speed * interceptor_speed
    b = 2.0 * relative_position.dot(target_velocity)
    c = relative_position.dot(relative_position)

    if abs(a) < EPSILON:
        if abs(b) < EPSILON:
            if c < EPSILON:
                return InterceptSolution(
                    point=target_position,
                    time=0.0,
                    interceptor_velocity=Vector2(0.0, 0.0),
                )
            return None
        candidate_time = -c / b
        return _solution_from_time(
            shooter_position,
            target_position,
            target_velocity,
            interceptor_speed,
            candidate_time,
            max_time,
        )

    discriminant = b * b - 4.0 * a * c
    if discriminant < 0:
        return None

    root = sqrt(discriminant)
    times = sorted(((-b - root) / (2.0 * a), (-b + root) / (2.0 * a)))
    for candidate_time in times:
        solution = _solution_from_time(
            shooter_position,
            target_position,
            target_velocity,
            interceptor_speed,
            candidate_time,
            max_time,
        )
        if solution is not None:
            return solution
    return None


def _solution_from_time(
    shooter_position: Vector2,
    target_position: Vector2,
    target_velocity: Vector2,
    interceptor_speed: float,
    time: float,
    max_time: float,
) -> InterceptSolution | None:
    if not isfinite(time) or time < 0 or time > max_time:
        return None

    point = target_position + target_velocity * time
    direction = (point - shooter_position).normalized()
    return InterceptSolution(
        point=point,
        time=time,
        interceptor_velocity=direction * interceptor_speed,
    )
