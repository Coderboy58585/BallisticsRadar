from __future__ import annotations

from collections.abc import Callable
import tkinter as tk
from math import cos, sin
from tkinter import ttk

from .models import Vector2
from .simulation import (
    CATALOG_DECADE_LABELS,
    ENEMY_PROFILES,
    EW_ACTIONS,
    EW_ACTION_MIN_YEARS,
    INTERCEPTOR_PROFILES,
    MAP_PROFILES,
    PROJECTILE_PROFILES,
    RADAR_DECADE_LABELS,
    RADAR_PROFILES,
    WORLD_HALF_SIZE,
    SimulationWorld,
)

try:
    import winsound
except ImportError:  # pragma: no cover - Windows-only nicety
    winsound = None

try:
    import win32com.client as win32com_client
except Exception:  # pragma: no cover - optional Windows speech bridge
    win32com_client = None


CANVAS_SIZE = 720
PADDING = 32
TICK_SECONDS = 0.05
MODE_OPTIONS = {
    "Sandbox": "sandbox",
    "Projectile Pilot": "projectile",
    "Waves": "waves",
    "Budget Waves": "budget_waves",
    "Ground Assault": "ground_assault",
    "Linked Defense": "linked_defense",
    "Story": "story",
    "Nuclear Plant": "nuclear_plant",
}
DISPLAY_OPTIONS = ("PPI Sweep", "B-Scope", "Sector Scan", "Tactical Map")
SOUND_CUES = (
    ("Wave", (880, 90)),
    ("Intercepted", (1240, 55)),
    ("Destroyed", (980, 70)),
    ("Hit", (830, 70)),
    ("damaged radar", (360, 130)),
    ("radar destroyed", (260, 180)),
    ("HQ phone", (940, 180)),
    ("HQ", (760, 90)),
    ("SCRAM", (180, 240)),
    ("Plant", (520, 120)),
    ("Grid synchronized", (660, 65)),
    ("pump", (480, 85)),
    ("Control rods", (420, 80)),
    ("Steam", (580, 95)),
    ("Turbine", (720, 85)),
    ("coolant", (390, 120)),
    ("Radiological", (300, 220)),
    ("Manual cannon", (1120, 60)),
    ("Sonic", (1320, 80)),
    ("Directional EW", (440, 120)),
    ("Hostile radar", (300, 150)),
    ("launched", (680, 55)),
    ("SEAD", (330, 160)),
    ("Mortar", (260, 140)),
    ("Drone", (1040, 55)),
    ("ghost", (430, 90)),
    ("out of ammo", (220, 110)),
    ("offline", (240, 120)),
    ("online", (880, 70)),
    ("ALARM", (250, 180)),
    ("failed", (160, 260)),
)


class RadarApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Game Radar Operator Simulator")
        self.minsize(1140, 800)

        self.world = SimulationWorld()
        self.running = True
        self.keys_pressed: set[str] = set()

        self.selected_mode = tk.StringVar(value="Sandbox")
        self.selected_projectile = tk.StringVar(value="9M22U Grad Rocket")
        self.selected_interceptor = tk.StringVar(value="Iron Dome Tamir")
        self.selected_enemy = tk.StringVar(value="Scout UAV")
        self.selected_radar = tk.StringVar(value=self.world.radar_profile_name)
        self.selected_radar_decade = tk.StringVar(value=self.world.current_radar.decade)
        self.selected_projectile_decade = tk.StringVar(value=PROJECTILE_PROFILES[self.selected_projectile.get()].decade)
        self.selected_projectile_role = tk.StringVar(value=PROJECTILE_PROFILES[self.selected_projectile.get()].role)
        self.selected_defense_decade = tk.StringVar(value=INTERCEPTOR_PROFILES[self.selected_interceptor.get()].decade)
        self.selected_defense_category = tk.StringVar(value=INTERCEPTOR_PROFILES[self.selected_interceptor.get()].category)
        self.selected_enemy_decade = tk.StringVar(value=ENEMY_PROFILES[self.selected_enemy.get()].decade)
        self.selected_enemy_group = tk.StringVar(value="Aircraft")
        self.selected_map = tk.StringVar(value=self.world.map_profile_name)
        self.selected_ew = tk.StringVar(value="ECCM Sweep")
        self.selected_display = tk.StringVar(value="PPI Sweep")
        self.sound_enabled = tk.BooleanVar(value=True)
        self.voice_enabled = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="Sandbox online")
        self.score_text = tk.StringVar(value="Score 0 | Base 10")
        self.speed_text = tk.StringVar()
        self.interceptor_speed = tk.DoubleVar(value=INTERCEPTOR_PROFILES["Iron Dome Tamir"].speed)
        self.voice = None
        self.hud_buttons: list[tuple[str, tuple[float, float, float, float]]] = []
        self.manual_fire_armed = tk.BooleanVar(value=False)
        self.place_radar_mode = tk.BooleanVar(value=False)
        self.aim_radar_mode = tk.BooleanVar(value=False)
        self.right_fire_active = False
        self.next_manual_fire_at = 0.0

        self._build_layout()
        self._sync_catalog_filters()
        self._sync_speed_label()
        self._bind_controls()
        self.after(50, self._tick)

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        shell = ttk.Frame(self, padding=14)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(shell, width=CANVAS_SIZE, height=CANVAS_SIZE, bg=self.world.current_map.color, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        side_shell = ttk.Frame(shell, padding=(14, 0, 0, 0), width=374)
        side_shell.grid(row=0, column=1, sticky="ns")
        side_shell.grid_propagate(False)
        side_shell.columnconfigure(0, weight=1)
        side_shell.rowconfigure(0, weight=1)
        self.side_canvas = tk.Canvas(side_shell, width=350, highlightthickness=0)
        self.side_canvas.grid(row=0, column=0, sticky="nsew")
        side_scroll = ttk.Scrollbar(side_shell, orient="vertical", command=self.side_canvas.yview)
        side_scroll.grid(row=0, column=1, sticky="ns")
        self.side_canvas.configure(yscrollcommand=side_scroll.set)
        side = ttk.Frame(self.side_canvas)
        self.side_window = self.side_canvas.create_window((0, 0), window=side, anchor="nw", width=350)
        side.bind("<Configure>", self._on_side_configure)
        self.side_canvas.bind("<Configure>", self._on_side_canvas_configure)
        self.side_canvas.bind("<Enter>", lambda _event: self._bind_side_mousewheel())
        self.side_canvas.bind("<Leave>", lambda _event: self._unbind_side_mousewheel())
        side.columnconfigure(0, weight=1)

        ttk.Label(side, textvariable=self.score_text, font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="ew")

        ttk.Label(side, text="Mode").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.OptionMenu(side, self.selected_mode, self.selected_mode.get(), *MODE_OPTIONS.keys(), command=self._mode_changed).grid(row=2, column=0, sticky="ew", pady=(4, 6))
        ttk.Button(side, text="Restart Mode", command=self._restart_mode).grid(row=3, column=0, sticky="ew")

        display_row = ttk.Frame(side)
        display_row.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        display_row.columnconfigure(0, weight=1)
        ttk.Label(display_row, text="Display").grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(display_row, text="Sound", variable=self.sound_enabled).grid(row=0, column=1, sticky="e")
        ttk.Checkbutton(display_row, text="Speech", variable=self.voice_enabled).grid(row=0, column=2, sticky="e")
        ttk.OptionMenu(side, self.selected_display, self.selected_display.get(), *DISPLAY_OPTIONS, command=lambda _value: self._draw()).grid(row=5, column=0, sticky="ew", pady=(4, 6))

        ttk.Label(side, text="Map").grid(row=6, column=0, sticky="w", pady=(8, 0))
        ttk.OptionMenu(side, self.selected_map, self.selected_map.get(), *MAP_PROFILES.keys(), command=self._map_changed).grid(row=7, column=0, sticky="ew", pady=(4, 6))

        ttk.Label(side, text="Radar decade").grid(row=8, column=0, sticky="w", pady=(8, 0))
        self.radar_decade_menu = ttk.OptionMenu(side, self.selected_radar_decade, self.selected_radar_decade.get(), *RADAR_DECADE_LABELS, command=self._radar_decade_changed)
        self.radar_decade_menu.grid(row=9, column=0, sticky="ew", pady=(4, 6))
        ttk.Label(side, text="Radar").grid(row=10, column=0, sticky="w")
        self.radar_menu = ttk.OptionMenu(side, self.selected_radar, self.selected_radar.get(), *self._radars_for_selected_decade(), command=self._radar_changed)
        self.radar_menu.grid(row=11, column=0, sticky="ew", pady=(4, 6))
        ttk.Button(side, text="Install / Switch Radar", command=self._install_radar).grid(row=12, column=0, sticky="ew")

        ttk.Separator(side).grid(row=13, column=0, sticky="ew", pady=10)

        ttk.Label(side, text="Projectile decade").grid(row=14, column=0, sticky="w")
        self.projectile_decade_menu = ttk.OptionMenu(side, self.selected_projectile_decade, self.selected_projectile_decade.get(), *self._catalog_decades(), command=self._projectile_decade_changed)
        self.projectile_decade_menu.grid(row=15, column=0, sticky="ew", pady=(4, 6))
        ttk.Label(side, text="Projectile role").grid(row=16, column=0, sticky="w")
        self.projectile_role_menu = ttk.OptionMenu(side, self.selected_projectile_role, self.selected_projectile_role.get(), *self._projectile_roles(), command=self._projectile_role_changed)
        self.projectile_role_menu.grid(row=17, column=0, sticky="ew", pady=(4, 6))
        ttk.Label(side, text="Missile / projectile").grid(row=18, column=0, sticky="w")
        self.projectile_menu = ttk.OptionMenu(side, self.selected_projectile, self.selected_projectile.get(), *self._projectiles_for_selected_role(), command=self._projectile_changed)
        self.projectile_menu.grid(row=19, column=0, sticky="ew", pady=(4, 6))
        ttk.Button(side, text="Launch Single Round", command=self._spawn_projectile).grid(row=20, column=0, sticky="ew")
        ttk.Button(side, text="Play As Projectile", command=self._play_projectile).grid(row=21, column=0, sticky="ew", pady=(6, 0))

        ttk.Label(side, text="Enemy / vehicle decade").grid(row=22, column=0, sticky="w", pady=(10, 0))
        self.enemy_decade_menu = ttk.OptionMenu(side, self.selected_enemy_decade, self.selected_enemy_decade.get(), *self._catalog_decades(), command=self._enemy_decade_changed)
        self.enemy_decade_menu.grid(row=23, column=0, sticky="ew", pady=(4, 6))
        ttk.Label(side, text="Enemy / vehicle group").grid(row=24, column=0, sticky="w")
        self.enemy_group_menu = ttk.OptionMenu(side, self.selected_enemy_group, self.selected_enemy_group.get(), *self._enemy_groups(), command=self._enemy_group_changed)
        self.enemy_group_menu.grid(row=25, column=0, sticky="ew", pady=(4, 6))
        self.enemy_menu = ttk.OptionMenu(side, self.selected_enemy, self.selected_enemy.get(), *self._enemies_for_selected_group(), command=self._enemy_changed)
        self.enemy_menu.grid(row=26, column=0, sticky="ew", pady=(4, 6))
        ttk.Button(side, text="Spawn Single Enemy", command=self._spawn_enemy).grid(row=27, column=0, sticky="ew")

        ttk.Separator(side).grid(row=28, column=0, sticky="ew", pady=10)

        ttk.Label(side, text="Defense decade").grid(row=29, column=0, sticky="w")
        self.defense_decade_menu = ttk.OptionMenu(side, self.selected_defense_decade, self.selected_defense_decade.get(), *self._catalog_decades(), command=self._defense_decade_changed)
        self.defense_decade_menu.grid(row=30, column=0, sticky="ew", pady=(4, 6))
        ttk.Label(side, text="Defense class").grid(row=31, column=0, sticky="w")
        self.defense_category_menu = ttk.OptionMenu(side, self.selected_defense_category, self.selected_defense_category.get(), *self._defense_categories(), command=self._defense_category_changed)
        self.defense_category_menu.grid(row=32, column=0, sticky="ew", pady=(4, 6))
        self.interceptor_menu = ttk.OptionMenu(side, self.selected_interceptor, self.selected_interceptor.get(), *self._interceptors_for_selected_category(), command=self._interceptor_changed)
        self.interceptor_menu.grid(row=33, column=0, sticky="ew", pady=(4, 6))

        speed_row = ttk.Frame(side)
        speed_row.grid(row=34, column=0, sticky="ew")
        speed_row.columnconfigure(0, weight=1)
        ttk.Label(speed_row, text="Speed").grid(row=0, column=0, sticky="w")
        ttk.Label(speed_row, textvariable=self.speed_text, width=8, anchor="e").grid(row=0, column=1, sticky="e")
        ttk.Scale(side, from_=80, to=380, variable=self.interceptor_speed, command=self._set_interceptor_speed).grid(row=35, column=0, sticky="ew", pady=(4, 8))

        ttk.Button(side, text="Deploy Best Intercept", command=self._deploy_best).grid(row=36, column=0, sticky="ew")
        ttk.Button(side, text="Manual Cannon Fire", command=self._manual_cannon_fire).grid(row=37, column=0, sticky="ew", pady=(6, 0))
        ttk.Checkbutton(side, text="Arm Right-Click Cannon", variable=self.manual_fire_armed).grid(row=38, column=0, sticky="w", pady=(4, 0))
        ttk.Button(side, text="Strike Nearest Tracked Enemy", command=self._strike_enemy).grid(row=39, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(side, text="Sonic Cone Pulse", command=self._sonic_pulse).grid(row=40, column=0, sticky="ew", pady=(6, 0))
        radar_control_row = ttk.Frame(side)
        radar_control_row.grid(row=41, column=0, sticky="ew", pady=(8, 0))
        radar_control_row.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        ttk.Checkbutton(radar_control_row, text="Place", variable=self.place_radar_mode).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(radar_control_row, text="Aim", variable=self.aim_radar_mode).grid(row=0, column=1, sticky="w")
        ttk.Button(radar_control_row, text="<", command=lambda: self._slew_radar(-15.0)).grid(row=0, column=2, sticky="ew", padx=(4, 0))
        ttk.Button(radar_control_row, text=">", command=lambda: self._slew_radar(15.0)).grid(row=0, column=3, sticky="ew", padx=(4, 0))
        ttk.Button(radar_control_row, text="AUTO", command=self._auto_radar).grid(row=0, column=4, sticky="ew", padx=(4, 0))
        ttk.Button(radar_control_row, text="HOST", command=self._spawn_enemy_radar).grid(row=0, column=5, sticky="ew", padx=(4, 0))

        ttk.Label(side, text="Radar repair wires").grid(row=42, column=0, sticky="w", pady=(10, 0))
        wire_row = ttk.Frame(side)
        wire_row.grid(row=43, column=0, sticky="ew", pady=(4, 6))
        wire_row.columnconfigure((0, 1, 2, 3), weight=1)
        for index, wire in enumerate(("red", "blue", "green", "yellow")):
            ttk.Button(wire_row, text=wire.title(), command=lambda color=wire: self._repair_wire(color)).grid(row=0, column=index, sticky="ew", padx=(0 if index == 0 else 4, 0))

        ttk.Label(side, text="Defender EW / Orders").grid(row=44, column=0, sticky="w", pady=(10, 0))
        self.ew_menu = ttk.OptionMenu(side, self.selected_ew, self.selected_ew.get(), *self._ew_actions_for_current_radar())
        self.ew_menu.grid(row=45, column=0, sticky="ew", pady=(4, 6))
        ttk.Button(side, text="Use EW Power", command=self._use_ew).grid(row=46, column=0, sticky="ew")
        ttk.Button(side, text="Answer HQ Phone", command=self._answer_hq).grid(row=47, column=0, sticky="ew", pady=(6, 0))

        plant_row = ttk.Frame(side)
        plant_row.grid(row=48, column=0, sticky="ew", pady=(8, 0))
        plant_row.columnconfigure((0, 1), weight=1)
        ttk.Button(plant_row, text="Insert Rods", command=self._plant_insert).grid(row=0, column=0, sticky="ew")
        ttk.Button(plant_row, text="Withdraw", command=self._plant_withdraw).grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ttk.Button(plant_row, text="Pump A", command=self._plant_pump_a).grid(row=1, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(plant_row, text="Pump B", command=self._plant_pump_b).grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=(6, 0))
        ttk.Button(plant_row, text="SCRAM", command=self._plant_scram).grid(row=2, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(plant_row, text="Vent", command=self._plant_vent).grid(row=2, column=1, sticky="ew", padx=(6, 0), pady=(6, 0))
        ttk.Button(plant_row, text="Load Up", command=self._plant_load_up).grid(row=3, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(plant_row, text="Load Down", command=self._plant_load_down).grid(row=3, column=1, sticky="ew", padx=(6, 0), pady=(6, 0))

        ttk.Button(side, text="Pause / Resume", command=self._toggle_running).grid(row=49, column=0, sticky="ew", pady=(8, 10))

        self.readout = tk.Text(side, height=11, width=42, wrap="word", state="disabled")
        self.readout.grid(row=50, column=0, sticky="nsew")
        side.rowconfigure(50, weight=1)

        ttk.Label(side, textvariable=self.status, wraplength=330).grid(row=51, column=0, sticky="ew", pady=(10, 0))

    def _bind_controls(self) -> None:
        self.bind("<KeyPress>", self._on_key_press)
        self.bind("<KeyRelease>", self._on_key_release)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<ButtonPress-3>", self._on_manual_fire_press)
        self.canvas.bind("<B3-Motion>", self._on_manual_fire_drag)
        self.canvas.bind("<ButtonRelease-3>", self._on_manual_fire_release)
        self.focus_set()

    def _on_side_configure(self, _event: tk.Event) -> None:
        self.side_canvas.configure(scrollregion=self.side_canvas.bbox("all"))

    def _on_side_canvas_configure(self, event: tk.Event) -> None:
        self.side_canvas.itemconfigure(self.side_window, width=event.width)

    def _bind_side_mousewheel(self) -> None:
        self.bind_all("<MouseWheel>", self._on_side_mousewheel)
        self.bind_all("<Button-4>", self._on_side_mousewheel)
        self.bind_all("<Button-5>", self._on_side_mousewheel)

    def _unbind_side_mousewheel(self) -> None:
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")

    def _on_side_mousewheel(self, event: tk.Event) -> None:
        if getattr(event, "num", None) == 4:
            delta = -3
        elif getattr(event, "num", None) == 5:
            delta = 3
        else:
            delta = -1 * int(event.delta / 120)
        self.side_canvas.yview_scroll(delta, "units")

    def _replace_option_values(
        self,
        widget: ttk.OptionMenu,
        variable: tk.StringVar,
        values: tuple[str, ...],
        command: Callable[[str], None] | None = None,
    ) -> None:
        menu = self.nametowidget(str(widget["menu"]))
        menu.delete(0, "end")
        if not values:
            values = ("No entries",)
        for value in values:
            menu.add_command(label=value, command=lambda selected=value: self._select_option(variable, selected, command))

    def _select_option(self, variable: tk.StringVar, value: str, command: Callable[[str], None] | None) -> None:
        variable.set(value)
        if command is not None:
            command(value)

    def _projectile_roles(self) -> tuple[str, ...]:
        preferred = ("anti-radiation", "ballistic", "bomb", "cruise", "drone", "rocket", "missile")
        roles = {profile.role for profile in PROJECTILE_PROFILES.values()}
        return tuple(role for role in preferred if role in roles) + tuple(sorted(roles.difference(preferred)))

    def _defense_categories(self) -> tuple[str, ...]:
        preferred = ("gun", "missile", "sonic", "directed-energy")
        categories = {profile.category for profile in INTERCEPTOR_PROFILES.values()}
        return tuple(category for category in preferred if category in categories) + tuple(sorted(categories.difference(preferred)))

    def _enemy_groups(self) -> tuple[str, ...]:
        return ("Aircraft", "UAVs", "Ground vehicles", "Electronic warfare")

    def _catalog_decades(self) -> tuple[str, ...]:
        return ("All decades",) + CATALOG_DECADE_LABELS

    def _decade_matches(self, selected: str, profile_decade: str) -> bool:
        return selected == "All decades" or selected == profile_decade

    def _ew_actions_for_current_radar(self) -> tuple[str, ...]:
        radar_year = self.world.current_radar.year
        return tuple(name for name in EW_ACTIONS if EW_ACTION_MIN_YEARS.get(name, 1935) <= radar_year)

    def _enemy_group_for_profile(self, name: str) -> str:
        profile = ENEMY_PROFILES[name]
        text = f"{name} {profile.platform}".lower()
        if profile.jammer_strength > 0 or "jammer" in text or " ew " in f" {text} ":
            return "Electronic warfare"
        if profile.platform == "ground":
            return "Ground vehicles"
        if "uav" in text or "drone" in text or "loiter" in text:
            return "UAVs"
        return "Aircraft"

    def _radars_for_selected_decade(self) -> tuple[str, ...]:
        decade = self.selected_radar_decade.get()
        return tuple(name for name, profile in RADAR_PROFILES.items() if profile.decade == decade)

    def _projectiles_for_selected_role(self) -> tuple[str, ...]:
        role = self.selected_projectile_role.get()
        decade = self.selected_projectile_decade.get()
        return tuple(name for name, profile in PROJECTILE_PROFILES.items() if profile.role == role and self._decade_matches(decade, profile.decade))

    def _interceptors_for_selected_category(self) -> tuple[str, ...]:
        category = self.selected_defense_category.get()
        decade = self.selected_defense_decade.get()
        return tuple(name for name, profile in INTERCEPTOR_PROFILES.items() if profile.category == category and self._decade_matches(decade, profile.decade))

    def _enemies_for_selected_group(self) -> tuple[str, ...]:
        group = self.selected_enemy_group.get()
        decade = self.selected_enemy_decade.get()
        return tuple(name for name, profile in ENEMY_PROFILES.items() if self._enemy_group_for_profile(name) == group and self._decade_matches(decade, profile.decade))

    def _keep_selection(self, variable: tk.StringVar, values: tuple[str, ...]) -> None:
        if values and variable.get() not in values:
            variable.set(values[0])

    def _sync_catalog_filters(self) -> None:
        self.selected_radar_decade.set(RADAR_PROFILES[self.selected_radar.get()].decade)
        self.selected_projectile_decade.set(PROJECTILE_PROFILES[self.selected_projectile.get()].decade)
        self.selected_projectile_role.set(PROJECTILE_PROFILES[self.selected_projectile.get()].role)
        self.selected_defense_decade.set(INTERCEPTOR_PROFILES[self.selected_interceptor.get()].decade)
        self.selected_defense_category.set(INTERCEPTOR_PROFILES[self.selected_interceptor.get()].category)
        self.selected_enemy_decade.set(ENEMY_PROFILES[self.selected_enemy.get()].decade)
        self.selected_enemy_group.set(self._enemy_group_for_profile(self.selected_enemy.get()))

        self._replace_option_values(self.radar_decade_menu, self.selected_radar_decade, RADAR_DECADE_LABELS, self._radar_decade_changed)
        self._replace_option_values(self.projectile_decade_menu, self.selected_projectile_decade, self._catalog_decades(), self._projectile_decade_changed)
        self._replace_option_values(self.projectile_role_menu, self.selected_projectile_role, self._projectile_roles(), self._projectile_role_changed)
        self._replace_option_values(self.defense_decade_menu, self.selected_defense_decade, self._catalog_decades(), self._defense_decade_changed)
        self._replace_option_values(self.defense_category_menu, self.selected_defense_category, self._defense_categories(), self._defense_category_changed)
        self._replace_option_values(self.enemy_decade_menu, self.selected_enemy_decade, self._catalog_decades(), self._enemy_decade_changed)
        self._replace_option_values(self.enemy_group_menu, self.selected_enemy_group, self._enemy_groups(), self._enemy_group_changed)

        self._refresh_radar_menu()
        self._refresh_projectile_menu()
        self._refresh_enemy_menu()
        self._refresh_interceptor_menu()
        self._refresh_ew_menu()

    def _refresh_radar_menu(self) -> None:
        values = self._radars_for_selected_decade()
        self._keep_selection(self.selected_radar, values)
        self._replace_option_values(self.radar_menu, self.selected_radar, values, self._radar_changed)

    def _refresh_projectile_menu(self) -> None:
        values = self._projectiles_for_selected_role()
        if not values and self.selected_projectile_decade.get() != "All decades":
            self.selected_projectile_decade.set("All decades")
            values = self._projectiles_for_selected_role()
        self._keep_selection(self.selected_projectile, values)
        self._replace_option_values(self.projectile_menu, self.selected_projectile, values, self._projectile_changed)

    def _refresh_enemy_menu(self) -> None:
        values = self._enemies_for_selected_group()
        if not values and self.selected_enemy_decade.get() != "All decades":
            self.selected_enemy_decade.set("All decades")
            values = self._enemies_for_selected_group()
        self._keep_selection(self.selected_enemy, values)
        self._replace_option_values(self.enemy_menu, self.selected_enemy, values, self._enemy_changed)

    def _refresh_interceptor_menu(self) -> None:
        values = self._interceptors_for_selected_category()
        if not values and self.selected_defense_decade.get() != "All decades":
            self.selected_defense_decade.set("All decades")
            values = self._interceptors_for_selected_category()
        self._keep_selection(self.selected_interceptor, values)
        self._replace_option_values(self.interceptor_menu, self.selected_interceptor, values, self._interceptor_changed)

    def _refresh_ew_menu(self) -> None:
        values = self._ew_actions_for_current_radar()
        self._keep_selection(self.selected_ew, values)
        self._replace_option_values(self.ew_menu, self.selected_ew, values)

    def _radar_decade_changed(self, value: str) -> None:
        self.selected_radar_decade.set(value)
        self._refresh_radar_menu()
        self._radar_changed(self.selected_radar.get())
        self._draw()

    def _projectile_role_changed(self, value: str) -> None:
        self.selected_projectile_role.set(value)
        self._refresh_projectile_menu()
        self._set_status(f"Projectile catalog filtered to {value}")

    def _projectile_decade_changed(self, value: str) -> None:
        self.selected_projectile_decade.set(value)
        self._refresh_projectile_menu()
        self._set_status(f"Projectile catalog filtered to {value}")

    def _projectile_changed(self, value: str) -> None:
        if value not in PROJECTILE_PROFILES:
            return
        profile = PROJECTILE_PROFILES[value]
        self.selected_projectile_decade.set(profile.decade)
        self.selected_projectile_role.set(profile.role)
        self._set_status(f"Selected {profile.name} [{profile.year}, {profile.role}]")

    def _enemy_group_changed(self, value: str) -> None:
        self.selected_enemy_group.set(value)
        self._refresh_enemy_menu()
        self._set_status(f"Enemy catalog filtered to {value}")

    def _enemy_decade_changed(self, value: str) -> None:
        self.selected_enemy_decade.set(value)
        self._refresh_enemy_menu()
        self._set_status(f"Enemy catalog filtered to {value}")

    def _enemy_changed(self, value: str) -> None:
        if value not in ENEMY_PROFILES:
            return
        profile = ENEMY_PROFILES[value]
        self.selected_enemy_decade.set(profile.decade)
        self.selected_enemy_group.set(self._enemy_group_for_profile(value))
        self._set_status(f"Selected {profile.name} [{profile.year}]")

    def _defense_category_changed(self, value: str) -> None:
        self.selected_defense_category.set(value)
        self._refresh_interceptor_menu()
        self._sync_selected_interceptor_speed()

    def _defense_decade_changed(self, value: str) -> None:
        self.selected_defense_decade.set(value)
        self._refresh_interceptor_menu()
        self._sync_selected_interceptor_speed()

    def _mode_changed(self, value: str) -> None:
        self.world.set_game_mode(MODE_OPTIONS[value], player_projectile_name=self.selected_projectile.get())
        self.running = True
        self._set_status(f"{value} mode started")
        self.keys_pressed.clear()
        self._update_player_control()
        self._draw()

    def _restart_mode(self) -> None:
        self._mode_changed(self.selected_mode.get())

    def _map_changed(self, value: str) -> None:
        self.world.set_map_profile(value)
        self._set_status(MAP_PROFILES[value].description)
        self._draw()

    def _radar_changed(self, value: str) -> None:
        profile = RADAR_PROFILES[value]
        self._set_status(f"{profile.name} [{profile.era}, {profile.sensor_type}, {profile.band}]: {', '.join(profile.abilities)}")

    def _install_radar(self) -> None:
        if self._plant_mode_blocks_radar():
            return
        self.world.set_radar_profile(self.selected_radar.get())
        self._refresh_ew_menu()
        events = self.world.consume_events()
        if events:
            self._set_status(events[-1])
        self._draw()

    def _spawn_projectile(self) -> None:
        if self._plant_mode_blocks_radar():
            return
        projectile = self.world.manual_spawn_projectile(self.selected_projectile.get())
        events = self.world.consume_events()
        if projectile is not None:
            self._set_status(f"Launched {projectile.profile.name} #{projectile.projectile_id}")
        elif events:
            self._set_status(events[-1])
        self._draw()

    def _spawn_enemy(self) -> None:
        if self._plant_mode_blocks_radar():
            return
        enemy = self.world.spawn_enemy(self.selected_enemy.get())
        if enemy.profile.jammer_strength > 0:
            self._set_status(f"Spawned {enemy.profile.name} #{enemy.enemy_id}: EW emitter active")
        elif enemy.profile.stealth_period > 0:
            self._set_status(f"Spawned {enemy.profile.name} #{enemy.enemy_id}: intermittent track")
        else:
            self._set_status(f"Spawned {enemy.profile.name} #{enemy.enemy_id}")
        self._draw()

    def _spawn_enemy_radar(self) -> None:
        if self._plant_mode_blocks_radar():
            return
        site = self.world.spawn_hostile_radar(self.selected_radar.get())
        self._set_status(f"Hostile radar #{site.site_id} online: {site.profile.name}")
        self._draw()

    def _play_projectile(self) -> None:
        if self._plant_mode_blocks_radar():
            return
        self.selected_mode.set("Projectile Pilot")
        self.world.set_game_mode("projectile", player_projectile_name=self.selected_projectile.get())
        projectile = self.world.projectiles[self.world.player_projectile_id]
        self._set_status(f"Steering {projectile.profile.name} #{projectile.projectile_id} with WASD or arrows")
        self.running = True
        self.canvas.focus_set()
        self.focus_set()
        self._draw()

    def _deploy_best(self) -> None:
        if self._plant_mode_blocks_radar():
            return
        tracks = sorted(
            (track for track in self.world.tracker.tracks if not self.world.is_ghost_track(track.projectile_id)),
            key=lambda track: track.position.distance_to(self.world.base_position),
        )
        for track in tracks:
            interceptor = self.world.deploy_interceptor(
                track.projectile_id,
                self.selected_interceptor.get(),
                speed_override=self.world.interceptor_speed,
            )
            events = self.world.consume_events()
            if interceptor is not None:
                self._set_status(f"{interceptor.profile.name} #{interceptor.interceptor_id} assigned to track #{track.projectile_id}")
                self._draw()
                return
            if events:
                self._set_status(events[-1])
        self._set_status("No launchable projectile intercept available")

    def _manual_cannon_fire(self) -> None:
        if self._plant_mode_blocks_radar():
            return
        fired = self.world.manual_cannon_fire(self.selected_interceptor.get())
        events = self.world.consume_events()
        if events:
            self._set_status(events[-1])
        elif fired:
            self._set_status("Manual cannon fired")
        self._draw()

    def _sonic_pulse(self) -> None:
        if self._plant_mode_blocks_radar():
            return
        fired = self.world.use_sonic_weapon(self.selected_interceptor.get())
        events = self.world.consume_events()
        if events:
            self._set_status(events[-1])
        elif fired:
            self._set_status("Sonic cone pulse fired")
        self._draw()

    def _strike_enemy(self) -> None:
        if self._plant_mode_blocks_radar():
            return
        enemies = sorted(
            self.world.tracked_enemies(require_engageable=True),
            key=lambda enemy: self.world.enemy_track_for(enemy.enemy_id, require_engageable=True).position.distance_to(self.world.base_position),
        )
        for enemy in enemies:
            interceptor = self.world.deploy_interceptor_at_enemy(
                enemy.enemy_id,
                self.selected_interceptor.get(),
                speed_override=self.world.interceptor_speed,
            )
            events = self.world.consume_events()
            if interceptor is not None:
                self._set_status(f"{interceptor.profile.name} #{interceptor.interceptor_id} striking {enemy.profile.name} #{enemy.enemy_id}")
                self._draw()
                return
            if events:
                self._set_status(events[-1])
        self._set_status("No weapon-quality enemy track available")

    def _use_ew(self) -> None:
        if self._plant_mode_blocks_radar():
            return
        self.world.use_defender_ew(self.selected_ew.get())
        events = self.world.consume_events()
        if events:
            self._set_status(events[-1])
        self._draw()

    def _slew_radar(self, delta_degrees: float) -> None:
        if self._plant_mode_blocks_radar():
            return
        self.world.slew_primary_radar(delta_degrees)
        self._show_latest_event()

    def _auto_radar(self) -> None:
        if self._plant_mode_blocks_radar():
            return
        self.world.resume_auto_radar_scan()
        self._show_latest_event()

    def _answer_hq(self) -> None:
        call = self.world.answer_hq_call()
        events = self.world.consume_events()
        if call:
            self._speak_hq(call)
            self._set_status(call)
        elif events:
            self._set_status(events[-1])
        self._draw()

    def _repair_wire(self, color: str) -> None:
        self.world.repair_radar_wire(color)
        self._show_latest_event()

    def _plant_insert(self) -> None:
        self.world.plant_insert_rods()
        self._show_latest_event()

    def _plant_withdraw(self) -> None:
        self.world.plant_withdraw_rods()
        self._show_latest_event()

    def _plant_pumps(self) -> None:
        self.world.plant_toggle_pumps()
        self._show_latest_event()

    def _plant_pump_a(self) -> None:
        self.world.plant_toggle_pump_a()
        self._show_latest_event()

    def _plant_pump_b(self) -> None:
        self.world.plant_toggle_pump_b()
        self._show_latest_event()

    def _plant_scram(self) -> None:
        self.world.plant_scram()
        self._show_latest_event()

    def _plant_vent(self) -> None:
        self.world.plant_vent_steam()
        self._show_latest_event()

    def _plant_load_cycle(self) -> None:
        if self.world.turbine_load < 70:
            self.world.plant_raise_load()
        else:
            self.world.plant_lower_load()
        self._show_latest_event()

    def _plant_load_up(self) -> None:
        self.world.plant_raise_load()
        self._show_latest_event()

    def _plant_load_down(self) -> None:
        self.world.plant_lower_load()
        self._show_latest_event()

    def _show_latest_event(self) -> None:
        events = self.world.consume_events()
        if events:
            self._set_status(events[-1])
        self._draw()

    def _plant_mode_blocks_radar(self) -> bool:
        if self.world.game_mode != "nuclear_plant":
            return False
        self._set_status("Nuclear plant mode is standalone: radar, enemies, weapons, and EW are offline")
        self._draw()
        return True

    def _toggle_running(self) -> None:
        self.running = not self.running
        self._set_status("Simulation running" if self.running else "Simulation paused")

    def _interceptor_changed(self, value: str) -> None:
        if value not in INTERCEPTOR_PROFILES:
            return
        profile = INTERCEPTOR_PROFILES[value]
        self.selected_defense_decade.set(profile.decade)
        self.selected_defense_category.set(profile.category)
        self._sync_selected_interceptor_speed()

    def _sync_selected_interceptor_speed(self) -> None:
        if self.selected_interceptor.get() not in INTERCEPTOR_PROFILES:
            return
        profile = INTERCEPTOR_PROFILES[self.selected_interceptor.get()]
        self.interceptor_speed.set(profile.speed)
        self._set_interceptor_speed(str(profile.speed))

    def _set_interceptor_speed(self, value: str) -> None:
        speed = min(380.0, max(80.0, float(value)))
        self.world.interceptor_speed = speed
        self.interceptor_speed.set(speed)
        self._sync_speed_label()

    def _sync_speed_label(self) -> None:
        self.speed_text.set(f"{self.world.interceptor_speed:.0f}")

    def _on_key_press(self, event: tk.Event) -> None:
        self.keys_pressed.add(str(event.keysym).lower())
        self._update_player_control()

    def _on_key_release(self, event: tk.Event) -> None:
        self.keys_pressed.discard(str(event.keysym).lower())
        self._update_player_control()

    def _on_canvas_click(self, event: tk.Event) -> None:
        if self.world.game_mode == "nuclear_plant":
            self._set_status("Plant screen is controlled from the reactor panel buttons")
            return
        if self._handle_hud_button_click(event.x, event.y):
            return
        x = (event.x - CANVAS_SIZE / 2) / self._world_scale()
        y = (CANVAS_SIZE / 2 - event.y) / self._world_scale()
        if self.place_radar_mode.get():
            self.world.place_radar_site(self.selected_radar.get(), Vector2(x, y))
            self._show_latest_event()
            return
        if self.aim_radar_mode.get():
            self.world.aim_primary_radar_at(Vector2(x, y))
            self._show_latest_event()
            return
        self.world.set_manual_aim_point(Vector2(x, y))
        self._show_latest_event()

    def _canvas_event_to_world(self, event: tk.Event) -> Vector2:
        return Vector2(
            (event.x - CANVAS_SIZE / 2) / self._world_scale(),
            (CANVAS_SIZE / 2 - event.y) / self._world_scale(),
        )

    def _on_manual_fire_press(self, event: tk.Event) -> None:
        if self.world.game_mode == "nuclear_plant":
            return
        if not self.manual_fire_armed.get():
            self._set_status("Arm Right-Click Cannon before manual fire")
            return
        self.right_fire_active = True
        self._aim_and_maybe_fire(event, force=True)

    def _on_manual_fire_drag(self, event: tk.Event) -> None:
        if self.right_fire_active:
            self._aim_and_maybe_fire(event)

    def _on_manual_fire_release(self, _event: tk.Event) -> None:
        self.right_fire_active = False

    def _aim_and_maybe_fire(self, event: tk.Event, *, force: bool = False) -> None:
        aim = self._canvas_event_to_world(event)
        self.world.set_manual_aim_point(aim)
        if force or self.world.time >= self.next_manual_fire_at:
            self.next_manual_fire_at = self.world.time + 0.18
            self.world.manual_cannon_fire(self.selected_interceptor.get(), aim)
        self._show_latest_event()

    def _handle_hud_button_click(self, x: float, y: float) -> bool:
        for action, (x1, y1, x2, y2) in self.hud_buttons:
            if not (x1 <= x <= x2 and y1 <= y <= y2):
                continue
            if action == "launch":
                self._spawn_projectile()
            elif action == "intercept":
                self._deploy_best()
            elif action == "gun":
                self._manual_cannon_fire()
            elif action == "sonic":
                self._sonic_pulse()
            elif action == "ew":
                self._use_ew()
            elif action == "hq":
                self._answer_hq()
            return True
        return False

    def _update_player_control(self) -> None:
        x = 0.0
        y = 0.0
        if "left" in self.keys_pressed or "a" in self.keys_pressed:
            x -= 1.0
        if "right" in self.keys_pressed or "d" in self.keys_pressed:
            x += 1.0
        if "up" in self.keys_pressed or "w" in self.keys_pressed:
            y += 1.0
        if "down" in self.keys_pressed or "s" in self.keys_pressed:
            y -= 1.0
        self.world.set_player_control(Vector2(x, y))

    def _tick(self) -> None:
        if self.running:
            self.world.step(TICK_SECONDS)
            events = self.world.consume_events()
            if events:
                self._set_status(events[-1])
            if self.world.base_health <= 0:
                self.running = False
                if self.world.game_mode == "nuclear_plant":
                    self._set_status(f"Plant failed. Final score {self.world.score}")
                else:
                    self._set_status(f"Base destroyed. Final score {self.world.score}")
            if self.world.radar_destroyable and not self.world.radar_alive:
                self._set_status("Radar destroyed: tracking offline until you install another radar")
            if self.world.radar_repair_needed:
                self._set_status(self.world.repair_summary())
            self._draw()
        self.after(int(TICK_SECONDS * 1000), self._tick)

    def _set_status(self, text: str) -> None:
        self.status.set(text)
        self._play_sound_for(text)

    def _play_sound_for(self, text: str) -> None:
        if not self.sound_enabled.get():
            return
        for pattern, cue in SOUND_CUES:
            if pattern.lower() in text.lower():
                self._play_tone(*cue)
                return

    def _play_tone(self, frequency: int, duration: int) -> None:
        if winsound is not None:
            try:
                if "HQ phone" in self.status.get():
                    winsound.Beep(900, 120)
                    winsound.Beep(700, 120)
                else:
                    winsound.Beep(frequency, duration)
                return
            except RuntimeError:
                pass
        self.bell()

    def _speak_hq(self, text: str) -> None:
        if not self.voice_enabled.get():
            return
        spoken = text.replace("HQ:", "").strip()
        if win32com_client is not None:
            try:
                if self.voice is None:
                    self.voice = win32com_client.Dispatch("SAPI.SpVoice")
                    self.voice.Rate = -1
                self.voice.Speak(spoken, 1)
                return
            except Exception:
                self.voice = None
        for frequency in (620, 760, 540):
            self._play_tone(frequency, 65)

    def _world_scale(self) -> float:
        return (CANVAS_SIZE - PADDING * 2) / (WORLD_HALF_SIZE * 2)

    def _world_to_canvas(self, x: float, y: float) -> tuple[float, float]:
        scale = self._world_scale()
        return (
            CANVAS_SIZE / 2 + x * scale,
            CANVAS_SIZE / 2 - y * scale,
        )

    def _radar_scope_shape(self, radar) -> str:
        return self.world.radar_fov_shape(radar)

    def _draw_square_scope(self, center: float, radar_radius: float, color: str, *, dense: bool = False) -> None:
        self.canvas.create_rectangle(PADDING, PADDING, CANVAS_SIZE - PADDING, CANVAS_SIZE - PADDING, outline=color, width=2)
        lines = 10 if dense else 8
        for index in range(1, lines):
            x = PADDING + (CANVAS_SIZE - PADDING * 2) * index / lines
            y = PADDING + (CANVAS_SIZE - PADDING * 2) * index / lines
            self.canvas.create_line(x, PADDING, x, CANVAS_SIZE - PADDING, fill="#143d4a")
            self.canvas.create_line(PADDING, y, CANVAS_SIZE - PADDING, y, fill="#143d4a")
        for fraction in (0.25, 0.5, 0.75):
            radius = radar_radius * fraction
            self.canvas.create_rectangle(center - radius, center - radius, center + radius, center + radius, outline="#1a4a56")

    def _draw_sector_scope(self, center: float, radar_radius: float, color: str, start: float, extent: float, *, label: str) -> None:
        for fraction in (0.25, 0.5, 0.75, 1.0):
            radius = radar_radius * fraction
            self.canvas.create_arc(center - radius, center - radius, center + radius, center + radius, start=start, extent=extent, outline="#123b38", style="arc")
        self.canvas.create_arc(center - radar_radius, center - radar_radius, center + radar_radius, center + radar_radius, start=start, extent=extent, outline=color, width=3, style="arc")
        for angle in (start, start + extent, start + extent / 2):
            radians = angle * 3.141592653589793 / 180.0
            x = center + radar_radius * cos(radians)
            y = center - radar_radius * sin(radians)
            self.canvas.create_line(center, center, x, y, fill="#123b38" if angle != start + extent / 2 else color, dash=(5, 8))
        self.canvas.create_text(center, center + 28, text=label, fill=color, justify="center", font=("Segoe UI", 9, "bold"))

    def _draw_fov_bearing_line(self, center: float, radar_radius: float, bearing: float, color: str, *, label: str = "") -> None:
        radians = bearing * 3.141592653589793 / 180.0
        x = center + radar_radius * cos(radians)
        y = center - radar_radius * sin(radians)
        self.canvas.create_line(center, center, x, y, fill=color, width=2, dash=(8, 6))
        self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, outline=color, width=2)
        if label:
            self.canvas.create_text(x, y - 12, text=label, fill=color, font=("Segoe UI", 8, "bold"))

    def _draw_fixed_lobe_scope(self, center: float, radar_radius: float, color: str) -> None:
        left = center - radar_radius * 0.82
        right = center + radar_radius * 0.82
        top = center - radar_radius * 0.76
        bottom = center + radar_radius * 0.68
        self.canvas.create_rectangle(left, top, right, bottom, outline=color, width=2)
        for index in range(1, 6):
            x = left + (right - left) * index / 6
            self.canvas.create_line(x, top, x, bottom, fill="#3a3a25", dash=(4, 10))
        for index in range(1, 5):
            y = top + (bottom - top) * index / 5
            self.canvas.create_line(left, y, right, y, fill="#3a3a25", dash=(4, 10))
        self.canvas.create_arc(left, top - 70, right, bottom + 30, start=0, extent=180, outline=color, width=2, style="arc")
        self.canvas.create_line(left, center, right, center, fill=color, dash=(10, 8))
        self.canvas.create_text(center, top + 18, text="FIXED LOBE\nHEIGHT BY TRACE", fill=color, justify="center", font=("Segoe UI", 9, "bold"))

    def _draw_passive_scope(self, center: float, radar_radius: float, color: str) -> None:
        self.canvas.create_rectangle(PADDING, PADDING, CANVAS_SIZE - PADDING, CANVAS_SIZE - PADDING, outline=color, width=2, dash=(8, 6))
        baselines = ((-0.68, 0.48), (0.62, 0.42), (-0.12, -0.62))
        points: list[tuple[float, float]] = []
        for x_mult, y_mult in baselines:
            x = center + radar_radius * x_mult
            y = center + radar_radius * y_mult
            points.append((x, y))
            self.canvas.create_polygon(x, y - 11, x + 10, y + 8, x - 10, y + 8, outline=color, fill="")
        for index, (x1, y1) in enumerate(points):
            x2, y2 = points[(index + 1) % len(points)]
            self.canvas.create_line(x1, y1, x2, y2, fill="#123b38", dash=(5, 9))
        for fraction in (0.32, 0.58, 0.84):
            radius = radar_radius * fraction
            self.canvas.create_oval(center - radius, center - radius, center + radius, center + radius, outline="#123b38", dash=(2, 8))
        self.canvas.create_text(center, center, text="PASSIVE\nESM FIX", fill=color, justify="center", font=("Segoe UI", 9, "bold"))

    def _draw_radar_fov_icon(self, radar, x: float, y: float, radius: float, bearing: float) -> None:
        shape = self._radar_scope_shape(radar)
        color = radar.color
        if shape == "square":
            self.canvas.create_rectangle(x - radius, y - radius, x + radius, y + radius, outline=color, dash=(3, 7))
        elif shape in {"sector", "narrow_sector"}:
            extent = self.world.radar_fov_degrees(radar)
            start = bearing - extent / 2
            self.canvas.create_arc(x - radius, y - radius, x + radius, y + radius, start=start, extent=extent, outline=color, dash=(3, 7), style="arc")
            radians = bearing * 3.141592653589793 / 180.0
            self.canvas.create_line(x, y, x + radius * cos(radians), y - radius * sin(radians), fill=color, dash=(3, 7))
        elif shape == "counter_battery":
            extent = self.world.radar_fov_degrees(radar)
            start = bearing - extent / 2
            self.canvas.create_arc(x - radius, y - radius, x + radius, y + radius, start=start, extent=extent, outline=color, dash=(3, 7), style="arc")
            for angle in (start, start + extent):
                radians = angle * 3.141592653589793 / 180.0
                self.canvas.create_line(x, y, x + radius * cos(radians), y - radius * sin(radians), fill=color, dash=(3, 7))
        elif shape == "passive":
            self.canvas.create_rectangle(x - radius, y - radius, x + radius, y + radius, outline=color, dash=(2, 6))
        elif shape == "fixed_lobe":
            self.canvas.create_rectangle(x - radius * 0.8, y - radius * 0.55, x + radius * 0.8, y + radius * 0.55, outline=color, dash=(4, 8))
        else:
            self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline=color, dash=(3, 9))

    def _draw(self) -> None:
        if self.world.game_mode == "nuclear_plant":
            self.canvas.configure(bg="#071014")
            self.canvas.delete("all")
            self._draw_plant_screen()
            self._update_readout()
            return
        self.canvas.configure(bg=self.world.current_map.color)
        self.canvas.delete("all")
        self._draw_grid()
        self._draw_terrain()
        self._draw_radar_sites()
        self._draw_field_effects()
        self._draw_tracks()
        self._draw_enemies()
        self._draw_projectiles()
        self._draw_interceptors()
        self._draw_manual_aim()
        self._draw_base()
        self._draw_hud_softkeys()
        self._update_readout()

    def _draw_plant_screen(self) -> None:
        self.canvas.create_text(34, 28, text="NUCLEAR PLANT CONTROL ROOM", fill="#d8f3dc", anchor="w", font=("Segoe UI", 16, "bold"))
        self.canvas.create_text(34, 54, text=self.world.plant_message, fill="#fefae0" if not self.world.plant_alarm else "#ff6b6b", anchor="w", font=("Segoe UI", 10, "bold"))

        vessel_x = 260
        vessel_y = 140
        vessel_w = 190
        vessel_h = 360
        core_heat = min(1.0, self.world.reactor_temperature / 760.0)
        heat_color = "#70e000" if core_heat < 0.55 else "#ffd166" if core_heat < 0.82 else "#ff6b6b"
        self.canvas.create_oval(vessel_x, vessel_y, vessel_x + vessel_w, vessel_y + 70, outline="#8ecae6", width=3)
        self.canvas.create_rectangle(vessel_x, vessel_y + 35, vessel_x + vessel_w, vessel_y + vessel_h, outline="#8ecae6", width=3)
        self.canvas.create_oval(vessel_x, vessel_y + vessel_h - 35, vessel_x + vessel_w, vessel_y + vessel_h + 35, outline="#8ecae6", width=3)
        self.canvas.create_text(vessel_x + vessel_w / 2, vessel_y + 18, text="REACTOR VESSEL", fill="#d8f3dc", font=("Segoe UI", 9, "bold"))

        coolant_fill = vessel_h * min(1.0, self.world.coolant_level / 100.0)
        self.canvas.create_rectangle(vessel_x + 18, vessel_y + vessel_h - coolant_fill, vessel_x + vessel_w - 18, vessel_y + vessel_h, fill="#0a9396", outline="")
        self.canvas.create_rectangle(vessel_x + 58, vessel_y + 185, vessel_x + vessel_w - 58, vessel_y + 300, fill=heat_color, outline="#fefae0", width=2)
        self.canvas.create_text(vessel_x + vessel_w / 2, vessel_y + 242, text=f"{self.world.reactor_power:.0f}%\nCORE", fill="#071014", justify="center", font=("Segoe UI", 13, "bold"))

        rod_drop = (self.world.control_rod_position / 100.0) * 190
        for offset in (55, 78, 101, 124, 147):
            self.canvas.create_line(vessel_x + offset, vessel_y + 65, vessel_x + offset, vessel_y + 65 + rod_drop, fill="#212529", width=7)
            self.canvas.create_line(vessel_x + offset, vessel_y + 65, vessel_x + offset, vessel_y + 65 + rod_drop, fill="#adb5bd", width=3)
        self.canvas.create_text(vessel_x + vessel_w + 20, vessel_y + 118, text=f"Rods {self.world.control_rod_position:.0f}%", fill="#d8f3dc", anchor="w", font=("Segoe UI", 10, "bold"))

        self._draw_plant_loop(86, 210, "PUMP A", self.world.pump_a_online)
        self._draw_plant_loop(86, 370, "PUMP B", self.world.pump_b_online)
        self.canvas.create_line(168, 230, vessel_x, 230, fill="#48cae4", width=6)
        self.canvas.create_line(168, 390, vessel_x, 390, fill="#48cae4", width=6)
        self.canvas.create_line(vessel_x + vessel_w, 250, 560, 250, fill="#fefae0", width=5)
        self.canvas.create_line(560, 250, 620, 355, fill="#fefae0", width=5)
        self.canvas.create_line(620, 390, vessel_x + vessel_w, 410, fill="#48cae4", width=6)

        turbine_color = "#70e000" if self.world.turbine_vibration < 28 else "#ffd166" if self.world.turbine_vibration < 40 else "#ff6b6b"
        self.canvas.create_oval(540, 320, 680, 460, outline=turbine_color, width=4)
        self.canvas.create_text(610, 368, text="TURBINE", fill="#d8f3dc", font=("Segoe UI", 12, "bold"))
        self.canvas.create_text(610, 395, text=f"Load {self.world.turbine_load:.0f}%\nVib {self.world.turbine_vibration:.0f}%", fill="#d8f3dc", justify="center", font=("Segoe UI", 9))
        self.canvas.create_rectangle(555, 485, 665, 540, outline="#ffd166", width=3)
        self.canvas.create_text(610, 512, text=f"GEN\n{self.world.generator_output:.0f}%", fill="#ffd166", justify="center", font=("Segoe UI", 12, "bold"))

        self._draw_plant_bar(36, 610, "Coolant", self.world.coolant_level, "#48cae4")
        self._draw_plant_bar(206, 610, "Temp", min(100.0, self.world.reactor_temperature / 8.0), heat_color, suffix=f"{self.world.reactor_temperature:.0f}")
        self._draw_plant_bar(376, 610, "Steam", self.world.steam_pressure, "#fefae0")
        self._draw_plant_bar(546, 610, "Grid", self.world.grid_demand, "#ffd166")

        integrity_color = "#70e000" if self.world.containment_integrity > 70 else "#ffd166" if self.world.containment_integrity > 38 else "#ff6b6b"
        self.canvas.create_rectangle(34, 86, 686, 104, outline="#495057")
        self.canvas.create_rectangle(34, 86, 34 + 652 * self.world.containment_integrity / 100.0, 104, fill=integrity_color, outline="")
        self.canvas.create_text(360, 95, text=f"Containment Integrity {self.world.containment_integrity:.0f}%", fill="#071014", font=("Segoe UI", 9, "bold"))
        if self.world.plant_alarm:
            self.canvas.create_rectangle(470, 28, 686, 70, outline="#ff6b6b", width=3)
            self.canvas.create_text(578, 49, text="ALARM", fill="#ff6b6b", font=("Segoe UI", 16, "bold"))

    def _draw_plant_loop(self, x: float, y: float, label: str, online: bool) -> None:
        color = "#70e000" if online else "#6c757d"
        self.canvas.create_oval(x, y, x + 82, y + 82, outline=color, width=4)
        self.canvas.create_arc(x + 18, y + 18, x + 64, y + 64, start=(self.world.time * 120) % 360, extent=250 if online else 70, outline=color, width=4)
        self.canvas.create_text(x + 41, y + 100, text=f"{label}\n{'ONLINE' if online else 'OFFLINE'}", fill=color, justify="center", font=("Segoe UI", 9, "bold"))

    def _draw_plant_bar(self, x: float, y: float, label: str, value: float, color: str, *, suffix: str | None = None) -> None:
        bounded = min(100.0, max(0.0, value))
        self.canvas.create_text(x, y - 18, text=label, fill="#d8f3dc", anchor="w", font=("Segoe UI", 9, "bold"))
        self.canvas.create_rectangle(x, y, x + 128, y + 26, outline="#495057")
        self.canvas.create_rectangle(x, y, x + 128 * bounded / 100.0, y + 26, fill=color, outline="")
        text = suffix if suffix is not None else f"{value:.0f}%"
        self.canvas.create_text(x + 64, y + 13, text=text, fill="#071014", font=("Segoe UI", 9, "bold"))

    def _draw_grid(self) -> None:
        center = CANVAS_SIZE / 2
        radar_radius = max(0, min(CANVAS_SIZE / 2 - PADDING, self.world.radar_radius * self._world_scale()))
        radar = self.world.current_radar
        display = self.selected_display.get()
        shape = self._radar_scope_shape(radar)
        bearing = self.world.radar_bearing_degrees
        fov = self.world.radar_fov_degrees(radar)
        sector_start = bearing - fov / 2.0
        if shape == "fixed_lobe":
            self._draw_fixed_lobe_scope(center, radar_radius, radar.color)
            self._draw_fov_bearing_line(center, radar_radius, bearing, radar.color, label=f"{fov:.0f} deg")
            self._draw_hud_labels(center, radar_radius)
            return
        if shape == "passive":
            self._draw_passive_scope(center, radar_radius, radar.color)
            self._draw_hud_labels(center, radar_radius)
            return
        if shape == "counter_battery":
            self._draw_sector_scope(center, radar_radius, radar.color, sector_start, fov, label="COUNTER-BATTERY\nFAN")
            self._draw_sweep(center, radar_radius, sector=True, start=sector_start, extent=fov)
            self._draw_hud_labels(center, radar_radius)
            return
        if shape == "narrow_sector":
            self._draw_sector_scope(center, radar_radius, radar.color, sector_start, fov, label="FIRE-CONTROL\nNARROW BEAM")
            self._draw_sweep(center, radar_radius, sector=True, start=sector_start, extent=fov)
            self._draw_hud_labels(center, radar_radius)
            return
        if shape == "naval":
            self._draw_square_scope(center, radar_radius, radar.color, dense=True)
            self.canvas.create_oval(center - radar_radius, center - radar_radius, center + radar_radius, center + radar_radius, outline=radar.color, width=2)
            if fov < 359.0:
                self._draw_sector_scope(center, radar_radius, radar.color, sector_start, fov, label="NAVAL\nSECTOR")
                self._draw_sweep(center, radar_radius, sector=True, start=sector_start, extent=fov)
            else:
                self._draw_sweep(center, radar_radius)
            self._draw_hud_labels(center, radar_radius)
            return
        if radar.scan_pattern == "aesa_multi_beam":
            self._draw_square_scope(center, radar_radius, radar.color, dense=True)
            self.canvas.create_oval(center - radar_radius, center - radar_radius, center + radar_radius, center + radar_radius, outline="#1a4a56", width=1)
            self._draw_fov_bearing_line(center, radar_radius, bearing, radar.color, label=f"{fov:.0f} deg")
            self._draw_aesa_beams(center, radar_radius)
            self._draw_hud_labels(center, radar_radius)
            return
        if radar.scan_pattern == "pesa_sector":
            self._draw_sector_scope(center, radar_radius, radar.color, sector_start, fov, label="PESA\nSECTOR")
            self._draw_pesa_lobes(center, radar_radius)
            self._draw_hud_labels(center, radar_radius)
            return
        if radar.scan_pattern == "pulse_doppler":
            self.canvas.create_oval(center - radar_radius, center - radar_radius, center + radar_radius, center + radar_radius, outline=radar.color, width=2)
            mid_y = CANVAS_SIZE / 2
            self.canvas.create_line(PADDING, mid_y, CANVAS_SIZE - PADDING, mid_y, fill="#3a5a40", dash=(6, 8))
            for fraction in (0.25, 0.5, 0.75):
                radius = radar_radius * fraction
                self.canvas.create_oval(center - radius, center - radius, center + radius, center + radius, outline="#123b38")
            for angle in range(0, 360, 45):
                radians = angle * 3.141592653589793 / 180.0
                x = center + radar_radius * cos(radians)
                y = center - radar_radius * sin(radians)
                self.canvas.create_line(center, center, x, y, fill="#123b38", dash=(2, 10))
            self._draw_sweep(center, radar_radius)
            self._draw_hud_labels(center, radar_radius)
            return
        if radar.scan_pattern == "height_finder":
            self.canvas.create_rectangle(PADDING, PADDING, CANVAS_SIZE - PADDING, CANVAS_SIZE - PADDING, outline=radar.color, width=2)
            for index in range(1, 6):
                x = PADDING + (CANVAS_SIZE - PADDING * 2) * index / 6
                self.canvas.create_line(x, PADDING, x, CANVAS_SIZE - PADDING, fill="#123b38")
            for index in range(1, 7):
                y = PADDING + (CANVAS_SIZE - PADDING * 2) * index / 7
                self.canvas.create_line(PADDING, y, CANVAS_SIZE - PADDING, y, fill="#123b38")
            self.canvas.create_text(PADDING + 8, PADDING + 8, text="HEIGHT FINDER", fill=radar.color, anchor="nw", font=("Segoe UI", 9, "bold"))
            self._draw_hud_labels(center, radar_radius)
            return
        if radar.hud_style == "early_analog":
            self.canvas.create_oval(center - radar_radius, center - radar_radius, center + radar_radius, center + radar_radius, outline=radar.color, width=2)
            for fraction in (0.33, 0.66):
                radius = radar_radius * fraction
                self.canvas.create_oval(center - radius, center - radius, center + radius, center + radius, outline="#3a3a25", dash=(4, 10))
            self.canvas.create_line(PADDING, center, CANVAS_SIZE - PADDING, center, fill="#3a3a25")
            self.canvas.create_line(center, PADDING, center, CANVAS_SIZE - PADDING, fill="#3a3a25")
            self._draw_sweep(center, radar_radius)
            self._draw_hud_labels(center, radar_radius)
            return
        if display == "B-Scope":
            self.canvas.create_rectangle(PADDING, PADDING, CANVAS_SIZE - PADDING, CANVAS_SIZE - PADDING, outline=radar.color, width=2)
            for index in range(1, 6):
                x = PADDING + (CANVAS_SIZE - PADDING * 2) * index / 6
                y = PADDING + (CANVAS_SIZE - PADDING * 2) * index / 6
                self.canvas.create_line(x, PADDING, x, CANVAS_SIZE - PADDING, fill="#123b38")
                self.canvas.create_line(PADDING, y, CANVAS_SIZE - PADDING, y, fill="#123b38")
            self._draw_hud_labels(center, radar_radius)
            return
        if display == "Sector Scan":
            self.canvas.create_arc(center - radar_radius, center - radar_radius, center + radar_radius, center + radar_radius, start=25, extent=130, outline=radar.color, width=3, style="arc")
            for fraction in (0.25, 0.5, 0.75, 1.0):
                radius = radar_radius * fraction
                self.canvas.create_arc(center - radius, center - radius, center + radius, center + radius, start=25, extent=130, outline="#123b38", style="arc")
            self.canvas.create_line(center, center, center + radar_radius * 0.91, center - radar_radius * 0.42, fill="#123b38")
            self.canvas.create_line(center, center, center - radar_radius * 0.42, center - radar_radius * 0.91, fill="#123b38")
            self._draw_sweep(center, radar_radius, sector=True, start=25, extent=130)
            self._draw_hud_labels(center, radar_radius)
            return
        self.canvas.create_oval(center - radar_radius, center - radar_radius, center + radar_radius, center + radar_radius, outline=radar.color, width=2)
        for fraction in (0.25, 0.5, 0.75):
            radius = radar_radius * fraction
            self.canvas.create_oval(center - radius, center - radius, center + radius, center + radius, outline="#123b38")
        self.canvas.create_line(PADDING, center, CANVAS_SIZE - PADDING, center, fill="#123b38")
        self.canvas.create_line(center, PADDING, center, CANVAS_SIZE - PADDING, fill="#123b38")
        if display == "PPI Sweep":
            self._draw_sweep(center, radar_radius)
        self._draw_hud_labels(center, radar_radius)

    def _draw_aesa_beams(self, center: float, radar_radius: float) -> None:
        radar = self.world.current_radar
        for index, region_bearing in enumerate(self.world.radar_region_bearings(radar, self.world.radar_bearing_degrees)):
            sweep = ((self.world.time * 80 + index * 31) % 12) - 6
            radians = (region_bearing + sweep) * 3.141592653589793 / 180.0
            inner = radar_radius * 0.18
            outer = radar_radius * (0.72 + (index % 3) * 0.08)
            x1 = center + inner * cos(radians)
            y1 = center - inner * sin(radians)
            x2 = center + outer * cos(radians)
            y2 = center - outer * sin(radians)
            self.canvas.create_line(x1, y1, x2, y2, fill=radar.color, width=2, dash=(8, 6))
            self.canvas.create_oval(x2 - 4, y2 - 4, x2 + 4, y2 + 4, outline=radar.color)
        self.canvas.create_text(center, center, text="AESA\nMULTI-BEAM", fill=radar.color, justify="center", font=("Segoe UI", 9, "bold"))

    def _draw_pesa_lobes(self, center: float, radar_radius: float) -> None:
        radar = self.world.current_radar
        width = self.world.radar_region_width_degrees(radar)
        for index, region_bearing in enumerate(self.world.radar_region_bearings(radar, self.world.radar_bearing_degrees)):
            angle = region_bearing - width / 2.0 + ((self.world.time * 40 + index * 13) % max(8.0, width * 0.25))
            self.canvas.create_arc(
                center - radar_radius,
                center - radar_radius,
                center + radar_radius,
                center + radar_radius,
                start=angle,
                extent=min(width, 18 + index * 4),
                outline=radar.color,
                width=2,
                style="arc",
            )
        self.canvas.create_text(center, center, text="PESA\nTWS", fill=radar.color, justify="center", font=("Segoe UI", 9, "bold"))

    def _hud_terms(self) -> tuple[str, str, str, str]:
        style = self.world.current_radar.hud_style
        if style == "soviet_green":
            return ("ДАЛЬН", "АЗИМ", "ВЫС", "ЦЕЛЬ")
        if style == "eastern_amber":
            return ("RNG", "BRG", "ALT", "TRK")
        if style == "early_analog":
            return ("RANGE", "BEARING", "HEIGHT", "ECHO")
        return ("RNG", "BRG", "ALT", "TRACK")

    def _draw_hud_labels(self, center: float, radar_radius: float) -> None:
        radar = self.world.current_radar
        rng, brg, alt, track = self._hud_terms()
        color = radar.color
        self.canvas.create_text(PADDING + 8, CANVAS_SIZE - PADDING - 8, text=f"{radar.year}  {radar.scan_pattern}  {self.world.radar_bearing_degrees:03.0f} deg", fill=color, anchor="sw", font=("Segoe UI", 8, "bold"))
        self.canvas.create_text(CANVAS_SIZE - PADDING - 8, PADDING + 8, text=f"{rng}/{brg}/{alt}", fill=color, anchor="ne", font=("Segoe UI", 8, "bold"))
        self.canvas.create_text(CANVAS_SIZE - PADDING - 8, CANVAS_SIZE - PADDING - 8, text=f"{track} {len(self.world.tracker.tracks):02d}", fill=color, anchor="se", font=("Segoe UI", 8, "bold"))
        if radar.hud_style == "soviet_green":
            self.canvas.create_text(center, PADDING + 18, text="РЛС БОЕВОЙ ПОСТ", fill=color, font=("Segoe UI", 9, "bold"))
        elif radar.hud_style == "early_analog":
            self.canvas.create_text(center, PADDING + 18, text="ANALOG A-SCOPE / PPI", fill=color, font=("Segoe UI", 9, "bold"))

    def _draw_sweep(self, center: float, radar_radius: float, *, sector: bool = False, start: float = 25.0, extent: float = 130.0) -> None:
        if not self.world.radar_alive:
            return
        if sector:
            live_offset = (self.world.radar_bearing_degrees - start) % 360.0
            angle = self.world.radar_bearing_degrees if live_offset <= extent else start + (self.world.time * 38) % extent
        else:
            angle = self.world.radar_bearing_degrees
        radians = angle * 3.141592653589793 / 180.0
        x = center + radar_radius * cos(radians)
        y = center - radar_radius * sin(radians)
        self.canvas.create_line(center, center, x, y, fill="#d8f3dc", width=2)
        for lag in (12, 24):
            lag_angle = (angle - lag) * 3.141592653589793 / 180.0
            lx = center + radar_radius * cos(lag_angle)
            ly = center - radar_radius * sin(lag_angle)
            self.canvas.create_line(center, center, lx, ly, fill="#1d6f64")

    def _draw_terrain(self) -> None:
        map_name = self.world.current_map.name
        if map_name == "Mountain Valley":
            for offset in (-210, 180):
                x, y = self._world_to_canvas(offset, 0)
                self.canvas.create_polygon(x - 70, 32, x + 40, 32, x + 95, CANVAS_SIZE - 32, x - 85, CANVAS_SIZE - 32, fill="#1f4d2b", outline="")
        elif map_name == "Urban Basin":
            for index in range(7):
                x = 80 + index * 85
                self.canvas.create_rectangle(x, 110, x + 34, 580, outline="#33415c", dash=(5, 9))
        elif map_name == "Desert Flats":
            self.canvas.create_arc(120, 120, 610, 650, start=10, extent=160, outline="#8d6b35", style="arc")
        elif map_name == "Snow Plateau":
            self.canvas.create_line(70, 240, 660, 460, fill="#88a0aa", dash=(8, 10))

    def _draw_base(self) -> None:
        x, y = self._world_to_canvas(self.world.base_position.x, self.world.base_position.y)
        color = "#e9ff70" if self.world.radar_alive else "#6c757d"
        self.canvas.create_oval(x - 10, y - 10, x + 10, y + 10, fill=color, outline="")
        self.canvas.create_text(x, y + 25, text="RADAR SITE", fill="#d8f3dc", font=("Segoe UI", 9, "bold"))
        if self.world.radar_repair_needed:
            self.canvas.create_rectangle(x - 64, y + 38, x + 64, y + 72, outline="#ff6b6b", width=2)
            self.canvas.create_text(x, y + 55, text="WIRE REPAIR", fill="#ff6b6b", font=("Segoe UI", 9, "bold"))

    def _draw_radar_sites(self) -> None:
        scale = self._world_scale()
        for site in self.world.radar_sites.values():
            x, y = self._world_to_canvas(site.position.x, site.position.y)
            radius = max(10.0, min(70.0, site.profile.range * scale * 0.16))
            self._draw_radar_fov_icon(site.profile, x, y, radius, site.bearing_degrees)
            self.canvas.create_polygon(x, y - 11, x + 11, y, x, y + 11, x - 11, y, fill=site.profile.color, outline="#071014")
            self.canvas.create_text(x + 16, y + 14, text=f"RDR {site.site_id}", fill=site.profile.color, anchor="w", font=("Segoe UI", 8, "bold"))
        for site in self.world.hostile_radar_sites.values():
            x, y = self._world_to_canvas(site.position.x, site.position.y)
            radius = max(10.0, min(70.0, site.profile.range * scale * 0.16))
            self._draw_radar_fov_icon(site.profile, x, y, radius, site.bearing_degrees)
            color = "#ff6b6b" if self.world.time >= site.jammed_until else "#ff70a6"
            self.canvas.create_polygon(x, y - 13, x + 13, y + 10, x - 13, y + 10, fill="", outline=color, width=2)
            self.canvas.create_text(x + 16, y + 14, text=f"HOST RDR {site.site_id}", fill=color, anchor="w", font=("Segoe UI", 8, "bold"))
            if self.world.time < site.jammed_until:
                self.canvas.create_text(x, y - 24, text="JAM", fill="#ff70a6", font=("Segoe UI", 8, "bold"))

    def _draw_field_effects(self) -> None:
        scale = self._world_scale()
        for effect in self.world.active_field_effects():
            x, y = self._world_to_canvas(effect.origin.x, effect.origin.y)
            radius = effect.range * scale
            start = effect.bearing_degrees - effect.width_degrees / 2.0
            color = effect.color
            self.canvas.create_arc(x - radius, y - radius, x + radius, y + radius, start=start, extent=effect.width_degrees, outline=color, width=3, style="arc")
            for angle in (start, start + effect.width_degrees, effect.bearing_degrees):
                radians = angle * 3.141592653589793 / 180.0
                ex = x + radius * cos(radians)
                ey = y - radius * sin(radians)
                self.canvas.create_line(x, y, ex, ey, fill=color, dash=(4, 8))
            label_x = x + radius * 0.42 * cos(effect.bearing_degrees * 3.141592653589793 / 180.0)
            label_y = y - radius * 0.42 * sin(effect.bearing_degrees * 3.141592653589793 / 180.0)
            self.canvas.create_text(label_x, label_y, text=effect.label, fill=color, font=("Segoe UI", 8, "bold"))

    def _draw_hud_softkeys(self) -> None:
        self.hud_buttons.clear()
        actions = (
            ("launch", "LCH", "#ffd166"),
            ("intercept", "INT", "#fefae0"),
            ("gun", "GUN", "#f8f9fa"),
            ("sonic", "SON", "#8ecae6"),
            ("ew", "EW", "#ff70a6"),
            ("hq", "HQ", "#9bf6ff"),
        )
        x = CANVAS_SIZE - 48
        y = 144
        for index, (action, label, color) in enumerate(actions):
            cy = y + index * 58
            active = action != "hq" or self.world.pending_hq_call is not None
            outline = color if active else "#495057"
            fill = "#11251f" if active else "#101820"
            self.canvas.create_oval(x - 22, cy - 22, x + 22, cy + 22, fill=fill, outline=outline, width=2)
            self.canvas.create_oval(x - 15, cy - 15, x + 15, cy + 15, outline="#234", width=1)
            self.canvas.create_text(x, cy, text=label, fill=outline, font=("Segoe UI", 8, "bold"))
            self.hud_buttons.append((action, (x - 24, cy - 24, x + 24, cy + 24)))

    def _draw_projectiles(self) -> None:
        for projectile in self.world.projectiles.values():
            x, y = self._world_to_canvas(projectile.position.x, projectile.position.y)
            if projectile.player_controlled:
                direction = projectile.velocity.normalized()
                dx, dy = direction.x, -direction.y
                self.canvas.create_polygon(x + dx * 12, y + dy * 12, x - dy * 7 - dx * 7, y + dx * 7 - dy * 7, x + dy * 7 - dx * 7, y - dx * 7 - dy * 7, fill="#fefae0", outline=projectile.profile.color, width=2)
            else:
                size = 6 if projectile.profile.radar_seeking else 5
                self.canvas.create_oval(x - size, y - size, x + size, y + size, fill=projectile.profile.color, outline="")
                if projectile.profile.radar_seeking:
                    self.canvas.create_line(x - 8, y, x + 8, y, fill="#fefae0")
                if self.world.current_radar.scan_pattern in {"height_finder", "aesa_multi_beam", "pesa_sector"}:
                    height_bar = min(28.0, projectile.altitude / 140.0)
                    self.canvas.create_line(x + 8, y + 8, x + 8, y + 8 - height_bar, fill=projectile.profile.color)

    def _draw_enemies(self) -> None:
        scale = self._world_scale()
        for enemy in self.world.tracked_enemies():
            track = self.world.enemy_track_for(enemy.enemy_id)
            if track is None:
                continue
            predicted = track.predict(self.world.time + 1.5)
            x, y = self._world_to_canvas(track.position.x, track.position.y)
            px, py = self._world_to_canvas(predicted.x, predicted.y)
            track_color = "#9bf6ff" if track.engageable else "#ffd166"
            if enemy.profile.jammer_strength > 0:
                radius = enemy.profile.jammer_radius * scale
                self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline="#ff70a6", dash=(6, 6))
            size = 10 + enemy.profile.health * 2
            fill = enemy.profile.color if track.confidence >= 0.45 else ""
            outline = "#f8f9fa" if track.engageable else track_color
            dash = None if track.engageable else (3, 7)
            self.canvas.create_line(x, y, px, py, fill=track_color, dash=(2, 7), width=2)
            if enemy.profile.platform == "ground":
                self.canvas.create_rectangle(x - size, y - size * 0.65, x + size, y + size * 0.65, fill=fill, outline=outline, dash=dash)
            else:
                self.canvas.create_polygon(x, y - size, x + size, y + size * 0.5, x, y + size * 0.2, x - size, y + size * 0.5, fill=fill, outline=outline)
                if not track.engageable:
                    self.canvas.create_oval(x - size - 3, y - size - 3, x + size + 3, y + size + 3, outline="#6c757d", dash=(3, 7))
            label = f"{enemy.profile.name} {enemy.health} {'WEAP' if track.engageable else 'CUE'} ALT {track.altitude:.0f} C{track.confidence:.2f}"
            if enemy.profile.jammer_strength > 0:
                label += " EW"
            self.canvas.create_text(x + size + 5, y - size, text=label, fill="#d8f3dc", anchor="w", font=("Segoe UI", 8))

    def _draw_tracks(self) -> None:
        for track in self.world.tracker.tracks:
            is_ghost = self.world.is_ghost_track(track.projectile_id)
            x, y = self._world_to_canvas(track.position.x, track.position.y)
            predicted = track.predict(self.world.time + 2.5)
            px, py = self._world_to_canvas(predicted.x, predicted.y)
            color = "#ff70a6" if is_ghost else "#9bf6ff" if track.engageable else "#ffd166"
            label = "GHOST" if is_ghost else f"#{track.projectile_id} {'WEAP' if track.engageable else 'CUE'} ALT {track.altitude:.0f}"
            dash = (2, 7) if is_ghost else (2, 8) if not track.engageable else (4, 4)
            self.canvas.create_line(x, y, px, py, fill=color, dash=dash, width=2)
            self.canvas.create_oval(x - 9, y - 9, x + 9, y + 9, outline=color, width=2 if track.engageable else 1)
            self.canvas.create_text(x + 16, y - 12, text=label, fill="#d8f3dc", anchor="w")
            if self.world.current_radar.scan_pattern in {"height_finder", "aesa_multi_beam", "pesa_sector"}:
                height_bar = min(42.0, track.altitude / 90.0)
                self.canvas.create_line(x - 13, y + 13, x - 13, y + 13 - height_bar, fill=color, width=2)
            if is_ghost:
                continue
            solution = self.world.best_intercept_for(track.projectile_id, self.selected_interceptor.get(), speed_override=self.world.interceptor_speed)
            if solution is not None:
                ix, iy = self._world_to_canvas(solution.point.x, solution.point.y)
                self.canvas.create_oval(ix - 6, iy - 6, ix + 6, iy + 6, outline="#fefae0", width=2)
                bx, by = self._world_to_canvas(self.world.base_position.x, self.world.base_position.y)
                self.canvas.create_line(bx, by, ix, iy, fill="#fefae0", dash=(2, 6))

    def _draw_interceptors(self) -> None:
        scale = self._world_scale()
        for interceptor in self.world.interceptors.values():
            x, y = self._world_to_canvas(interceptor.position.x, interceptor.position.y)
            ix, iy = self._world_to_canvas(interceptor.intercept_point.x, interceptor.intercept_point.y)
            radius = max(4, interceptor.profile.blast_radius * scale)
            self.canvas.create_line(x, y, ix, iy, fill=interceptor.profile.color)
            self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline=interceptor.profile.color)
            if interceptor.profile.category == "gun":
                self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=interceptor.profile.color, outline="")
            else:
                self.canvas.create_rectangle(x - 4, y - 4, x + 4, y + 4, fill=interceptor.profile.color, outline="")

    def _draw_manual_aim(self) -> None:
        if self.world.manual_aim_point is None:
            return
        x, y = self._world_to_canvas(self.world.manual_aim_point.x, self.world.manual_aim_point.y)
        self.canvas.create_line(x - 14, y, x + 14, y, fill="#fefae0", dash=(2, 4))
        self.canvas.create_line(x, y - 14, x, y + 14, fill="#fefae0", dash=(2, 4))
        self.canvas.create_text(x + 16, y + 12, text="MAN", fill="#fefae0", anchor="w", font=("Segoe UI", 8))

    def _update_readout(self) -> None:
        if self.world.game_mode == "nuclear_plant":
            self.score_text.set(f"Plant Score {self.world.score} | Integrity {self.world.containment_integrity:.0f}%")
            lines = [
                "Mode: Nuclear Plant",
                self.world.plant_summary(),
                f"Feedwater flow: {self.world.feedwater_flow:.0f}%",
                f"Turbine vibration: {self.world.turbine_vibration:.0f}%",
                f"Blackout: {'yes' if self.world.plant_blackout else 'no'}",
                f"Alarm: {'active' if self.world.plant_alarm else 'clear'}",
                f"Message: {self.world.plant_message}",
                "",
                "Use the plant buttons only. No radar tracks, enemies, missiles, EW, or base damage run in this mode.",
            ]
            self.readout.configure(state="normal")
            self.readout.delete("1.0", "end")
            self.readout.insert("1.0", "\n".join(lines))
            self.readout.configure(state="disabled")
            return
        player = "active" if self.world.player_projectile_id in self.world.projectiles else "off"
        budget = f" | Budget {self.world.budget_points}" if self.world.game_mode in {"budget_waves", "linked_defense"} else ""
        self.score_text.set(f"Score {self.world.score} | Base {self.world.base_health}{budget}")
        radar_status = "offline" if not self.world.radar_alive else f"{self.world.radar_health}/{self.world.current_radar.health}"
        projectile = PROJECTILE_PROFILES[self.selected_projectile.get()]
        defense = INTERCEPTOR_PROFILES[self.selected_interceptor.get()]
        radar = self.world.current_radar
        selected_range = self.world._target_adjusted_radar_range(
            radar,
            self.world.radar_health,
            self.world.base_position,
            self.world.base_position + Vector2(0.0, min(radar.range, WORLD_HALF_SIZE)),
            radar_cross_section=projectile.radar_cross_section,
            altitude=self.world._initial_projectile_altitude(projectile),
            target_role=projectile.role,
            terrain_following=projectile.terrain_following,
            emitter=projectile.radar_seeking or projectile.role == "anti-radiation",
        )
        selected_engageable = self.world.radar_track_engageable(radar, projectile.role)
        lines = [
            f"Mode: {self.selected_mode.get()}",
            f"Map: {self.world.current_map.name}",
            f"Radar: {radar.name}",
            f"Radar year: {radar.year} ({radar.decade})",
            f"Radar era: {radar.era}",
            f"Radar type: {radar.sensor_type} | {radar.band}",
            f"Radar role: {radar.category}",
            f"Radar HUD: {radar.hud_style} | {radar.scan_pattern}",
            f"Radar scan: {self.world.radar_bearing_degrees:03.0f} deg / FOV {self.world.radar_fov_degrees(radar):.0f} deg / {'manual' if self.world.radar_manual_aim else 'auto'}",
            f"Sweep gate: {'required' if self.world.radar_requires_sweep_contact(radar) else 'continuous'} | regions {self.world.radar_simultaneous_region_count(radar)} x {self.world.radar_region_width_degrees(radar):.0f} deg",
            f"Radar track mode: {self.world.radar_track_mode(radar)}",
            f"Selected target link: {'weapon-quality' if selected_engageable else 'cue only'} | dyn range {selected_range:.0f}",
            f"Track quality model: {self.world.radar_track_quality(radar, projectile.role):.2f}",
            f"Radar height: acc {radar.height_accuracy:.2f} elev {radar.elevation_coverage:.0f}deg beam {radar.beam_width:.1f}deg",
            f"Radar behavior: scan {radar.scan_rate:.2f} low-alt {radar.low_altitude_factor:.2f}",
            f"Radar ECCM/precision: {radar.jamming_resistance:.2f}/{radar.tracking_precision:.2f}",
            f"Radar health: {radar_status}",
            f"Radar sites: {1 + len(self.world.radar_sites)} | {self.world.repair_summary()}",
            f"Hostile radars: {len(self.world.hostile_radar_sites)} | fire-control fixes {self.world.hostile_radar_pressure()}",
            self.world.ew_summary(),
            f"Radar pros: {', '.join(radar.pros[:2]) if radar.pros else 'balanced'}",
            f"Radar cons: {', '.join(radar.cons[:2]) if radar.cons else 'none'}",
            f"Weapon role/year: {projectile.role} / {projectile.year} ({projectile.decade})",
            f"Defense class/year: {defense.category} / {defense.year} ({defense.decade})",
            f"Enemy filter: {self.selected_enemy_decade.get()} / {self.selected_enemy_group.get()}",
            f"Defense ammo: {self.world.ammo_summary(self.selected_interceptor.get())}",
            f"Round inventory: {self.world.projectile_ammo_summary(self.selected_projectile.get())}",
            f"Manual cannon: {'armed' if self.manual_fire_armed.get() else 'safe'} | Place radar: {'on' if self.place_radar_mode.get() else 'off'} | Aim radar: {'on' if self.aim_radar_mode.get() else 'off'}",
            f"Wave: {self.world.wave_number}",
            f"Tracks: {len(self.world.tracker.tracks)}  Enemy tracks: {len(self.world.enemy_tracks)} / Enemies: {len(self.world.enemies)}",
            f"Projectiles: {len(self.world.projectiles)}  Interceptors: {len(self.world.interceptors)}",
            f"Player projectile: {player}",
            self.world.plant_summary() if self.world.game_mode == "nuclear_plant" else "",
            f"HQ call: {'ringing' if self.world.pending_hq_call else 'clear'}",
            "",
        ]
        for track in sorted(self.world.tracker.tracks, key=lambda item: item.projectile_id)[:8]:
            if self.world.is_ghost_track(track.projectile_id):
                lines.append(f"Ghost track conf={track.confidence:.2f}")
                continue
            solution = self.world.best_intercept_for(track.projectile_id, self.selected_interceptor.get(), speed_override=self.world.interceptor_speed)
            eta = f"{solution.time:4.1f}s" if solution else "none"
            track_state = "WEAP" if track.engageable else "CUE"
            lines.append(f"#{track.projectile_id} {track_state} {track.track_mode} vel={track.velocity.magnitude():5.1f} alt={track.altitude:5.0f} conf={track.confidence:.2f} eta={eta}")
        for enemy in sorted(self.world.tracked_enemies(), key=lambda item: item.enemy_id)[:6]:
            track = self.world.enemy_track_for(enemy.enemy_id)
            if track is None:
                continue
            solution = self.world.best_enemy_intercept_for(enemy.enemy_id, self.selected_interceptor.get(), speed_override=self.world.interceptor_speed)
            eta = f"{solution.time:4.1f}s" if solution else "none"
            track_state = "WEAP" if track.engageable else "CUE"
            lines.append(f"E{enemy.enemy_id} {track_state} {track.track_mode} {enemy.profile.platform} alt={track.altitude:5.0f} conf={track.confidence:.2f} src={track.source_name} eta={eta}")

        self.readout.configure(state="normal")
        self.readout.delete("1.0", "end")
        self.readout.insert("1.0", "\n".join(lines))
        self.readout.configure(state="disabled")


def main() -> None:
    app = RadarApp()
    app.mainloop()


if __name__ == "__main__":
    main()
