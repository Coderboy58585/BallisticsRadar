from __future__ import annotations

from dataclasses import dataclass, field

from .models import Vector2, ZERO


@dataclass(frozen=True, slots=True)
class Observation:
    projectile_id: int
    position: Vector2
    timestamp: float
    altitude: float = 0.0
    source_name: str = ""
    track_mode: str = "surveillance-track"
    engageable: bool = True


@dataclass(slots=True)
class Track:
    projectile_id: int
    position: Vector2
    velocity: Vector2 = ZERO
    altitude: float = 0.0
    vertical_velocity: float = 0.0
    last_timestamp: float = 0.0
    confidence: float = 0.25
    samples: int = 1
    source_name: str = ""
    track_mode: str = "surveillance-track"
    engageable: bool = True

    def predict(self, timestamp: float) -> Vector2:
        dt = max(0.0, timestamp - self.last_timestamp)
        return self.position + self.velocity * dt

    def predict_altitude(self, timestamp: float) -> float:
        dt = max(0.0, timestamp - self.last_timestamp)
        return max(0.0, self.altitude + self.vertical_velocity * dt)


@dataclass(slots=True)
class RadarTracker:
    smoothing: float = 0.35
    stale_after: float = 3.0
    _tracks: dict[int, Track] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0 < self.smoothing <= 1:
            raise ValueError("smoothing must be in the range (0, 1]")
        if self.stale_after <= 0:
            raise ValueError("stale_after must be positive")

    @property
    def tracks(self) -> tuple[Track, ...]:
        return tuple(self._tracks.values())

    def update(self, observation: Observation) -> Track:
        if observation.timestamp < 0:
            raise ValueError("observation timestamp cannot be negative")

        track = self._tracks.get(observation.projectile_id)
        if track is None:
            track = Track(
                projectile_id=observation.projectile_id,
                position=observation.position,
                altitude=observation.altitude,
                last_timestamp=observation.timestamp,
                source_name=observation.source_name,
                track_mode=observation.track_mode,
                engageable=observation.engageable,
            )
            self._tracks[observation.projectile_id] = track
            return track

        dt = observation.timestamp - track.last_timestamp
        if dt <= 0:
            track.position = observation.position
            track.altitude = observation.altitude
            track.source_name = observation.source_name
            track.track_mode = observation.track_mode
            track.engageable = observation.engageable
            return track

        measured_velocity = (observation.position - track.position) / dt
        measured_vertical_velocity = (observation.altitude - track.altitude) / dt
        alpha = self.smoothing
        track.velocity = track.velocity * (1.0 - alpha) + measured_velocity * alpha
        track.vertical_velocity = track.vertical_velocity * (1.0 - alpha) + measured_vertical_velocity * alpha
        track.position = observation.position
        track.altitude = observation.altitude
        track.last_timestamp = observation.timestamp
        track.samples += 1
        track.source_name = observation.source_name
        track.track_mode = observation.track_mode
        track.engageable = observation.engageable
        track.confidence = min(1.0, track.confidence + 0.12)
        return track

    def prune(self, timestamp: float) -> None:
        stale_ids = [
            projectile_id
            for projectile_id, track in self._tracks.items()
            if timestamp - track.last_timestamp > self.stale_after
        ]
        for projectile_id in stale_ids:
            del self._tracks[projectile_id]

    def remove(self, projectile_id: int) -> None:
        self._tracks.pop(projectile_id, None)
