from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count
from math import cos, pi, sin
from random import Random

from .intercept import InterceptSolution, solve_intercept
from .models import Interceptor, Projectile, ProjectileProfile, Vector2
from .tracker import Observation, RadarTracker


WORLD_HALF_SIZE = 500.0

PROJECTILE_PROFILES: dict[str, ProjectileProfile] = {
    "Rocket": ProjectileProfile("Rocket", speed=105.0, turn_rate=0.0, radar_cross_section=1.0, color="#ff6b4a"),
    "Mortar": ProjectileProfile("Mortar", speed=78.0, turn_rate=0.0, radar_cross_section=0.7, color="#ffd166"),
    "Drone": ProjectileProfile("Drone", speed=46.0, turn_rate=0.4, radar_cross_section=1.4, color="#83c5be"),
    "Plasma": ProjectileProfile("Plasma", speed=140.0, turn_rate=0.0, radar_cross_section=0.45, color="#c77dff"),
}


@dataclass(slots=True)
class SimulationWorld:
    radar_radius: float = 480.0
    base_position: Vector2 = Vector2(0.0, 0.0)
    interceptor_speed: float = 180.0
    rng: Random = field(default_factory=lambda: Random(7))
    tracker: RadarTracker = field(default_factory=RadarTracker)
    projectiles: dict[int, Projectile] = field(default_factory=dict)
    interceptors: dict[int, Interceptor] = field(default_factory=dict)
    time: float = 0.0
    _projectile_ids: count = field(default_factory=lambda: count(1))
    _interceptor_ids: count = field(default_factory=lambda: count(1))

    def spawn_projectile(self, profile_name: str) -> Projectile:
        profile = PROJECTILE_PROFILES[profile_name]
        angle = self.rng.uniform(0, 2 * pi)
        spawn = Vector2(cos(angle), sin(angle)) * WORLD_HALF_SIZE
        aim_offset = Vector2(self.rng.uniform(-90, 90), self.rng.uniform(-90, 90))
        direction = (self.base_position + aim_offset - spawn).normalized()
        projectile = Projectile(
            projectile_id=next(self._projectile_ids),
            profile=profile,
            position=spawn,
            velocity=direction * profile.speed,
        )
        self.projectiles[projectile.projectile_id] = projectile
        return projectile

    def step(self, dt: float) -> None:
        if dt <= 0:
            raise ValueError("dt must be positive")
        self.time += dt

        for projectile in list(self.projectiles.values()):
            if projectile.active:
                projectile.step(dt)
            if projectile.position.distance_to(self.base_position) < 12:
                projectile.active = False
            if projectile.position.magnitude() > WORLD_HALF_SIZE * 1.4:
                projectile.active = False

        for interceptor in list(self.interceptors.values()):
            if interceptor.active:
                interceptor.step(dt)
                target = self.projectiles.get(interceptor.target_id)
                if target and target.active and interceptor.position.distance_to(target.position) < 18:
                    target.active = False
                    interceptor.active = False
                    self.tracker.remove(target.projectile_id)

        self.projectiles = {
            projectile_id: projectile
            for projectile_id, projectile in self.projectiles.items()
            if projectile.active
        }
        self.interceptors = {
            interceptor_id: interceptor
            for interceptor_id, interceptor in self.interceptors.items()
            if interceptor.active
        }

        self._scan()
        self.tracker.prune(self.time)

    def _scan(self) -> None:
        for projectile in self.projectiles.values():
            if projectile.position.distance_to(self.base_position) > self.radar_radius:
                continue

            noise = 3.0 / projectile.profile.radar_cross_section
            observed = Vector2(
                projectile.position.x + self.rng.uniform(-noise, noise),
                projectile.position.y + self.rng.uniform(-noise, noise),
            )
            self.tracker.update(
                Observation(
                    projectile_id=projectile.projectile_id,
                    position=observed,
                    timestamp=self.time,
                )
            )

    def best_intercept_for(self, projectile_id: int) -> InterceptSolution | None:
        track = next((item for item in self.tracker.tracks if item.projectile_id == projectile_id), None)
        if track is None:
            return None
        return solve_intercept(
            self.base_position,
            track.position,
            track.velocity,
            self.interceptor_speed,
            max_time=20.0,
        )

    def deploy_interceptor(self, projectile_id: int) -> Interceptor | None:
        solution = self.best_intercept_for(projectile_id)
        if solution is None:
            return None

        interceptor = Interceptor(
            interceptor_id=next(self._interceptor_ids),
            target_id=projectile_id,
            position=self.base_position,
            velocity=solution.interceptor_velocity,
            intercept_point=solution.point,
            time_remaining=solution.time,
        )
        self.interceptors[interceptor.interceptor_id] = interceptor
        return interceptor
