import unittest

from game_radar.models import Vector2
from game_radar.tracker import Observation, RadarTracker


class TrackerTests(unittest.TestCase):
    def test_tracker_estimates_velocity(self) -> None:
        tracker = RadarTracker(smoothing=1.0)
        tracker.update(Observation(1, Vector2(0, 0), 0.0))
        track = tracker.update(Observation(1, Vector2(10, 0), 2.0))

        self.assertAlmostEqual(track.velocity.x, 5.0)
        self.assertAlmostEqual(track.velocity.y, 0.0)
        self.assertEqual(track.samples, 2)

    def test_prediction_uses_estimated_velocity(self) -> None:
        tracker = RadarTracker(smoothing=1.0)
        tracker.update(Observation(1, Vector2(0, 0), 0.0))
        track = tracker.update(Observation(1, Vector2(10, 0), 2.0))

        predicted = track.predict(4.0)

        self.assertAlmostEqual(predicted.x, 20.0)
        self.assertAlmostEqual(predicted.y, 0.0)

    def test_prune_removes_stale_tracks(self) -> None:
        tracker = RadarTracker(stale_after=1.0)
        tracker.update(Observation(1, Vector2(0, 0), 0.0))

        tracker.prune(2.0)

        self.assertEqual(tracker.tracks, ())


if __name__ == "__main__":
    unittest.main()
