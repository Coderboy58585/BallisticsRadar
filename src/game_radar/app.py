from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .simulation import PROJECTILE_PROFILES, WORLD_HALF_SIZE, SimulationWorld


CANVAS_SIZE = 720
PADDING = 32
TICK_SECONDS = 0.05


class RadarApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Game Radar Intercept Simulator")
        self.minsize(980, 760)

        self.world = SimulationWorld()
        self.running = True
        self.next_auto_spawn_at = 2.0
        self.selected_profile = tk.StringVar(value="Rocket")
        self.status = tk.StringVar(value="Radar online")
        self.interceptor_speed = tk.DoubleVar(value=self.world.interceptor_speed)

        self._build_layout()
        self.after(50, self._tick)

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        shell = ttk.Frame(self, padding=14)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(shell, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="#071312", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        side = ttk.Frame(shell, padding=(14, 0, 0, 0), width=220)
        side.grid(row=0, column=1, sticky="ns")
        side.grid_propagate(False)

        ttk.Label(side, text="Projectile").grid(row=0, column=0, sticky="w")
        profile_menu = ttk.OptionMenu(
            side,
            self.selected_profile,
            self.selected_profile.get(),
            *PROJECTILE_PROFILES.keys(),
        )
        profile_menu.grid(row=1, column=0, sticky="ew", pady=(4, 12))

        ttk.Button(side, text="Spawn", command=self._spawn).grid(row=2, column=0, sticky="ew")
        ttk.Button(side, text="Deploy Best Intercept", command=self._deploy_best).grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(side, text="Pause / Resume", command=self._toggle_running).grid(row=4, column=0, sticky="ew", pady=(8, 18))

        ttk.Label(side, text="Interceptor speed").grid(row=5, column=0, sticky="w")
        speed = ttk.Scale(
            side,
            from_=80,
            to=320,
            variable=self.interceptor_speed,
            command=self._set_interceptor_speed,
        )
        speed.grid(row=6, column=0, sticky="ew", pady=(4, 18))

        self.readout = tk.Text(side, height=24, width=30, wrap="word", state="disabled")
        self.readout.grid(row=7, column=0, sticky="nsew")
        side.rowconfigure(7, weight=1)

        ttk.Label(side, textvariable=self.status).grid(row=8, column=0, sticky="ew", pady=(12, 0))

    def _spawn(self) -> None:
        projectile = self.world.spawn_projectile(self.selected_profile.get())
        self.status.set(f"Spawned {projectile.profile.name} #{projectile.projectile_id}")
        self._draw()

    def _deploy_best(self) -> None:
        tracks = sorted(
            self.world.tracker.tracks,
            key=lambda track: track.position.distance_to(self.world.base_position),
        )
        for track in tracks:
            interceptor = self.world.deploy_interceptor(track.projectile_id)
            if interceptor is not None:
                self.status.set(f"Interceptor #{interceptor.interceptor_id} assigned to track #{track.projectile_id}")
                self._draw()
                return
        self.status.set("No intercept solution available")

    def _toggle_running(self) -> None:
        self.running = not self.running
        self.status.set("Simulation running" if self.running else "Simulation paused")

    def _set_interceptor_speed(self, value: str) -> None:
        self.world.interceptor_speed = float(value)

    def _tick(self) -> None:
        if self.running:
            self.world.step(TICK_SECONDS)
            if self.world.time >= self.next_auto_spawn_at and len(self.world.projectiles) < 8:
                self.world.spawn_projectile(self.selected_profile.get())
                self.next_auto_spawn_at = self.world.time + 3.5
            self._draw()
        self.after(int(TICK_SECONDS * 1000), self._tick)

    def _world_to_canvas(self, x: float, y: float) -> tuple[float, float]:
        scale = (CANVAS_SIZE - PADDING * 2) / (WORLD_HALF_SIZE * 2)
        return (
            CANVAS_SIZE / 2 + x * scale,
            CANVAS_SIZE / 2 - y * scale,
        )

    def _draw(self) -> None:
        self.canvas.delete("all")
        self._draw_grid()
        self._draw_tracks()
        self._draw_projectiles()
        self._draw_interceptors()
        self._draw_base()
        self._update_readout()

    def _draw_grid(self) -> None:
        center = CANVAS_SIZE / 2
        radar_radius = CANVAS_SIZE / 2 - PADDING
        self.canvas.create_oval(
            center - radar_radius,
            center - radar_radius,
            center + radar_radius,
            center + radar_radius,
            outline="#1d6f64",
            width=2,
        )
        for fraction in (0.25, 0.5, 0.75):
            radius = radar_radius * fraction
            self.canvas.create_oval(
                center - radius,
                center - radius,
                center + radius,
                center + radius,
                outline="#123b38",
            )
        self.canvas.create_line(PADDING, center, CANVAS_SIZE - PADDING, center, fill="#123b38")
        self.canvas.create_line(center, PADDING, center, CANVAS_SIZE - PADDING, fill="#123b38")

    def _draw_base(self) -> None:
        x, y = self._world_to_canvas(self.world.base_position.x, self.world.base_position.y)
        self.canvas.create_oval(x - 8, y - 8, x + 8, y + 8, fill="#e9ff70", outline="")
        self.canvas.create_text(x, y + 22, text="BASE", fill="#d8f3dc", font=("Segoe UI", 9, "bold"))

    def _draw_projectiles(self) -> None:
        for projectile in self.world.projectiles.values():
            x, y = self._world_to_canvas(projectile.position.x, projectile.position.y)
            self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill=projectile.profile.color, outline="")

    def _draw_tracks(self) -> None:
        for track in self.world.tracker.tracks:
            x, y = self._world_to_canvas(track.position.x, track.position.y)
            predicted = track.predict(self.world.time + 2.5)
            px, py = self._world_to_canvas(predicted.x, predicted.y)
            self.canvas.create_line(x, y, px, py, fill="#9bf6ff", dash=(4, 4), width=2)
            self.canvas.create_oval(x - 9, y - 9, x + 9, y + 9, outline="#9bf6ff", width=2)
            self.canvas.create_text(x + 16, y - 12, text=f"#{track.projectile_id}", fill="#d8f3dc", anchor="w")

            solution = self.world.best_intercept_for(track.projectile_id)
            if solution is not None:
                ix, iy = self._world_to_canvas(solution.point.x, solution.point.y)
                self.canvas.create_oval(ix - 6, iy - 6, ix + 6, iy + 6, outline="#fefae0", width=2)
                bx, by = self._world_to_canvas(self.world.base_position.x, self.world.base_position.y)
                self.canvas.create_line(bx, by, ix, iy, fill="#fefae0", dash=(2, 6))

    def _draw_interceptors(self) -> None:
        for interceptor in self.world.interceptors.values():
            x, y = self._world_to_canvas(interceptor.position.x, interceptor.position.y)
            ix, iy = self._world_to_canvas(interceptor.intercept_point.x, interceptor.intercept_point.y)
            self.canvas.create_line(x, y, ix, iy, fill="#ffffff")
            self.canvas.create_rectangle(x - 4, y - 4, x + 4, y + 4, fill="#ffffff", outline="")

    def _update_readout(self) -> None:
        lines = [
            f"Time: {self.world.time:5.1f}s",
            f"Projectiles: {len(self.world.projectiles)}",
            f"Tracks: {len(self.world.tracker.tracks)}",
            f"Interceptors: {len(self.world.interceptors)}",
            f"Interceptor speed: {self.world.interceptor_speed:5.1f}",
            "",
        ]
        for track in sorted(self.world.tracker.tracks, key=lambda item: item.projectile_id):
            solution = self.world.best_intercept_for(track.projectile_id)
            eta = f"{solution.time:4.1f}s" if solution else "none"
            lines.append(
                f"#{track.projectile_id} pos=({track.position.x:6.1f}, {track.position.y:6.1f}) "
                f"vel={track.velocity.magnitude():5.1f} conf={track.confidence:.2f} eta={eta}"
            )

        self.readout.configure(state="normal")
        self.readout.delete("1.0", "end")
        self.readout.insert("1.0", "\n".join(lines))
        self.readout.configure(state="disabled")


def main() -> None:
    app = RadarApp()
    app.mainloop()


if __name__ == "__main__":
    main()
