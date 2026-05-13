import unittest

from game_radar.models import Vector2
from game_radar.simulation import (
    ENEMY_PROFILES,
    INTERCEPTOR_PROFILES,
    PROJECTILE_PROFILES,
    RADAR_ERA_ORDER,
    RADAR_DECADE_LABELS,
    RADAR_PROFILES,
    SimulationWorld,
)


class SimulationTests(unittest.TestCase):
    def test_catalog_has_large_operator_roster(self) -> None:
        combined_count = (
            len(PROJECTILE_PROFILES)
            + len(INTERCEPTOR_PROFILES)
            + len(RADAR_PROFILES)
            + len(ENEMY_PROFILES)
        )

        self.assertGreaterEqual(combined_count, 900)
        self.assertIn("Chain Home Mk I", RADAR_PROFILES)
        self.assertIn("LTAMDS GaN AESA", RADAR_PROFILES)
        self.assertEqual(RADAR_DECADE_LABELS[0], "1930s")
        self.assertEqual(RADAR_PROFILES["AN/MPQ-53 PESA"].sensor_type, "PESA")
        self.assertTrue(all(any(radar.era == era for radar in RADAR_PROFILES.values()) for era in RADAR_ERA_ORDER))
        self.assertTrue(all(any(radar.decade == decade for radar in RADAR_PROFILES.values()) for decade in RADAR_DECADE_LABELS))
        self.assertTrue(any("J-band" in radar.band for radar in RADAR_PROFILES.values()))
        self.assertTrue(any(radar.sensor_type == "EASA/AESA" for radar in RADAR_PROFILES.values()))
        self.assertEqual(RADAR_PROFILES["Chain Home Mk I"].year, 1935)
        self.assertEqual(RADAR_PROFILES["AN/MPQ-53 PESA"].year, 1984)
        self.assertEqual(RADAR_PROFILES["LTAMDS GaN AESA"].scan_pattern, "aesa_multi_beam")
        self.assertEqual(RADAR_PROFILES["AN/MPQ-53 PESA"].scan_pattern, "pesa_sector")
        self.assertEqual(RADAR_PROFILES["P-18 Spoon Rest"].hud_style, "soviet_green")
        self.assertTrue(all(profile.decade for profile in PROJECTILE_PROFILES.values()))
        self.assertTrue(all(profile.decade for profile in INTERCEPTOR_PROFILES.values()))
        self.assertTrue(all(profile.decade for profile in ENEMY_PROFILES.values()))
        self.assertTrue(any(profile.role == "bomb" for profile in PROJECTILE_PROFILES.values()))

    def test_generated_catalog_names_are_operator_friendly(self) -> None:
        combined_names = tuple(PROJECTILE_PROFILES) + tuple(INTERCEPTOR_PROFILES) + tuple(ENEMY_PROFILES)

        self.assertFalse(any(" A1" in name or " A2" in name for name in combined_names))
        self.assertIn("ATACMS SRBM", PROJECTILE_PROFILES)
        self.assertNotIn("ATACMS Light Rocket", PROJECTILE_PROFILES)
        self.assertNotIn("ATACMS-style Light Rocket", PROJECTILE_PROFILES)
        self.assertIn("F-16C Block 50 Strike Flight", ENEMY_PROFILES)
        self.assertFalse(any("F-16 Recon" in name for name in ENEMY_PROFILES))

    def test_catalog_years_avoid_obvious_anachronisms(self) -> None:
        self.assertGreaterEqual(PROJECTILE_PROFILES["ATACMS SRBM"].year, 1991)
        self.assertEqual(PROJECTILE_PROFILES["Grad Light Rocket"].decade, "1960s")
        self.assertGreaterEqual(PROJECTILE_PROFILES["HARM Anti-Radiation Missile"].year, 1984)
        self.assertGreaterEqual(PROJECTILE_PROFILES["GBU-39 Glide Bomb"].year, 2006)
        self.assertEqual(PROJECTILE_PROFILES["GBU-39 Glide Bomb"].role, "bomb")
        self.assertGreaterEqual(INTERCEPTOR_PROFILES["Patriot ABM Interceptor"].year, 2000)
        self.assertGreaterEqual(INTERCEPTOR_PROFILES["Iron Beam Laser"].year, 2025)
        self.assertEqual(INTERCEPTOR_PROFILES["Iron Beam Laser"].category, "directed-energy")
        self.assertGreaterEqual(INTERCEPTOR_PROFILES["Oerlikon Autocannon"].year, 1950)
        self.assertEqual(ENEMY_PROFILES["F-16C Block 50 Strike Flight"].decade, "1990s")
        self.assertEqual(ENEMY_PROFILES["Su-24M Fencer Strike Flight"].decade, "1980s")
        self.assertEqual(ENEMY_PROFILES["H-6K Badger Bomber Flight"].decade, "2000s")
        self.assertEqual(ENEMY_PROFILES["B-52H Stratofortress Bomber Flight"].decade, "1960s")
        self.assertEqual(ENEMY_PROFILES["M270 MLRS Battery MLRS Troop"].decade, "1980s")
        self.assertEqual(ENEMY_PROFILES["M142 HIMARS Cell MLRS Troop"].decade, "2000s")
        self.assertFalse(any(profile.year < 1960 and ("EW Package" in name or profile.jammer_strength > 0) for name, profile in ENEMY_PROFILES.items()))
        self.assertFalse(any(profile.year < 1980 and "UAV" in name for name, profile in ENEMY_PROFILES.items()))

    def test_radar_catalog_does_not_backdate_modern_labels(self) -> None:
        mpq_53_profiles = {name: profile for name, profile in RADAR_PROFILES.items() if name.startswith("AN/MPQ-53")}

        self.assertTrue(mpq_53_profiles)
        self.assertFalse(any(profile.year < 1984 for profile in mpq_53_profiles.values()))
        self.assertFalse(any("Chain-era" in name or "WW2" in name for name in mpq_53_profiles))
        self.assertFalse(any(name.startswith("P-18") and "AESA" in name for name in RADAR_PROFILES))
        self.assertTrue(all(profile.year >= 1970 for name, profile in RADAR_PROFILES.items() if name.startswith("P-18")))

    def test_defender_ew_is_limited_by_radar_era(self) -> None:
        world = SimulationWorld()
        world.set_radar_profile("Chain Home Mk I")

        blocked = world.use_defender_ew("Burn Through")
        allowed = world.use_defender_ew("EMCON Silence")

        self.assertFalse(blocked)
        self.assertTrue(allowed)

    def test_enemy_launches_projectile(self) -> None:
        world = SimulationWorld()
        enemy = world.spawn_enemy("Scout UAV")
        enemy.next_launch_at = world.time

        world.step(0.1)

        self.assertGreaterEqual(len(world.projectiles), 1)

    def test_player_projectile_can_be_controlled(self) -> None:
        world = SimulationWorld()
        projectile = world.spawn_player_projectile("Tomahawk-style Cruise")
        world.set_player_control(Vector2(1, 0))

        world.step(0.1)

        self.assertIn(projectile.projectile_id, world.projectiles)
        self.assertGreater(world.projectiles[projectile.projectile_id].velocity.x, 0)

    def test_deploy_interceptor_uses_selected_profile(self) -> None:
        world = SimulationWorld()
        projectile = world.spawn_projectile("9M22U Grad Rocket", position=Vector2(120, 0), direction=Vector2(0, 0))
        world.aim_primary_radar_at(projectile.position)
        world.step(0.1)

        interceptor = world.deploy_interceptor(projectile.projectile_id, "Patriot PAC-3")

        self.assertIsNotNone(interceptor)
        assert interceptor is not None
        self.assertEqual(interceptor.profile.name, "Patriot PAC-3")

    def test_zero_direction_projectile_spawn_gets_live_heading(self) -> None:
        world = SimulationWorld()
        projectile = world.spawn_projectile("9M22U Grad Rocket", position=Vector2(120, 0), direction=Vector2(0, 0))

        self.assertGreater(projectile.velocity.magnitude(), 0)

    def test_linked_defense_mode_requires_compatible_radar(self) -> None:
        world = SimulationWorld()
        world.set_game_mode("linked_defense")
        world.budget_points = 999
        projectile = world.spawn_projectile("M31 GMLRS Rocket", position=Vector2(160, 0), direction=Vector2(0, 0))
        world.step(0.1)

        blocked = world.deploy_interceptor(projectile.projectile_id, "Patriot PAC-3")

        self.assertIsNone(blocked)

        world.budget_points = 999
        world.set_radar_profile("AN/MPQ-53 PESA")
        world.aim_primary_radar_at(projectile.position)
        world.step(0.1)
        launched = world.deploy_interceptor(projectile.projectile_id, "Patriot PAC-3")

        self.assertIsNotNone(launched)

    def test_placeable_radar_site_can_keep_network_alive(self) -> None:
        world = SimulationWorld()
        site = world.place_radar_site("AN/TPS-77", Vector2(240, -120))
        world.radar_health = 0

        self.assertIsNotNone(site)
        self.assertTrue(world.radar_alive)
        self.assertEqual(len(world.radar_sites), 1)

    def test_directional_radar_fov_controls_detection(self) -> None:
        world = SimulationWorld()
        world.set_radar_profile("AN/MPQ-53 PESA")
        world.aim_primary_radar_at(Vector2(250, 0))
        inside = world.spawn_projectile("155mm Artillery Shell", position=Vector2(140, 0), direction=Vector2(0, 1))
        outside = world.spawn_projectile("155mm Artillery Shell", position=Vector2(0, 140), direction=Vector2(1, 0))

        for _ in range(8):
            world.step(0.1)

        tracked_ids = {track.projectile_id for track in world.tracker.tracks}
        self.assertIn(inside.projectile_id, tracked_ids)
        self.assertNotIn(outside.projectile_id, tracked_ids)

        world.aim_primary_radar_at(Vector2(0, 250))
        self.assertTrue(
            world.radar_source_covers_position(
                world.current_radar,
                world.base_position,
                world.radar_health,
                world.radar_bearing_degrees,
                outside.position,
                radar_cross_section=outside.profile.radar_cross_section,
            )
        )

    def test_mechanical_circle_radar_waits_for_sweep_contact(self) -> None:
        world = SimulationWorld()
        world.set_radar_profile("AN/TPS-77")
        world.aim_primary_radar_at(Vector2(0, 260))
        projectile = world.spawn_projectile("155mm Artillery Shell", position=Vector2(180, 0), direction=Vector2(0, 1))
        projectile.velocity = Vector2(0, 0)
        projectile.altitude = 800.0
        projectile.vertical_velocity = 0.0

        self.assertTrue(
            world.radar_source_covers_position(
                world.current_radar,
                world.base_position,
                world.radar_health,
                world.radar_bearing_degrees,
                projectile.position,
                radar_cross_section=projectile.profile.radar_cross_section,
                altitude=projectile.altitude,
                target_role=projectile.profile.role,
            )
        )
        self.assertFalse(
            world.radar_source_detects_position_now(
                world.current_radar,
                world.base_position,
                world.radar_health,
                world.radar_bearing_degrees,
                projectile.position,
                radar_cross_section=projectile.profile.radar_cross_section,
                altitude=projectile.altitude,
                target_role=projectile.profile.role,
            )
        )

        for _ in range(5):
            world.step(0.1)
        self.assertNotIn(projectile.projectile_id, {track.projectile_id for track in world.tracker.tracks})

        world.aim_primary_radar_at(projectile.position)
        for _ in range(20):
            world.step(0.1)

        self.assertIn(projectile.projectile_id, {track.projectile_id for track in world.tracker.tracks})

    def test_aesa_radar_can_watch_multiple_regions_at_once(self) -> None:
        world = SimulationWorld()
        world.set_radar_profile("LTAMDS GaN AESA")
        world.aim_primary_radar_at(Vector2(300, 0))
        radar = world.current_radar

        self.assertGreater(world.radar_simultaneous_region_count(radar), 1)
        for target in (Vector2(160, 240), Vector2(260, 0), Vector2(160, -240)):
            self.assertTrue(
                world.radar_source_detects_position_now(
                    radar,
                    world.base_position,
                    world.radar_health,
                    world.radar_bearing_degrees,
                    target,
                    radar_cross_section=1.0,
                    altitude=900.0,
                    target_role="rocket",
                )
            )

    def test_ground_vehicle_launch_reveals_and_round_can_be_intercepted(self) -> None:
        world = SimulationWorld()
        world.set_radar_profile("AN/MPQ-53 PESA")
        enemy = world.spawn_enemy("BM-21 Grad Battery MLRS Troop Night Package")
        enemy.position = Vector2(180, 0)
        enemy.velocity = Vector2(0, 0)
        world.time = 1.0
        enemy.next_launch_at = world.time
        world.aim_primary_radar_at(enemy.position)

        self.assertFalse(world.is_enemy_visible(enemy))

        world.step(0.1)

        self.assertTrue(world.is_enemy_visible(enemy))
        vehicle_round = next(projectile for projectile in world.projectiles.values() if projectile.launcher_enemy_id == enemy.enemy_id)
        self.assertEqual(vehicle_round.launcher_platform, "ground")

        world.aim_primary_radar_at(vehicle_round.position)
        for _ in range(8):
            world.step(0.1)

        self.assertIn(vehicle_round.projectile_id, {track.projectile_id for track in world.tracker.tracks})
        self.assertIsNotNone(world.deploy_interceptor(vehicle_round.projectile_id, "Patriot PAC-3"))

    def test_enemy_strike_requires_weapon_quality_track_not_raw_visibility(self) -> None:
        world = SimulationWorld()
        world.set_radar_profile("AN/TPS-77")
        enemy = world.spawn_enemy("Bomber")
        enemy.position = Vector2(420, 0)
        enemy.velocity = Vector2(0, 0)
        enemy.altitude = 450.0
        enemy.next_launch_at = 999.0
        world.aim_primary_radar_at(Vector2(0, 260))

        self.assertTrue(world.is_enemy_visible(enemy))
        self.assertEqual(world.visible_enemies(), ())
        self.assertIsNone(world.deploy_interceptor_at_enemy(enemy.enemy_id, "NASAMS AMRAAM"))

        world.aim_primary_radar_at(enemy.position)
        for _ in range(60):
            world.aim_primary_radar_at(enemy.position)
            world.step(0.1)

        self.assertIn(enemy.enemy_id, {tracked.enemy_id for tracked in world.visible_enemies()})
        self.assertIsNotNone(world.enemy_track_for(enemy.enemy_id, require_engageable=True))
        self.assertIsNotNone(world.deploy_interceptor_at_enemy(enemy.enemy_id, "NASAMS AMRAAM"))

    def test_enemy_tracks_respect_directional_fov_before_engagement(self) -> None:
        world = SimulationWorld()
        world.set_radar_profile("AN/MPQ-53 PESA")
        enemy = world.spawn_enemy("Bomber")
        enemy.position = Vector2(0, 180)
        enemy.velocity = Vector2(0, 0)
        enemy.altitude = 250.0
        enemy.next_launch_at = 999.0
        world.aim_primary_radar_at(Vector2(260, 0))

        for _ in range(10):
            world.step(0.1)

        self.assertNotIn(enemy.enemy_id, {tracked.enemy_id for tracked in world.visible_enemies()})
        self.assertIsNone(world.deploy_interceptor_at_enemy(enemy.enemy_id, "Patriot PAC-3"))

        world.aim_primary_radar_at(enemy.position)
        for _ in range(20):
            world.aim_primary_radar_at(enemy.position)
            world.step(0.1)

        self.assertIsNotNone(world.enemy_track_for(enemy.enemy_id, require_engageable=True))

    def test_directional_ew_creates_real_radar_blackout_sector(self) -> None:
        world = SimulationWorld()
        world.set_radar_profile("LTAMDS GaN AESA")
        target = Vector2(360, 0)
        world.aim_primary_radar_at(target)
        before = world._target_adjusted_radar_range(
            world.current_radar,
            world.radar_health,
            world.base_position,
            target,
            radar_cross_section=1.0,
            altitude=800.0,
            target_role="drone",
        )

        self.assertTrue(world.use_defender_ew("Directional Noise Gate"))
        after = world._target_adjusted_radar_range(
            world.current_radar,
            world.radar_health,
            world.base_position,
            target,
            radar_cross_section=1.0,
            altitude=800.0,
            target_role="drone",
        )

        self.assertGreater(world.directional_ew_level_at(target), 0.0)
        self.assertLess(after, before)

    def test_sonic_weapon_disrupts_low_altitude_drone_but_not_ballistic_shell(self) -> None:
        world = SimulationWorld()
        drone = world.spawn_projectile("Shahed-style Loiterer", position=Vector2(140, 0), direction=Vector2(-1, 0))
        shell = world.spawn_projectile("155mm Artillery Shell", position=Vector2(145, 0), direction=Vector2(-1, 0))
        drone.altitude = 120.0
        shell.altitude = 120.0
        world.aim_primary_radar_at(Vector2(200, 0))

        self.assertTrue(world.use_sonic_weapon("Counter-UAS Sonic Fence", Vector2(200, 0)))

        self.assertNotIn(drone.projectile_id, world.projectiles)
        self.assertIn(shell.projectile_id, world.projectiles)

    def test_hostile_radar_can_guide_and_be_jammed_directionally(self) -> None:
        world = SimulationWorld()
        world.set_radar_profile("LTAMDS GaN AESA")
        site = world.spawn_hostile_radar("AN/MPQ-53 PESA", Vector2(260, 0))
        site.bearing_degrees = 180.0

        self.assertTrue(world.hostile_radar_has_fix_on_base(site))

        world.aim_primary_radar_at(site.position)
        self.assertTrue(world.use_defender_ew("Directional Noise Gate"))

        self.assertFalse(world.hostile_radar_has_fix_on_base(site))
        self.assertGreater(site.jammed_until, world.time)

    def test_player_anti_radiation_round_can_destroy_hostile_radar(self) -> None:
        world = SimulationWorld()
        site = world.spawn_hostile_radar("P-18 Spoon Rest", Vector2(30, 0))
        site.health = 1
        missile = world.spawn_projectile("AGM-88 HARM", owner="player", position=Vector2(0, 0), direction=Vector2(1, 0))
        missile.altitude = 50.0

        world.step(0.2)

        self.assertFalse(site.active)
        self.assertNotIn(missile.projectile_id, world.projectiles)

    def test_early_warning_radar_cues_but_cannot_weapon_track(self) -> None:
        world = SimulationWorld()
        world.set_radar_profile("Chain Home Mk I")
        world.aim_primary_radar_at(Vector2(0, 400))
        projectile = world.spawn_projectile("155mm Artillery Shell", position=Vector2(0, 260), direction=Vector2(1, 0))

        for _ in range(20):
            world.step(0.1)

        track = next(track for track in world.tracker.tracks if track.projectile_id == projectile.projectile_id)
        self.assertEqual(track.track_mode, "early-warning")
        self.assertFalse(track.engageable)
        self.assertIsNone(world.best_intercept_for(projectile.projectile_id, "M61 C-RAM Gun"))

    def test_fire_control_radar_produces_weapon_quality_track(self) -> None:
        world = SimulationWorld()
        world.set_radar_profile("AN/MPQ-53 PESA")
        world.aim_primary_radar_at(Vector2(250, 0))
        projectile = world.spawn_projectile("155mm Artillery Shell", position=Vector2(130, 0), direction=Vector2(0, 1))

        for _ in range(8):
            world.step(0.1)

        track = next(track for track in world.tracker.tracks if track.projectile_id == projectile.projectile_id)
        self.assertTrue(track.engageable)
        self.assertEqual(track.track_mode, "fire-control")
        self.assertIsNotNone(world.best_intercept_for(projectile.projectile_id, "Patriot PAC-3"))

    def test_radar_wire_repair_sequence_restores_primary_radar(self) -> None:
        world = SimulationWorld()
        world.radar_repair_needed = True
        world.radar_repair_sequence = ("red", "blue", "green")
        world.radar_repair_index = 0
        world.radar_health = 0

        self.assertTrue(world.repair_radar_wire("red"))
        self.assertTrue(world.repair_radar_wire("blue"))
        self.assertTrue(world.repair_radar_wire("green"))

        self.assertFalse(world.radar_repair_needed)
        self.assertGreater(world.radar_health, 0)

    def test_sandbox_mode_does_not_auto_spawn(self) -> None:
        world = SimulationWorld()
        world.set_game_mode("sandbox")

        world.step(10.0)

        self.assertEqual(world.projectiles, {})
        self.assertEqual(world.enemies, {})
        self.assertEqual(world.wave_number, 0)

    def test_waves_mode_spawns_wave(self) -> None:
        world = SimulationWorld()
        world.set_game_mode("waves")

        world.step(1.1)

        self.assertEqual(world.wave_number, 1)
        self.assertGreater(len(world.enemies), 0)

    def test_projectile_mode_spawns_player_projectile(self) -> None:
        world = SimulationWorld()
        world.set_game_mode("projectile", player_projectile_name="AGM-88 HARM")

        self.assertIsNotNone(world.player_projectile_id)
        assert world.player_projectile_id is not None
        self.assertEqual(world.projectiles[world.player_projectile_id].profile.name, "AGM-88 HARM")

    def test_jammer_creates_ghost_track_and_eccm_clears_it(self) -> None:
        world = SimulationWorld()
        world.spawn_enemy("Radar Jammer")
        world.next_ghost_at = world.time

        world.step(0.1)

        self.assertGreater(world.active_jammer_count(), 0)
        self.assertGreater(len(world.ghost_track_ids), 0)

        world.activate_eccm()

        self.assertEqual(world.ghost_track_ids, set())

    def test_jamming_level_reduces_under_eccm(self) -> None:
        world = SimulationWorld()
        jammer = world.spawn_enemy("EW Aircraft")
        point = jammer.position
        jammed_level = world.jamming_level_at(point)

        world.activate_eccm()
        eccm_level = world.jamming_level_at(point)

        self.assertGreater(jammed_level, 0)
        self.assertLess(eccm_level, jammed_level)

    def test_defense_ammo_limits_spam(self) -> None:
        world = SimulationWorld()
        world.defense_inventory["Patriot PAC-3"] = 1
        first = world.spawn_projectile("M31 GMLRS Rocket", position=Vector2(160, 0), direction=Vector2(0, 1))
        second = world.spawn_projectile("M31 GMLRS Rocket", position=Vector2(180, 0), direction=Vector2(0, 1))
        world.aim_primary_radar_at(first.position)
        world.step(0.1)

        launched = world.deploy_interceptor(first.projectile_id, "Patriot PAC-3")
        blocked = world.deploy_interceptor(second.projectile_id, "Patriot PAC-3")

        self.assertIsNotNone(launched)
        self.assertIsNone(blocked)

    def test_aircraft_loiter_instead_of_crashing_base(self) -> None:
        world = SimulationWorld()
        enemy = world.spawn_enemy("EW Aircraft")
        enemy.position = Vector2(0, 80)

        world.step(1.0)

        self.assertIn(enemy.enemy_id, world.enemies)
        self.assertEqual(world.base_health, 10)

    def test_anti_radiation_missile_can_damage_radar_in_budget_mode(self) -> None:
        world = SimulationWorld()
        world.set_game_mode("budget_waves")
        radar_health = world.radar_health
        missile = world.spawn_projectile("AGM-88 HARM", position=Vector2(0, 1), direction=Vector2(0, -1))

        world.step(0.1)

        self.assertNotIn(missile.projectile_id, world.projectiles)
        self.assertLess(world.radar_health, radar_health)

    def test_ew_actions_spend_power_without_cooldown(self) -> None:
        world = SimulationWorld()
        starting_power = world.ew_power

        first = world.use_defender_ew("Decoy Emitters")
        second = world.use_defender_ew("Decoy Emitters")

        self.assertTrue(first)
        self.assertTrue(second)
        self.assertLess(world.ew_power, starting_power)

    def test_budget_waves_awards_points_and_spawns_harder_wave(self) -> None:
        world = SimulationWorld()
        world.set_game_mode("budget_waves")
        starting_budget = world.budget_points

        world.step(1.1)

        self.assertEqual(world.wave_number, 1)
        self.assertGreater(world.budget_points, starting_budget)
        self.assertGreater(len(world.enemies), 0)

    def test_stealth_enemy_can_fade_from_visible_list(self) -> None:
        world = SimulationWorld()
        enemy = world.spawn_enemy("Stealth UAV")
        enemy.position = Vector2(120, 0)
        world.time = enemy.profile.stealth_period - 0.1

        self.assertFalse(world.is_enemy_visible(enemy))

        world.use_defender_ew("Burn Through")

        self.assertTrue(world.is_enemy_visible(enemy))

    def test_story_mode_starts_with_hq_call_and_answer_spawns_order(self) -> None:
        world = SimulationWorld()
        world.set_game_mode("story")

        self.assertIsNotNone(world.pending_hq_call)

        call = world.answer_hq_call()

        self.assertIsNotNone(call)
        self.assertEqual(world.hq_orders_completed, 1)
        self.assertGreater(len(world.enemies), 0)

    def test_manual_cannon_fire_is_gun_only(self) -> None:
        world = SimulationWorld()
        missile = world.spawn_projectile("9M22U Grad Rocket", position=Vector2(120, 0), direction=Vector2(0, 0))
        world.step(0.1)

        blocked = world.manual_cannon_fire("Iron Dome Tamir", Vector2(120, 0))
        fired = world.manual_cannon_fire("M61 C-RAM Gun", world.projectiles[missile.projectile_id].position)

        self.assertFalse(blocked)
        self.assertTrue(fired)
        self.assertNotIn(missile.projectile_id, world.projectiles)

    def test_nuclear_plant_controls_affect_plant_state(self) -> None:
        world = SimulationWorld()
        world.set_game_mode("nuclear_plant")
        rods = world.control_rod_position
        power = world.reactor_power

        world.plant_insert_rods()
        world.plant_toggle_pump_a()
        world.step(1.0)

        self.assertGreater(world.control_rod_position, rods)
        self.assertFalse(world.pump_a_online)
        self.assertTrue(world.pump_b_online)
        self.assertNotEqual(world.reactor_power, power)

    def test_nuclear_plant_mode_is_standalone(self) -> None:
        world = SimulationWorld()
        world.set_game_mode("nuclear_plant")
        world.next_plant_event_at = world.time

        world.step(20.0)

        self.assertEqual(world.projectiles, {})
        self.assertEqual(world.interceptors, {})
        self.assertEqual(world.enemies, {})
        self.assertEqual(world.tracker.tracks, ())
        self.assertNotEqual(world.plant_message, "Plant simulator ready")

    def test_radiological_event_affects_radar_environment(self) -> None:
        world = SimulationWorld()
        world._trigger_random_event("Radiological Alert")

        self.assertGreater(world.radiological_until, world.time)

    def test_radar_tracks_include_height(self) -> None:
        world = SimulationWorld()
        world.set_radar_profile("LTAMDS GaN AESA")
        projectile = world.spawn_projectile("Tomahawk-style Cruise", position=Vector2(100, 0), direction=Vector2(0, 0))
        world.aim_primary_radar_at(projectile.position)

        for _ in range(10):
            world.step(0.1)

        track = next(track for track in world.tracker.tracks if track.projectile_id == projectile.projectile_id)
        self.assertGreater(track.altitude, 0)
        self.assertNotEqual(world.current_radar.height_accuracy, 1.0)


if __name__ == "__main__":
    unittest.main()
