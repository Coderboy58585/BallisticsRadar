import unittest

from game_radar.intercept import solve_intercept
from game_radar.models import Vector2


class InterceptTests(unittest.TestCase):
    def test_stationary_target_solution(self) -> None:
        solution = solve_intercept(Vector2(0, 0), Vector2(100, 0), Vector2(0, 0), 50)

        self.assertIsNotNone(solution)
        assert solution is not None
        self.assertAlmostEqual(solution.time, 2.0)
        self.assertAlmostEqual(solution.point.x, 100.0)
        self.assertAlmostEqual(solution.point.y, 0.0)

    def test_moving_target_solution(self) -> None:
        solution = solve_intercept(Vector2(0, 0), Vector2(100, 0), Vector2(10, 0), 60)

        self.assertIsNotNone(solution)
        assert solution is not None
        self.assertAlmostEqual(solution.time, 2.0)
        self.assertAlmostEqual(solution.point.x, 120.0)

    def test_no_solution_when_target_too_fast(self) -> None:
        solution = solve_intercept(Vector2(0, 0), Vector2(100, 0), Vector2(100, 0), 50, max_time=10)

        self.assertIsNone(solution)

    def test_rejects_bad_speed(self) -> None:
        with self.assertRaises(ValueError):
            solve_intercept(Vector2(0, 0), Vector2(10, 0), Vector2(0, 0), 0)


if __name__ == "__main__":
    unittest.main()
