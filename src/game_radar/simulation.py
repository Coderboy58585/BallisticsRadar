from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count
from math import atan2, cos, degrees, pi, sin
from random import Random

from .intercept import InterceptSolution, solve_intercept
from .models import (
    EWActionProfile,
    Enemy,
    EnemyProfile,
    Interceptor,
    InterceptorProfile,
    MapProfile,
    Projectile,
    ProjectileProfile,
    RadarProfile,
    RadarSite,
    Vector2,
    ZERO,
)
from .tracker import Observation, RadarTracker


WORLD_HALF_SIZE = 500.0
BASE_RADIUS = 14.0
GAME_MODES = (
    "sandbox",
    "projectile",
    "waves",
    "budget_waves",
    "ground_assault",
    "linked_defense",
    "story",
    "nuclear_plant",
)

PROJECTILE_PROFILES: dict[str, ProjectileProfile] = {
    "9M22U Grad Rocket": ProjectileProfile("9M22U Grad Rocket", 118.0, 0.12, 1.25, "#ff6b4a", damage=1, score_value=18, cost=18, ammo=10, role="rocket", year=1963, decade="1960s"),
    "M31 GMLRS Rocket": ProjectileProfile("M31 GMLRS Rocket", 150.0, 0.28, 0.9, "#f77f00", damage=2, score_value=38, cost=40, ammo=6, role="rocket", year=2005, decade="2000s"),
    "81mm Mortar Bomb": ProjectileProfile("81mm Mortar Bomb", 70.0, 0.04, 0.7, "#ffd166", damage=1, score_value=22, cost=16, ammo=12, role="ballistic", year=1935, decade="1930s"),
    "155mm Artillery Shell": ProjectileProfile("155mm Artillery Shell", 95.0, 0.05, 1.05, "#bc6c25", damage=2, score_value=35, cost=32, ammo=8, role="ballistic", year=1942, decade="1940s"),
    "Iskander-style SRBM": ProjectileProfile("Iskander-style SRBM", 176.0, 0.42, 1.4, "#ff9f1c", damage=4, score_value=90, cost=90, ammo=2, role="ballistic", year=2006, decade="2000s"),
    "Tomahawk-style Cruise": ProjectileProfile("Tomahawk-style Cruise", 88.0, 1.05, 0.75, "#80ed99", damage=2, score_value=42, cost=45, ammo=5, role="cruise", terrain_following=True, year=1983, decade="1980s"),
    "Shahed-style Loiterer": ProjectileProfile("Shahed-style Loiterer", 54.0, 1.2, 0.45, "#90e0ef", damage=1, score_value=28, cost=24, ammo=8, role="drone", terrain_following=True, year=2019, decade="2010s"),
    "AGM-88 HARM": ProjectileProfile("AGM-88 HARM", 165.0, 1.1, 0.8, "#c77dff", damage=2, score_value=55, cost=65, ammo=4, role="anti-radiation", radar_seeking=True, year=1984, decade="1980s"),
    "Kh-31P ARM": ProjectileProfile("Kh-31P ARM", 190.0, 0.9, 0.95, "#b5179e", damage=3, score_value=65, cost=75, ammo=3, role="anti-radiation", radar_seeking=True, year=1990, decade="1990s"),
    "Radiation Seeker": ProjectileProfile("Radiation Seeker", 138.0, 1.25, 0.65, "#f72585", damage=2, score_value=48, cost=58, ammo=5, role="anti-radiation", radar_seeking=True, year=2022, decade="2020s+"),
}

PROJECTILE_FAMILIES = (
    ("Light Rocket", "rocket", 95.0, 0.16, 1.15, 1, "#ff6b4a"),
    ("Guided Rocket", "rocket", 135.0, 0.34, 0.92, 2, "#f77f00"),
    ("Mortar Bomb", "ballistic", 64.0, 0.05, 0.78, 1, "#ffd166"),
    ("Artillery Shell", "ballistic", 98.0, 0.08, 1.04, 2, "#bc6c25"),
    ("Guided Bomb", "bomb", 82.0, 0.24, 0.88, 2, "#e9c46a"),
    ("Glide Bomb", "bomb", 118.0, 0.42, 0.68, 2, "#f4a261"),
    ("SRBM", "ballistic", 170.0, 0.35, 1.35, 4, "#ff9f1c"),
    ("Cruise Missile", "cruise", 86.0, 1.0, 0.72, 2, "#80ed99"),
    ("Loitering Munition", "drone", 52.0, 1.15, 0.42, 1, "#90e0ef"),
    ("Anti-Radiation Missile", "anti-radiation", 160.0, 1.08, 0.78, 2, "#c77dff"),
    ("Hypersonic Glide", "ballistic", 205.0, 0.72, 1.18, 4, "#ffbe0b"),
    ("Sea-Skimmer", "cruise", 112.0, 1.25, 0.58, 2, "#00b4d8"),
)

PUBLIC_STYLE_PROJECTILES = (
    "ATACMS", "PrSM", "Storm Shadow", "SCALP", "JASSM", "Kalibr", "Kh-101", "Kh-22",
    "Harpoon", "NSM", "Exocet", "BrahMos", "Neptune", "Tochka", "Scud", "Fateh",
    "Zelzal", "Qassam", "Grad", "Smerch", "Uragan", "LORA", "Delilah", "Spike NLOS",
    "Brimstone", "Hellfire", "Maverick", "KAB Glide", "SDB", "JDAM-ER", "AASM", "HARM",
    "ALARM", "Martel", "Kh-58", "Kh-31", "ARMAT", "Paveway", "Vikhr", "Lancet",
    "Switchblade", "Warmate", "Phoenix Ghost", "Harop", "Harpy", "Shahed", "Kinzhal",
    "Zircon", "YJ-12", "YJ-18", "C-802", "P-800", "RBS-15", "Gabriel", "Sea Venom",
    "Meteor Strike", "Spear", "Brave-1", "Vulcano",
    "Taurus KEPD", "Popeye", "SLAM-ER", "JSOW", "APKWS", "DAGR", "Hydra 70", "S-8",
    "S-13", "S-25", "M26 MLRS", "M30A1", "M39 ATACMS", "DF-15", "DF-21", "Fajr-5",
    "Nazeat", "Qiam", "Nimrod", "LAHAT", "Spike ER", "TOW-2B", "Kornet", "Javelin",
    "BONUS Shell", "SMArt 155", "M982 Excalibur", "Copperhead", "BGM-109", "AGM-154",
    "GBU-39", "GBU-53", "GBU-24", "GBU-31", "GBU-38", "FAB Glide", "Hammer Glide",
    "SPEAR 3", "Rampage", "Rocks", "Blue Sparrow", "Silver Sparrow", "Black Sparrow",
    "Jericho Training", "Hyunmoo", "KTSSM", "Chunmoo", "FROG-7", "Honest John",
    "Little John", "Matador", "Regulus", "V-1 Training", "Tiny Tim", "RP-3",
)

INTERCEPTOR_PROFILES: dict[str, InterceptorProfile] = {
    "M61 C-RAM Gun": InterceptorProfile("M61 C-RAM Gun", 300.0, 7.0, "#f8f9fa", ammo=80, cost=6, power_cost=0.4, category="gun", year=1959, decade="1950s", compatible_radars=("fire-control", "counter-battery", "Sentinel", "AN/MPQ-64")),
    "Gepard 35mm Burst": InterceptorProfile("Gepard 35mm Burst", 260.0, 10.0, "#a7c957", ammo=50, cost=8, power_cost=0.5, category="gun", year=1976, decade="1970s", compatible_radars=("fire-control", "tracking", "search")),
    "Iron Dome Tamir": InterceptorProfile("Iron Dome Tamir", 210.0, 20.0, "#ffffff", ammo=12, cost=24, power_cost=1.2, category="missile", year=2011, decade="2010s", compatible_radars=("EL/M-2084", "Sentinel", "AN/MPQ-64", "AESA", "3D")),
    "NASAMS AMRAAM": InterceptorProfile("NASAMS AMRAAM", 235.0, 18.0, "#caf0f8", ammo=8, cost=34, power_cost=1.5, category="missile", year=1998, decade="1990s", compatible_radars=("Sentinel", "AN/MPQ-64", "NASAMS", "3D", "AESA")),
    "Patriot PAC-3": InterceptorProfile("Patriot PAC-3", 290.0, 13.0, "#ffd6a5", ammo=5, cost=58, power_cost=2.0, category="missile", year=2001, decade="2000s", compatible_radars=("AN/MPQ-53", "AN/MPQ-65", "LTAMDS", "PESA")),
    "SAMP/T Aster 30": InterceptorProfile("SAMP/T Aster 30", 270.0, 22.0, "#e0aaff", ammo=6, cost=52, power_cost=2.2, category="missile", year=2011, decade="2010s", compatible_radars=("Arabel", "SAMPSON", "Sea Fire", "AESA", "PESA")),
    "IFPC Laser": InterceptorProfile("IFPC Laser", 360.0, 8.0, "#70e000", ammo=999, cost=16, power_cost=5.0, category="directed-energy", year=2024, decade="2020s+", compatible_radars=("AESA", "digital", "LTAMDS", "glass")),
}

DEFENSE_FAMILIES = (
    ("Gun Burst", "gun", 250.0, 8.0, 70, 7, 0.5, "#f8f9fa"),
    ("Autocannon", "gun", 270.0, 10.0, 55, 9, 0.7, "#a7c957"),
    ("SHORAD Missile", "missile", 205.0, 18.0, 14, 22, 1.2, "#ffffff"),
    ("MRAD Missile", "missile", 240.0, 20.0, 9, 38, 1.7, "#caf0f8"),
    ("ABM Interceptor", "missile", 300.0, 14.0, 5, 62, 2.5, "#ffd6a5"),
    ("Area Defense", "missile", 260.0, 25.0, 7, 54, 2.1, "#e0aaff"),
    ("Laser", "directed-energy", 360.0, 8.0, 999, 18, 5.0, "#70e000"),
)

PUBLIC_STYLE_DEFENSES = (
    "Avenger", "Skyranger", "Skynex", "Mantis", "Phalanx", "Centurion", "Pantsir", "Tor",
    "Buk", "Osa", "Strela", "Tunguska", "NASAMS", "IRIS-T SLM", "Crotale", "MICA VL",
    "CAMM", "Sea Ceptor", "Barak", "David Sling", "Iron Dome", "Arrow", "Patriot", "THAAD",
    "SAMP/T", "Aegis", "SM-2", "SM-3", "SM-6", "RIM-7", "RIM-116", "HQ-9", "HQ-16",
    "Akash", "Spyder", "Rapier", "Roland", "Starstreak", "Martlet", "Mistral", "Stinger",
    "Grom", "Piorun", "RBS-70", "M61", "Gepard", "Vulcan", "Oerlikon", "Goalkeeper",
    "Iron Beam", "HELWS",
)

RADAR_PROFILES: dict[str, RadarProfile] = {
    "AN/MPQ-64 Sentinel": RadarProfile("AN/MPQ-64 Sentinel", range=420.0, noise=1.0, ew_power=80.0, ew_regen=5.0, terrain_resistance=0.45, health=6, cost=120, color="#9bf6ff", abilities=("mobile", "good clutter handling")),
    "AN/TPS-77": RadarProfile("AN/TPS-77", range=520.0, noise=0.82, ew_power=95.0, ew_regen=4.2, terrain_resistance=0.62, health=7, cost=180, color="#bde0fe", abilities=("long range", "terrain mapping")),
    "AN/TPY-2": RadarProfile("AN/TPY-2", range=610.0, noise=0.68, ew_power=120.0, ew_regen=3.4, terrain_resistance=0.5, health=5, cost=260, color="#fefae0", abilities=("high fidelity", "ballistic focus")),
    "91N6E Big Bird": RadarProfile("91N6E Big Bird", range=560.0, noise=0.78, ew_power=105.0, ew_regen=4.0, terrain_resistance=0.54, health=8, cost=230, color="#caffbf", abilities=("wide area", "high endurance")),
    "P-18 Spoon Rest": RadarProfile("P-18 Spoon Rest", range=470.0, noise=1.25, ew_power=140.0, ew_regen=6.0, terrain_resistance=0.3, health=9, cost=150, color="#ffadad", abilities=("VHF style", "anti-stealth game bonus")),
}

RADAR_PROFILES.update(
    {
        "Chain Home Mk I": RadarProfile(
            "Chain Home Mk I",
            range=330.0,
            noise=1.9,
            ew_power=46.0,
            ew_regen=2.2,
            terrain_resistance=0.16,
            health=10,
            cost=70,
            color="#cdb4db",
            abilities=("early warning", "huge returns"),
            era="1930s",
            sensor_type="fixed early-warning array",
            band="HF/VHF",
            pros=("long warning time", "rugged"),
            cons=("poor precision", "weak low-altitude coverage"),
        ),
        "SCR-270": RadarProfile(
            "SCR-270",
            range=300.0,
            noise=1.65,
            ew_power=52.0,
            ew_regen=2.7,
            terrain_resistance=0.2,
            health=8,
            cost=80,
            color="#adb5bd",
            abilities=("mobile early warning", "simple sweep"),
            era="1940s",
            sensor_type="mechanical pulse radar",
            band="VHF",
            pros=("mobile for its era", "cheap"),
            cons=("slow scan", "coarse tracks"),
        ),
        "Wuerzburg Fire Control": RadarProfile(
            "Wuerzburg Fire Control",
            range=220.0,
            noise=1.25,
            ew_power=48.0,
            ew_regen=3.2,
            terrain_resistance=0.24,
            health=5,
            cost=65,
            color="#f4a261",
            abilities=("fire control", "short range"),
            era="1940s",
            sensor_type="dish fire-control radar",
            band="UHF",
            pros=("better precision", "cheap guns pairing"),
            cons=("short reach", "fragile"),
        ),
        "P-14 Tall King": RadarProfile(
            "P-14 Tall King",
            range=500.0,
            noise=1.28,
            ew_power=116.0,
            ew_regen=4.8,
            terrain_resistance=0.28,
            health=11,
            cost=170,
            color="#f08080",
            abilities=("VHF search", "anti-stealth game bonus"),
            era="Cold War",
            sensor_type="VHF search radar",
            band="VHF",
            pros=("sees low-signature targets better", "durable"),
            cons=("less precise", "large emitter"),
        ),
        "SNR-75 Fan Song": RadarProfile(
            "SNR-75 Fan Song",
            range=360.0,
            noise=0.95,
            ew_power=86.0,
            ew_regen=4.4,
            terrain_resistance=0.36,
            health=6,
            cost=130,
            color="#ffd166",
            abilities=("missile guidance", "narrow beam"),
            era="Cold War",
            sensor_type="tracking/guidance radar",
            band="E/F-band style",
            pros=("good engagement quality", "focused beam"),
            cons=("jamming-sensitive", "not wide-area"),
        ),
        "AN/MPQ-53 PESA": RadarProfile(
            "AN/MPQ-53 PESA",
            range=500.0,
            noise=0.72,
            ew_power=104.0,
            ew_regen=4.4,
            terrain_resistance=0.52,
            health=7,
            cost=220,
            color="#fefae0",
            abilities=("PESA track-while-scan", "fire-control quality"),
            era="late Cold War",
            sensor_type="PESA",
            band="C-band style",
            pros=("fast beam steering", "good intercept support"),
            cons=("power hungry", "expensive"),
        ),
        "LTAMDS GaN AESA": RadarProfile(
            "LTAMDS GaN AESA",
            range=640.0,
            noise=0.56,
            ew_power=145.0,
            ew_regen=5.2,
            terrain_resistance=0.68,
            health=8,
            cost=330,
            color="#a0c4ff",
            abilities=("AESA", "wide coverage", "high ECCM"),
            era="modern",
            sensor_type="AESA",
            band="multi-band game abstraction",
            pros=("excellent track quality", "strong EW reserve"),
            cons=("very expensive", "priority target"),
        ),
    }
)

RADAR_FAMILIES = (
    ("Search Radar", 440.0, 1.05, 82.0, 4.8, 0.45, 6, "#9bf6ff", ("search", "balanced")),
    ("Long-Range Radar", 560.0, 0.88, 96.0, 4.0, 0.58, 7, "#bde0fe", ("long range", "wide area")),
    ("Fire-Control Radar", 400.0, 0.68, 84.0, 5.6, 0.5, 5, "#fefae0", ("high fidelity", "fire control")),
    ("Low-Frequency Radar", 480.0, 1.18, 130.0, 5.8, 0.32, 8, "#ffadad", ("low frequency", "anti-stealth game bonus")),
    ("Passive Sensor", 320.0, 1.35, 150.0, 6.5, 0.7, 4, "#caffbf", ("passive", "low emissions")),
    ("Counter-Battery Radar", 360.0, 0.9, 72.0, 5.2, 0.4, 5, "#ffd6a5", ("ballistic focus", "fast track")),
)

PUBLIC_STYLE_RADARS = (
    "AN/MPQ-53", "AN/MPQ-65", "AN/MPQ-64", "AN/TPS-59", "AN/TPS-77", "AN/TPY-2",
    "AN/SPY-1", "AN/SPY-6", "TRML-4D", "Giraffe AMB", "Giraffe 4A", "Kronos",
    "Ground Master 200", "Ground Master 400", "SMART-L", "SAMPSON", "S1850M", "Sea Fire",
    "APAR", "EL/M-2084", "EL/M-2080", "Green Pine", "Arabel", "Nebo", "Gamma-DE",
    "Protivnik", "Podlet", "91N6E", "92N6E", "96L6E", "P-18", "Vostok-E", "YLC-8",
    "JY-27A", "JY-26", "Type 305B", "Rajendra", "Swordfish", "Rezonans", "Kolchuga",
    "Vera-NG", "Tamara", "Silent Sentry", "BOR-A", "COBRA", "ARTHUR", "Firefinder",
    "TPQ-36", "TPQ-37", "TPQ-53",
)

RADAR_LABEL_YEARS = {
    "AN/MPQ-53": 1984,
    "AN/MPQ-65": 2003,
    "AN/MPQ-64": 1997,
    "AN/TPS-59": 1982,
    "AN/TPS-77": 1997,
    "AN/TPY-2": 2004,
    "AN/SPY-1": 1983,
    "AN/SPY-6": 2020,
    "TRML-4D": 2018,
    "Giraffe AMB": 2005,
    "Giraffe 4A": 2014,
    "Kronos": 2008,
    "Ground Master 200": 2008,
    "Ground Master 400": 2008,
    "SMART-L": 1995,
    "SAMPSON": 2008,
    "S1850M": 2008,
    "Sea Fire": 2021,
    "APAR": 2003,
    "EL/M-2084": 2008,
    "EL/M-2080": 2000,
    "Green Pine": 2000,
    "Arabel": 1997,
    "Nebo": 1986,
    "Gamma-DE": 2008,
    "Protivnik": 1999,
    "Podlet": 2015,
    "91N6E": 2007,
    "92N6E": 2007,
    "96L6E": 2000,
    "P-18": 1970,
    "Vostok-E": 2007,
    "YLC-8": 2010,
    "JY-27A": 2015,
    "JY-26": 2014,
    "Type 305B": 2010,
    "Rajendra": 2008,
    "Swordfish": 2012,
    "Rezonans": 2015,
    "Kolchuga": 1987,
    "Vera-NG": 2013,
    "Tamara": 1986,
    "Silent Sentry": 1998,
    "BOR-A": 1990,
    "COBRA": 2002,
    "ARTHUR": 1994,
    "Firefinder": 1978,
    "TPQ-36": 1978,
    "TPQ-37": 1980,
    "TPQ-53": 2010,
}

RADAR_LABEL_TAGS = {
    "AN/MPQ-53": ("pesa",),
    "AN/MPQ-65": ("pesa",),
    "AN/MPQ-64": ("pulse_doppler", "aesa_3d"),
    "AN/TPS-59": ("pulse_doppler", "aesa_3d"),
    "AN/TPS-77": ("pulse_doppler", "aesa_3d"),
    "AN/TPY-2": ("abm_aesa",),
    "AN/SPY-1": ("pesa",),
    "AN/SPY-6": ("gan_aesa",),
    "TRML-4D": ("gan_aesa",),
    "Giraffe AMB": ("aesa_3d",),
    "Giraffe 4A": ("gan_aesa",),
    "Kronos": ("aesa_3d", "gan_aesa"),
    "Ground Master 200": ("aesa_3d", "gan_aesa"),
    "Ground Master 400": ("aesa_3d", "gan_aesa"),
    "SMART-L": ("pulse_doppler", "aesa_3d"),
    "SAMPSON": ("gan_aesa",),
    "S1850M": ("aesa_3d",),
    "Sea Fire": ("gan_aesa",),
    "APAR": ("aesa_3d",),
    "EL/M-2084": ("aesa_3d", "gan_aesa"),
    "EL/M-2080": ("abm_aesa",),
    "Green Pine": ("abm_aesa",),
    "Arabel": ("pesa",),
    "Nebo": ("vhf",),
    "Gamma-DE": ("pulse_doppler", "aesa_3d"),
    "Protivnik": ("pulse_doppler",),
    "Podlet": ("pulse_doppler", "aesa_3d"),
    "91N6E": ("pulse_doppler", "aesa_3d"),
    "92N6E": ("pesa",),
    "96L6E": ("pulse_doppler", "aesa_3d"),
    "P-18": ("vhf",),
    "Vostok-E": ("vhf",),
    "YLC-8": ("vhf",),
    "JY-27A": ("vhf",),
    "JY-26": ("aesa_3d", "gan_aesa"),
    "Type 305B": ("aesa_3d", "gan_aesa"),
    "Rajendra": ("pesa",),
    "Swordfish": ("abm_aesa",),
    "Rezonans": ("vhf",),
    "Kolchuga": ("passive",),
    "Vera-NG": ("passive",),
    "Tamara": ("passive",),
    "Silent Sentry": ("passive",),
    "BOR-A": ("passive",),
    "COBRA": ("counter_battery",),
    "ARTHUR": ("counter_battery",),
    "Firefinder": ("counter_battery",),
    "TPQ-36": ("counter_battery",),
    "TPQ-37": ("counter_battery",),
    "TPQ-53": ("counter_battery",),
}

RADAR_VARIANT_BLOCKS = (
    ("", 0, 1.00),
    ("Mobility Upgrade", 4, 0.98),
    ("ECCM Upgrade", 8, 1.04),
    ("Digital Refit", 14, 1.07),
)

RADAR_ERA_ORDER = (
    "WW2 1930s",
    "WW2 1940s",
    "Early Cold War 1950s",
    "Cold War 1960s",
    "Cold War 1970s",
    "Digital 1980s",
    "Post-Cold War 1990s",
    "Networked 2000s",
    "Modern 2010s",
    "Modern 2020s",
)

RADAR_ERA_YEARS = {
    "WW2 1930s": 1935,
    "WW2 1940s": 1940,
    "Early Cold War 1950s": 1950,
    "Cold War 1960s": 1960,
    "Cold War 1970s": 1970,
    "Digital 1980s": 1980,
    "Post-Cold War 1990s": 1990,
    "Networked 2000s": 2000,
    "Modern 2010s": 2010,
    "Modern 2020s": 2020,
}

RADAR_DECADE_LABELS = (
    "1930s",
    "1940s",
    "1950s",
    "1960s",
    "1970s",
    "1980s",
    "1990s",
    "2000s",
    "2010s",
    "2020s+",
)
CATALOG_DECADE_LABELS = RADAR_DECADE_LABELS

PROFILE_BLOCKS = (
    ("", 1.00, 0),
    ("Extended Range", 1.08, 6),
    ("Low Observable", 0.98, 8),
    ("Terminal Seeker", 1.04, 10),
)

DEFENSE_BLOCKS = (
    ("", 1.00, 0),
    ("Improved Fire-Control", 1.06, 4),
    ("Extended Magazine", 0.97, 6),
)

ENEMY_BLOCKS = (
    ("", 1.00, 0),
    ("Night Package", 0.94, 12),
    ("Heavy Package", 0.86, 22),
    ("EW Package", 0.98, 18),
)

RADAR_ARCHITECTURES = (
    (
        "Chain-era Early Warning",
        "WW2 1930s",
        "fixed early-warning array",
        "HF/VHF",
        "early-warning",
        330.0,
        1.9,
        46.0,
        2.2,
        0.16,
        10,
        "#cdb4db",
        ("early warning", "huge returns"),
        ("long warning time", "rugged electronics"),
        ("poor precision", "weak low-altitude picture"),
        0.52,
        0.62,
        0.20,
        0.04,
        0.58,
    ),
    (
        "WW2 Fire-Control Dish",
        "WW2 1940s",
        "mechanical dish fire-control",
        "UHF/J-band style",
        "fire-control",
        230.0,
        1.2,
        48.0,
        3.1,
        0.24,
        5,
        "#f4a261",
        ("gun-laying", "short-range precision"),
        ("good local accuracy", "low cost"),
        ("short reach", "fragile site"),
        0.68,
        0.72,
        0.10,
        0.08,
        0.88,
    ),
    (
        "Height-Finder",
        "Early Cold War 1950s",
        "mechanical height-finder",
        "S-band",
        "height-finder",
        360.0,
        1.35,
        62.0,
        3.0,
        0.30,
        7,
        "#adb5bd",
        ("altitude cueing", "rugged"),
        ("better height estimates", "cheap upgrades"),
        ("slow scan", "needs pairing"),
        0.72,
        0.80,
        0.12,
        0.10,
        0.82,
    ),
    (
        "VHF Search",
        "Cold War 1960s",
        "VHF search radar",
        "VHF",
        "search",
        500.0,
        1.24,
        112.0,
        4.7,
        0.30,
        10,
        "#ffadad",
        ("low-frequency search", "anti-stealth game bonus"),
        ("wide-area coverage", "low-signature warning"),
        ("coarse tracks", "large emitter"),
        0.76,
        0.72,
        0.42,
        0.18,
        0.70,
    ),
    (
        "Pulse-Doppler Search",
        "Cold War 1970s",
        "pulse-Doppler mechanical",
        "L/S-band",
        "search",
        470.0,
        0.94,
        88.0,
        4.5,
        0.48,
        7,
        "#bde0fe",
        ("moving-target indication", "clutter rejection"),
        ("better low flyers", "balanced scan"),
        ("medium EW reserve", "less fire-control quality"),
        0.96,
        1.08,
        0.20,
        0.28,
        1.00,
    ),
    (
        "Counter-Battery Radar",
        "Cold War 1970s",
        "weapon-locating radar",
        "S/C-band",
        "counter-battery",
        360.0,
        0.90,
        72.0,
        5.2,
        0.40,
        5,
        "#ffd6a5",
        ("ballistic focus", "fast track"),
        ("quick launch-point estimate", "good shell tracks"),
        ("narrow sector", "less useful for aircraft"),
        1.08,
        0.90,
        0.12,
        0.24,
        1.12,
    ),
    (
        "Passive ESM Sensor",
        "Digital 1980s",
        "passive coherent-location/ESM",
        "VHF/UHF emitters",
        "passive",
        320.0,
        1.35,
        150.0,
        6.5,
        0.70,
        4,
        "#caffbf",
        ("passive", "low emissions"),
        ("hard to target", "sees emitters without sweeping"),
        ("poor fire-control quality", "depends on target emissions"),
        0.88,
        0.96,
        0.18,
        0.58,
        0.82,
    ),
    (
        "PESA Engagement Radar",
        "Digital 1980s",
        "PESA",
        "C/J-band style",
        "engagement",
        520.0,
        0.72,
        106.0,
        4.2,
        0.54,
        7,
        "#fefae0",
        ("track-while-scan", "fire-control quality"),
        ("fast electronic steering", "strong intercept support"),
        ("power hungry", "expensive"),
        1.28,
        1.15,
        0.30,
        0.42,
        1.22,
    ),
    (
        "X-band ABM AESA",
        "Post-Cold War 1990s",
        "AESA",
        "X/J-band style",
        "ballistic-defense",
        620.0,
        0.62,
        128.0,
        3.8,
        0.50,
        6,
        "#fefae0",
        ("high fidelity", "ballistic focus"),
        ("excellent precision", "fast handoff"),
        ("narrow-sector bias", "high cost"),
        1.45,
        0.98,
        0.32,
        0.52,
        1.42,
    ),
    (
        "Networked 3D AESA",
        "Networked 2000s",
        "AESA",
        "S-band",
        "3D search",
        560.0,
        0.70,
        118.0,
        5.2,
        0.62,
        8,
        "#9bf6ff",
        ("3D search", "network handoff"),
        ("good clutter handling", "steady EW reserve"),
        ("expensive", "visible emitter"),
        1.42,
        1.22,
        0.34,
        0.56,
        1.28,
    ),
    (
        "GaN AESA Multirole",
        "Modern 2010s",
        "AESA",
        "S/C/J-band style",
        "multirole",
        650.0,
        0.55,
        150.0,
        5.6,
        0.70,
        8,
        "#a0c4ff",
        ("GaN AESA", "wide coverage", "high ECCM"),
        ("excellent track quality", "strong EW reserve"),
        ("very expensive", "priority target"),
        1.72,
        1.35,
        0.46,
        0.68,
        1.58,
    ),
    (
        "EASA Training Alias",
        "Modern 2020s",
        "EASA/AESA",
        "multi-band",
        "multirole",
        680.0,
        0.50,
        165.0,
        6.0,
        0.74,
        9,
        "#70e000",
        ("digital beamforming", "adaptive waveforms"),
        ("best synthetic picture", "fast retask"),
        ("very high cost", "complex power management"),
        1.88,
        1.42,
        0.52,
        0.76,
        1.70,
    ),
)

HISTORICAL_RADAR_ROSTER = (
    ("Chain Home Mk I", "WW2 1930s", "fixed early-warning array", "HF/VHF", "early-warning", 330.0, 1.90, 46.0, 2.2, 0.16, 10, "#cdb4db"),
    ("Freya FuMG 80", "WW2 1940s", "mechanical early-warning", "VHF/UHF", "early-warning", 285.0, 1.55, 50.0, 2.6, 0.22, 7, "#d8b4a0"),
    ("Wuerzburg Fire Control", "WW2 1940s", "mechanical dish fire-control", "UHF/J-band style", "fire-control", 220.0, 1.25, 48.0, 3.2, 0.24, 5, "#f4a261"),
    ("SCR-270", "WW2 1940s", "mechanical pulse radar", "VHF", "early-warning", 300.0, 1.65, 52.0, 2.7, 0.20, 8, "#adb5bd"),
    ("SCR-584", "WW2 1940s", "conical-scan fire-control", "S-band/J-band style", "fire-control", 260.0, 1.05, 56.0, 3.5, 0.28, 6, "#ffd6a5"),
    ("CXAM Ship Radar", "WW2 1940s", "naval search radar", "VHF", "naval search", 275.0, 1.60, 54.0, 2.5, 0.18, 8, "#90e0ef"),
    ("Type 13 Early Warning", "WW2 1940s", "fixed early-warning array", "VHF", "early-warning", 245.0, 1.80, 42.0, 2.0, 0.14, 6, "#c8b6ff"),
    ("GL Mk III Gun Laying", "WW2 1940s", "gun-laying radar", "S-band/J-band style", "fire-control", 215.0, 1.18, 45.0, 3.1, 0.25, 5, "#f4a261"),
    ("P-8 Knife Rest", "Early Cold War 1950s", "VHF search radar", "VHF", "search", 355.0, 1.45, 72.0, 3.2, 0.24, 8, "#ffadad"),
    ("AN/FPS-3 Search Radar", "Early Cold War 1950s", "mechanical search radar", "S-band", "search", 385.0, 1.22, 68.0, 3.4, 0.36, 7, "#bde0fe"),
    ("AN/FPS-6 Height Finder", "Early Cold War 1950s", "height-finder", "S-band", "height-finder", 360.0, 1.34, 64.0, 3.0, 0.31, 7, "#adb5bd"),
    ("P-12 Spoon Rest", "Cold War 1960s", "VHF search radar", "VHF", "search", 430.0, 1.34, 92.0, 4.2, 0.28, 9, "#ffadad"),
    ("P-18 Spoon Rest", "Cold War 1970s", "VHF search radar", "VHF", "search", 470.0, 1.25, 140.0, 6.0, 0.30, 9, "#ffadad"),
    ("P-14 Tall King", "Cold War 1960s", "VHF search radar", "VHF", "search", 500.0, 1.28, 116.0, 4.8, 0.28, 11, "#f08080"),
    ("SNR-75 Fan Song", "Cold War 1960s", "tracking/guidance radar", "E/F/J-band style", "engagement", 360.0, 0.95, 86.0, 4.4, 0.36, 6, "#ffd166"),
    ("P-15 Flat Face", "Cold War 1960s", "2D acquisition radar", "UHF", "search", 390.0, 1.18, 82.0, 4.0, 0.34, 7, "#caffbf"),
    ("SNR-125 Low Blow", "Cold War 1970s", "fire-control radar", "I/J-band style", "engagement", 350.0, 0.90, 88.0, 4.6, 0.42, 6, "#ffdd99"),
    ("1S91 Straight Flush", "Cold War 1970s", "tracking/guidance radar", "G/H/J-band style", "engagement", 370.0, 0.86, 90.0, 4.8, 0.46, 7, "#caffbf"),
    ("AN/TPS-43", "Cold War 1970s", "3D mechanical search", "S-band", "3D search", 460.0, 0.96, 82.0, 4.4, 0.48, 7, "#bde0fe"),
    ("AN/MPQ-46 HAWK", "Cold War 1970s", "continuous-wave illuminator", "J-band style", "fire-control", 340.0, 0.84, 78.0, 4.8, 0.44, 5, "#fefae0"),
    ("AN/MPQ-53 PESA", "Digital 1980s", "PESA", "C/J-band style", "engagement", 500.0, 0.72, 104.0, 4.4, 0.52, 7, "#fefae0"),
    ("AN/SPY-1 PESA", "Digital 1980s", "naval PESA", "S-band", "naval 3D search", 570.0, 0.76, 112.0, 4.8, 0.58, 9, "#9bf6ff"),
    ("N011M Bars PESA", "Digital 1980s", "PESA", "X/J-band style", "airborne multirole", 410.0, 0.70, 96.0, 4.2, 0.44, 5, "#d0f4de"),
    ("AN/MPQ-64 Sentinel", "Post-Cold War 1990s", "3D pulse-Doppler", "X/J-band style", "short-range search", 420.0, 1.00, 80.0, 5.0, 0.45, 6, "#9bf6ff"),
    ("AN/TPS-77", "Post-Cold War 1990s", "3D pulse-Doppler", "L-band", "long-range 3D", 520.0, 0.82, 95.0, 4.2, 0.62, 7, "#bde0fe"),
    ("ARTHUR Counter-Battery", "Post-Cold War 1990s", "PESA counter-battery", "C-band", "counter-battery", 380.0, 0.82, 82.0, 5.2, 0.46, 5, "#ffd6a5"),
    ("AN/TPY-2 X-band AESA", "Networked 2000s", "AESA", "X/J-band style", "ballistic-defense", 610.0, 0.68, 120.0, 3.4, 0.50, 5, "#fefae0"),
    ("EL/M-2084 MMR AESA", "Networked 2000s", "AESA", "S-band", "multimission", 525.0, 0.70, 118.0, 5.0, 0.62, 7, "#caffbf"),
    ("Giraffe AMB 3D", "Networked 2000s", "3D AESA", "C-band", "mobile search", 470.0, 0.74, 104.0, 5.4, 0.66, 6, "#b8f2e6"),
    ("91N6E Big Bird", "Networked 2000s", "digital PESA", "S/L-band style", "long-range 3D", 560.0, 0.78, 105.0, 4.0, 0.54, 8, "#caffbf"),
    ("TRML-4D AESA", "Modern 2010s", "AESA", "C-band", "multirole", 590.0, 0.60, 132.0, 5.6, 0.70, 8, "#a0c4ff"),
    ("SAMPSON AESA", "Modern 2010s", "naval AESA", "S/J-band style", "naval multirole", 600.0, 0.58, 136.0, 5.5, 0.70, 8, "#90e0ef"),
    ("AN/SPY-6 AMDR AESA", "Modern 2020s", "GaN AESA", "S-band", "naval 3D search", 690.0, 0.52, 162.0, 5.8, 0.74, 10, "#70e000"),
    ("LTAMDS GaN AESA", "Modern 2020s", "GaN AESA", "S/C/J-band style", "multirole", 640.0, 0.56, 145.0, 5.2, 0.68, 8, "#a0c4ff"),
    ("Sea Fire 500 AESA", "Modern 2020s", "AESA", "S-band", "naval multirole", 620.0, 0.54, 150.0, 5.8, 0.72, 8, "#9bf6ff"),
    ("Ground Master 400 Alpha", "Modern 2020s", "digital AESA", "S-band", "long-range 3D", 665.0, 0.56, 152.0, 5.7, 0.72, 9, "#bde0fe"),
)

HISTORICAL_RADAR_YEARS = {
    "Chain Home Mk I": 1935,
    "Freya FuMG 80": 1938,
    "Wuerzburg Fire Control": 1940,
    "SCR-270": 1940,
    "SCR-584": 1943,
    "CXAM Ship Radar": 1940,
    "Type 13 Early Warning": 1941,
    "GL Mk III Gun Laying": 1942,
    "P-8 Knife Rest": 1950,
    "AN/FPS-3 Search Radar": 1950,
    "AN/FPS-6 Height Finder": 1954,
    "P-12 Spoon Rest": 1956,
    "P-18 Spoon Rest": 1970,
    "P-14 Tall King": 1959,
    "SNR-75 Fan Song": 1957,
    "P-15 Flat Face": 1955,
    "SNR-125 Low Blow": 1961,
    "1S91 Straight Flush": 1967,
    "AN/TPS-43": 1963,
    "AN/MPQ-46 HAWK": 1972,
    "AN/MPQ-53 PESA": 1984,
    "AN/SPY-1 PESA": 1983,
    "N011M Bars PESA": 2002,
    "AN/MPQ-64 Sentinel": 1997,
    "AN/TPS-77": 1997,
    "ARTHUR Counter-Battery": 1994,
    "AN/TPY-2 X-band AESA": 2004,
    "EL/M-2084 MMR AESA": 2008,
    "Giraffe AMB 3D": 2005,
    "91N6E Big Bird": 2007,
    "TRML-4D AESA": 2018,
    "SAMPSON AESA": 2008,
    "AN/SPY-6 AMDR AESA": 2020,
    "LTAMDS GaN AESA": 2023,
    "Sea Fire 500 AESA": 2021,
    "Ground Master 400 Alpha": 2021,
}

MAP_PROFILES: dict[str, MapProfile] = {
    "Coastal Plain": MapProfile("Coastal Plain", radar_range_mult=1.0, clutter=0.18, projectile_drag=0.004, ground_speed_mult=1.0, terrain_shadow=0.08, color="#0b3d3a", description="open approaches with mild sea clutter"),
    "Mountain Valley": MapProfile("Mountain Valley", radar_range_mult=0.82, clutter=0.45, projectile_drag=0.007, ground_speed_mult=0.74, terrain_shadow=0.35, color="#20351f", description="terrain masking hurts low flyers"),
    "Urban Basin": MapProfile("Urban Basin", radar_range_mult=0.9, clutter=0.55, projectile_drag=0.005, ground_speed_mult=0.82, terrain_shadow=0.26, color="#1d2730", description="dense false returns and short sightlines"),
    "Desert Flats": MapProfile("Desert Flats", radar_range_mult=1.12, clutter=0.12, projectile_drag=0.003, ground_speed_mult=1.12, terrain_shadow=0.04, color="#3a2f20", description="long views with fast ground movement"),
    "Snow Plateau": MapProfile("Snow Plateau", radar_range_mult=0.96, clutter=0.28, projectile_drag=0.009, ground_speed_mult=0.68, terrain_shadow=0.14, color="#26343d", description="cold dense air slows projectiles"),
}

EW_ACTIONS: dict[str, EWActionProfile] = {
    "ECCM Sweep": EWActionProfile("ECCM Sweep", cost=26.0, duration=7.0, effect="eccm"),
    "Burn Through": EWActionProfile("Burn Through", cost=34.0, duration=5.0, effect="burn"),
    "Decoy Emitters": EWActionProfile("Decoy Emitters", cost=18.0, duration=8.0, effect="decoy"),
    "EMCON Silence": EWActionProfile("EMCON Silence", cost=12.0, duration=6.0, effect="silent"),
    "Directional Noise Gate": EWActionProfile("Directional Noise Gate", cost=30.0, duration=7.5, effect="directional"),
}

STORY_CALLS = (
    "HQ: Confirm line clear. Launch only cannons until we identify the tracks.",
    "HQ: EW reports noise on the scope. Use burn-through if the picture collapses.",
    "HQ: SEAD package inbound. Protect the radar from anti-radiation missiles.",
    "HQ: Civil plant nearby. Maintain radar coverage and avoid losing the site.",
)

RANDOM_EVENTS = (
    "Mortar Wave",
    "Drone Swarm",
    "SEAD Raid",
    "Ground Push",
    "Ghost Storm",
    "Radiological Alert",
)

PLANT_EVENTS = (
    "Grid Demand Surge",
    "Coolant Pump Trip",
    "Feedwater Drop",
    "Steam Valve Drift",
    "Control Rod Drift",
    "Turbine Vibration",
    "Training Inspection",
)

ENEMY_PROFILES: dict[str, EnemyProfile] = {
    "Scout UAV": EnemyProfile("Scout UAV", speed=34.0, launch_interval=5.2, health=1, score_value=35, color="#8ecae6", projectile_names=("Shahed-style Loiterer", "9M22U Grad Rocket"), platform="air", can_damage_base=False, standoff_radius=170.0, year=2010, decade="2010s"),
    "Bomber": EnemyProfile("Bomber", speed=24.0, launch_interval=6.5, health=2, score_value=70, color="#ffb703", projectile_names=("81mm Mortar Bomb", "155mm Artillery Shell"), platform="air", can_damage_base=False, standoff_radius=210.0, year=1942, decade="1940s"),
    "TEL Vehicle": EnemyProfile("TEL Vehicle", speed=16.0, launch_interval=8.0, health=3, score_value=115, color="#d4a373", projectile_names=("Iskander-style SRBM", "M31 GMLRS Rocket"), platform="ground", can_damage_base=True, standoff_radius=60.0, year=1998, decade="1990s"),
    "MLRS Battery": EnemyProfile("MLRS Battery", speed=13.0, launch_interval=4.4, health=2, score_value=80, color="#dda15e", projectile_names=("9M22U Grad Rocket", "M31 GMLRS Rocket"), platform="ground", can_damage_base=True, standoff_radius=65.0, year=1976, decade="1970s"),
    "Armored Column": EnemyProfile("Armored Column", speed=20.0, launch_interval=7.2, health=4, score_value=130, color="#606c38", projectile_names=("155mm Artillery Shell",), platform="ground", can_damage_base=True, standoff_radius=25.0, year=1965, decade="1960s"),
    "SEAD Aircraft": EnemyProfile("SEAD Aircraft", speed=38.0, launch_interval=5.7, health=2, score_value=125, color="#f72585", projectile_names=("AGM-88 HARM", "Kh-31P ARM"), platform="air", can_damage_base=False, standoff_radius=240.0, stealth_period=9.0, stealth_duration=2.7, year=1984, decade="1980s"),
    "Stealth UAV": EnemyProfile("Stealth UAV", speed=30.0, launch_interval=7.8, health=1, score_value=100, color="#ced4da", projectile_names=("Radiation Seeker", "Shahed-style Loiterer"), platform="air", can_damage_base=False, standoff_radius=190.0, stealth_period=7.0, stealth_duration=3.2, year=2020, decade="2020s+"),
    "Radar Jammer": EnemyProfile("Radar Jammer", speed=15.0, launch_interval=9.0, health=2, score_value=90, color="#ff70a6", projectile_names=("Shahed-style Loiterer",), platform="ground", can_damage_base=True, standoff_radius=120.0, jammer_radius=180.0, jammer_strength=0.9, ghost_rate=0.55, year=2015, decade="2010s"),
    "EW Aircraft": EnemyProfile("EW Aircraft", speed=31.0, launch_interval=7.5, health=2, score_value=120, color="#b8f2e6", projectile_names=("Tomahawk-style Cruise", "Radiation Seeker"), platform="air", can_damage_base=False, standoff_radius=260.0, jammer_radius=230.0, jammer_strength=1.1, ghost_rate=0.8, stealth_period=10.0, stealth_duration=2.0, year=2006, decade="2000s"),
}

ENEMY_FAMILIES = (
    ("Recon UAV", "air", 32.0, 6.8, 1, 40, "#8ecae6", ("Shahed-style Loiterer",), False, 180.0, 6.0, 2.0, 0.2, 0.0, 0.0),
    ("Strike Aircraft", "air", 40.0, 6.0, 2, 115, "#ffb703", ("Tomahawk-style Cruise", "AGM-88 HARM"), False, 240.0, 9.0, 2.5, 0.8, 0.0, 0.0),
    ("Bomber Cell", "air", 23.0, 7.0, 3, 140, "#dda15e", ("155mm Artillery Shell", "Iskander-style SRBM"), False, 260.0, 0.0, 0.0, 1.1, 0.0, 0.0),
    ("TEL Platoon", "ground", 15.0, 8.5, 3, 120, "#d4a373", ("M31 GMLRS Rocket", "Iskander-style SRBM"), True, 55.0, 0.0, 0.0, 1.25, 0.0, 0.0),
    ("MLRS Troop", "ground", 14.0, 4.8, 2, 90, "#bc6c25", ("9M22U Grad Rocket", "M31 GMLRS Rocket"), True, 70.0, 0.0, 0.0, 1.35, 0.0, 0.0),
    ("Armored Probe", "ground", 20.0, 7.4, 4, 130, "#606c38", ("155mm Artillery Shell",), True, 28.0, 0.0, 0.0, 1.6, 0.0, 0.0),
    ("Stand-In Jammer", "air", 30.0, 7.2, 2, 130, "#b8f2e6", ("Radiation Seeker",), False, 250.0, 10.0, 2.5, 0.85, 210.0, 0.8),
    ("Ground Jammer", "ground", 13.0, 9.2, 2, 100, "#ff70a6", ("Shahed-style Loiterer",), True, 115.0, 0.0, 0.0, 1.5, 180.0, 0.65),
)

PUBLIC_STYLE_ENEMIES = (
    "Orlan", "Forpost", "Bayraktar", "Reaper", "Predator", "Hermes", "Heron", "Watchkeeper",
    "Mohajer", "Ababil", "Wing Loong", "CH-4", "Lancet Team", "Harop Cell", "Su-24", "Su-34",
    "F-16", "Tornado", "Gripen", "Mirage", "Tu-22", "H-6", "B-52", "TEL-1", "TEL-2",
    "Smerch Battery", "Uragan Battery", "Grad Battery", "M270 Battery", "HIMARS Cell", "TOS-1",
    "SPH Column", "Tank Company", "IFV Column", "EW Truck", "Krasukha-style", "Leer-style",
    "Divnomorye-style", "SEAD Package", "Jammer Drone", "Low Observable UAV",
)

AIRCRAFT_NAME_OVERRIDES = {
    "F-16": "F-16C Block 50",
    "Tornado": "Tornado IDS",
    "Gripen": "JAS 39C Gripen",
    "Mirage": "Mirage 2000D",
    "Su-24": "Su-24M Fencer",
    "Su-34": "Su-34 Fullback",
    "Tu-22": "Tu-22M3 Backfire",
    "H-6": "H-6K Badger",
    "B-52": "B-52H Stratofortress",
}

UAV_NAME_OVERRIDES = {
    "Orlan": "Orlan-10",
    "Forpost": "Forpost-R",
    "Bayraktar": "Bayraktar TB2",
    "Reaper": "MQ-9 Reaper",
    "Predator": "MQ-1 Predator",
    "Hermes": "Hermes 900",
    "Heron": "IAI Heron",
    "Watchkeeper": "Watchkeeper WK450",
    "Mohajer": "Mohajer-6",
    "Ababil": "Ababil-3",
    "Wing Loong": "Wing Loong II",
    "CH-4": "CH-4B",
    "Jammer Drone": "Stand-in Jammer UAV",
    "Low Observable UAV": "Low Observable UAV",
}

GROUND_NAME_OVERRIDES = {
    "TEL-1": "8x8 TEL Section",
    "TEL-2": "Tracked TEL Section",
    "Smerch Battery": "BM-30 Smerch Battery",
    "Uragan Battery": "BM-27 Uragan Battery",
    "Grad Battery": "BM-21 Grad Battery",
    "M270 Battery": "M270 MLRS Battery",
    "HIMARS Cell": "M142 HIMARS Cell",
    "TOS-1": "TOS-1A Battery",
    "SPH Column": "Self-Propelled Howitzer Column",
    "Tank Company": "Tank Company",
    "IFV Column": "IFV Column",
    "EW Truck": "EW Truck Section",
    "Krasukha-style": "Krasukha-style EW Vehicle",
    "Leer-style": "Leer-style EW Vehicle",
    "Divnomorye-style": "Divnomorye-style EW Vehicle",
}


def _variant_factor(index: int, base: float = 1.0, step: float = 0.035) -> float:
    return base + ((index % 7) - 3) * step


def _year_for_era(era: str, index: int) -> int:
    base = RADAR_ERA_YEARS.get(era, 2020)
    span = 5 if era == "WW2 1930s" else 10
    return base + index % span


def _radar_era_for_year(year: int) -> str:
    if year < 1940:
        return "WW2 1930s"
    if year < 1950:
        return "WW2 1940s"
    if year < 1960:
        return "Early Cold War 1950s"
    if year < 1970:
        return "Cold War 1960s"
    if year < 1980:
        return "Cold War 1970s"
    if year < 1990:
        return "Digital 1980s"
    if year < 2000:
        return "Post-Cold War 1990s"
    if year < 2010:
        return "Networked 2000s"
    if year < 2020:
        return "Modern 2010s"
    return "Modern 2020s"


def _decade_for_year(year: int) -> str:
    if year < 1940:
        return "1930s"
    if year >= 2020:
        return "2020s+"
    return f"{year // 10 * 10}s"


def _normalize_degrees(angle: float) -> float:
    return angle % 360.0


def _angle_delta_degrees(angle: float, reference: float) -> float:
    return ((angle - reference + 180.0) % 360.0) - 180.0


def _bearing_between(origin: Vector2, target: Vector2) -> float:
    delta = target - origin
    if delta.magnitude() == 0:
        return 0.0
    return _normalize_degrees(degrees(atan2(delta.y, delta.x)))


def _cone_factor(origin: Vector2, bearing_degrees: float, target: Vector2, max_range: float, width_degrees: float) -> float:
    distance = origin.distance_to(target)
    if distance > max_range or max_range <= 0:
        return 0.0
    target_bearing = _bearing_between(origin, target)
    angle_error = abs(_angle_delta_degrees(target_bearing, bearing_degrees))
    if angle_error > width_degrees / 2.0:
        return 0.0
    range_factor = 1.0 - distance / max_range
    angle_factor = 1.0 - angle_error / max(width_degrees / 2.0, 1.0)
    return max(0.0, min(1.0, 0.35 + range_factor * 0.35 + angle_factor * 0.30))


def _year_for_decade_label(decade: str, offset: int = 0) -> int:
    if decade == "1930s":
        return 1935 + offset % 5
    if decade == "2020s+":
        return min(2026, 2020 + offset % 7)
    return int(decade[:4]) + offset % 10


PROJECTILE_LABEL_YEARS = {
    "RP-3": 1941,
    "V-1 Training": 1944,
    "Tiny Tim": 1944,
    "Honest John": 1953,
    "Little John": 1961,
    "Matador": 1952,
    "Regulus": 1955,
    "Scud": 1957,
    "FROG-7": 1965,
    "Grad": 1963,
    "S-8": 1984,
    "S-13": 1983,
    "S-25": 1975,
    "Maverick": 1972,
    "Paveway": 1968,
    "KAB Glide": 1975,
    "Kh-22": 1962,
    "Harpoon": 1977,
    "Exocet": 1975,
    "TOW-2B": 1987,
    "Kornet": 1998,
    "Javelin": 1996,
    "M26 MLRS": 1983,
    "M30A1": 2015,
    "M39 ATACMS": 1991,
    "ATACMS": 1991,
    "Tochka": 1975,
    "Uragan": 1975,
    "Smerch": 1987,
    "Kh-31": 1988,
    "Kh-58": 1982,
    "AGM-154": 1999,
    "HARM": 1984,
    "ALARM": 1990,
    "ARMAT": 1988,
    "Martel": 1970,
    "Brimstone": 2005,
    "Hellfire": 1984,
    "Spike NLOS": 1981,
    "Delilah": 1995,
    "LORA": 2003,
    "PrSM": 2023,
    "Storm Shadow": 2003,
    "SCALP": 2003,
    "JASSM": 2003,
    "Kalibr": 1994,
    "Kh-101": 2013,
    "NSM": 2012,
    "BrahMos": 2006,
    "Neptune": 2021,
    "Fateh": 2002,
    "Zelzal": 1990,
    "Qassam": 2001,
    "SDB": 2006,
    "JDAM-ER": 1997,
    "AASM": 2007,
    "Vikhr": 1985,
    "Lancet": 2019,
    "Switchblade": 2011,
    "Warmate": 2016,
    "Phoenix Ghost": 2022,
    "Harop": 2005,
    "Harpy": 1989,
    "Shahed": 2020,
    "Kinzhal": 2018,
    "Zircon": 2022,
    "YJ-12": 2015,
    "YJ-18": 2014,
    "C-802": 1989,
    "P-800": 2002,
    "RBS-15": 1985,
    "Gabriel": 1970,
    "Sea Venom": 2021,
    "Meteor Strike": 2016,
    "Spear": 2025,
    "Brave-1": 2023,
    "Vulcano": 2012,
    "Taurus KEPD": 2005,
    "Popeye": 1985,
    "SLAM-ER": 2000,
    "JSOW": 1999,
    "APKWS": 2012,
    "DAGR": 2012,
    "Hydra 70": 1948,
    "DF-15": 1989,
    "DF-21": 1991,
    "Fajr-5": 1991,
    "Nazeat": 1980,
    "Qiam": 2010,
    "Nimrod": 1989,
    "LAHAT": 1992,
    "Spike ER": 1997,
    "BONUS Shell": 2000,
    "SMArt 155": 1998,
    "M982 Excalibur": 2007,
    "Copperhead": 1980,
    "BGM-109": 1983,
    "GBU-39": 2006,
    "GBU-53": 2019,
    "GBU-24": 1983,
    "GBU-31": 1997,
    "GBU-38": 2004,
    "FAB Glide": 2023,
    "Hammer Glide": 2007,
    "SPEAR 3": 2025,
    "Rampage": 2018,
    "Rocks": 2019,
    "Blue Sparrow": 1996,
    "Silver Sparrow": 2013,
    "Black Sparrow": 2014,
    "Jericho Training": 1973,
    "Hyunmoo": 1986,
    "KTSSM": 2022,
    "Chunmoo": 2015,
}

PROJECTILE_FAMILY_MIN_YEARS = {
    "Light Rocket": 1940,
    "Guided Rocket": 1970,
    "Mortar Bomb": 1935,
    "Artillery Shell": 1935,
    "Guided Bomb": 1968,
    "Glide Bomb": 1944,
    "SRBM": 1953,
    "Cruise Missile": 1944,
    "Loitering Munition": 1989,
    "Anti-Radiation Missile": 1963,
    "Hypersonic Glide": 2018,
    "Sea-Skimmer": 1967,
}

PROJECTILE_LABEL_FAMILIES = {
    "ATACMS": "SRBM",
    "PrSM": "SRBM",
    "Tochka": "SRBM",
    "Scud": "SRBM",
    "Fateh": "SRBM",
    "Zelzal": "SRBM",
    "LORA": "SRBM",
    "Kinzhal": "Hypersonic Glide",
    "Zircon": "Hypersonic Glide",
    "DF-15": "SRBM",
    "DF-21": "SRBM",
    "Qiam": "SRBM",
    "Hyunmoo": "SRBM",
    "KTSSM": "SRBM",
    "Chunmoo": "Guided Rocket",
    "FROG-7": "Light Rocket",
    "Honest John": "Light Rocket",
    "Little John": "Light Rocket",
    "Jericho Training": "SRBM",
    "Blue Sparrow": "SRBM",
    "Silver Sparrow": "SRBM",
    "Black Sparrow": "SRBM",
    "Storm Shadow": "Cruise Missile",
    "SCALP": "Cruise Missile",
    "JASSM": "Cruise Missile",
    "Kalibr": "Cruise Missile",
    "Kh-101": "Cruise Missile",
    "BGM-109": "Cruise Missile",
    "Taurus KEPD": "Cruise Missile",
    "Popeye": "Cruise Missile",
    "SLAM-ER": "Cruise Missile",
    "Matador": "Cruise Missile",
    "Regulus": "Cruise Missile",
    "V-1 Training": "Cruise Missile",
    "Kh-22": "Sea-Skimmer",
    "Harpoon": "Sea-Skimmer",
    "NSM": "Sea-Skimmer",
    "Exocet": "Sea-Skimmer",
    "BrahMos": "Sea-Skimmer",
    "Neptune": "Sea-Skimmer",
    "YJ-12": "Sea-Skimmer",
    "YJ-18": "Sea-Skimmer",
    "C-802": "Sea-Skimmer",
    "P-800": "Sea-Skimmer",
    "RBS-15": "Sea-Skimmer",
    "Gabriel": "Sea-Skimmer",
    "Sea Venom": "Sea-Skimmer",
    "Grad": "Light Rocket",
    "Smerch": "Guided Rocket",
    "Uragan": "Light Rocket",
    "Qassam": "Light Rocket",
    "Fajr-5": "Light Rocket",
    "Hydra 70": "Light Rocket",
    "S-8": "Light Rocket",
    "S-13": "Light Rocket",
    "S-25": "Light Rocket",
    "M26 MLRS": "Light Rocket",
    "M30A1": "Guided Rocket",
    "APKWS": "Guided Rocket",
    "DAGR": "Guided Rocket",
    "Hellfire": "Guided Rocket",
    "Brimstone": "Guided Rocket",
    "Maverick": "Guided Rocket",
    "Spike NLOS": "Guided Rocket",
    "TOW-2B": "Guided Rocket",
    "Kornet": "Guided Rocket",
    "Javelin": "Guided Rocket",
    "Vikhr": "Guided Rocket",
    "LAHAT": "Guided Rocket",
    "Nimrod": "Guided Rocket",
    "KAB Glide": "Glide Bomb",
    "SDB": "Glide Bomb",
    "JDAM-ER": "Guided Bomb",
    "AASM": "Guided Bomb",
    "Paveway": "Guided Bomb",
    "JSOW": "Glide Bomb",
    "GBU-39": "Glide Bomb",
    "GBU-53": "Glide Bomb",
    "GBU-24": "Guided Bomb",
    "GBU-31": "Guided Bomb",
    "GBU-38": "Guided Bomb",
    "FAB Glide": "Glide Bomb",
    "Hammer Glide": "Glide Bomb",
    "SPEAR 3": "Guided Bomb",
    "Rampage": "Guided Bomb",
    "Rocks": "Guided Bomb",
    "BONUS Shell": "Artillery Shell",
    "SMArt 155": "Artillery Shell",
    "M982 Excalibur": "Artillery Shell",
    "Copperhead": "Artillery Shell",
    "Vulcano": "Artillery Shell",
    "HARM": "Anti-Radiation Missile",
    "ALARM": "Anti-Radiation Missile",
    "Martel": "Anti-Radiation Missile",
    "Kh-58": "Anti-Radiation Missile",
    "Kh-31": "Anti-Radiation Missile",
    "ARMAT": "Anti-Radiation Missile",
    "Lancet": "Loitering Munition",
    "Switchblade": "Loitering Munition",
    "Warmate": "Loitering Munition",
    "Phoenix Ghost": "Loitering Munition",
    "Harop": "Loitering Munition",
    "Harpy": "Loitering Munition",
    "Shahed": "Loitering Munition",
}

DEFENSE_LABEL_YEARS = {
    "Avenger": 1990,
    "Skyranger": 2018,
    "Skynex": 2021,
    "Mantis": 2011,
    "Phalanx": 1980,
    "Centurion": 2005,
    "Pantsir": 2012,
    "Tor": 1986,
    "Buk": 1980,
    "Osa": 1971,
    "Strela": 1968,
    "Tunguska": 1982,
    "NASAMS": 1998,
    "IRIS-T SLM": 2022,
    "Crotale": 1971,
    "MICA VL": 2010,
    "CAMM": 2018,
    "Sea Ceptor": 2018,
    "Barak": 1988,
    "David Sling": 2017,
    "Iron Dome": 2011,
    "Arrow": 2000,
    "Patriot": 1984,
    "THAAD": 2008,
    "SAMP/T": 2011,
    "Aegis": 1983,
    "SM-2": 1979,
    "SM-3": 2004,
    "SM-6": 2013,
    "RIM-7": 1976,
    "RIM-116": 1992,
    "HQ-9": 1997,
    "HQ-16": 2011,
    "Akash": 2009,
    "Spyder": 2005,
    "Rapier": 1971,
    "Roland": 1977,
    "Starstreak": 1997,
    "Martlet": 2021,
    "Mistral": 1988,
    "Stinger": 1981,
    "Grom": 1995,
    "Piorun": 2019,
    "RBS-70": 1977,
    "M61": 1959,
    "Gepard": 1976,
    "Vulcan": 1965,
    "Oerlikon": 1937,
    "Goalkeeper": 1980,
    "Iron Beam": 2025,
    "HELWS": 2020,
}

DEFENSE_FAMILY_MIN_YEARS = {
    "Gun Burst": 1937,
    "Autocannon": 1950,
    "SHORAD Missile": 1968,
    "MRAD Missile": 1971,
    "ABM Interceptor": 2000,
    "Area Defense": 1979,
    "Laser": 2020,
}

DEFENSE_LABEL_FAMILIES = {
    "M61": "Gun Burst",
    "Gepard": "Autocannon",
    "Vulcan": "Gun Burst",
    "Oerlikon": "Autocannon",
    "Goalkeeper": "Gun Burst",
    "Phalanx": "Gun Burst",
    "Centurion": "Gun Burst",
    "Skyranger": "Autocannon",
    "Skynex": "Autocannon",
    "Mantis": "Autocannon",
    "Iron Beam": "Laser",
    "HELWS": "Laser",
    "Arrow": "ABM Interceptor",
    "Patriot": "ABM Interceptor",
    "THAAD": "ABM Interceptor",
    "SM-3": "ABM Interceptor",
    "SAMP/T": "Area Defense",
    "Aegis": "Area Defense",
    "SM-2": "Area Defense",
    "SM-6": "Area Defense",
    "HQ-9": "Area Defense",
    "David Sling": "Area Defense",
    "Barak": "Area Defense",
    "NASAMS": "MRAD Missile",
    "IRIS-T SLM": "MRAD Missile",
    "Crotale": "MRAD Missile",
    "MICA VL": "MRAD Missile",
    "CAMM": "MRAD Missile",
    "Sea Ceptor": "MRAD Missile",
    "Buk": "MRAD Missile",
    "Tor": "SHORAD Missile",
    "Pantsir": "SHORAD Missile",
    "Osa": "SHORAD Missile",
    "Tunguska": "SHORAD Missile",
    "Avenger": "SHORAD Missile",
    "Strela": "SHORAD Missile",
    "Stinger": "SHORAD Missile",
    "Mistral": "SHORAD Missile",
    "Grom": "SHORAD Missile",
    "Piorun": "SHORAD Missile",
    "RBS-70": "SHORAD Missile",
    "Martlet": "SHORAD Missile",
    "Starstreak": "SHORAD Missile",
    "Rapier": "SHORAD Missile",
    "Roland": "SHORAD Missile",
    "RIM-7": "MRAD Missile",
    "RIM-116": "SHORAD Missile",
    "HQ-16": "MRAD Missile",
    "Akash": "MRAD Missile",
    "Spyder": "MRAD Missile",
    "Iron Dome": "SHORAD Missile",
}

ENEMY_LABEL_YEARS = {
    "Orlan": 2010,
    "Forpost": 2020,
    "Bayraktar": 2014,
    "Reaper": 2007,
    "Predator": 1995,
    "Hermes": 2009,
    "Heron": 2005,
    "Watchkeeper": 2014,
    "Mohajer": 2017,
    "Ababil": 2008,
    "Wing Loong": 2017,
    "CH-4": 2014,
    "Lancet Team": 2019,
    "Harop Cell": 2005,
    "Su-24": 1983,
    "Su-34": 2014,
    "F-16": 1991,
    "Tornado": 1979,
    "Gripen": 2003,
    "Mirage": 1995,
    "Tu-22": 1989,
    "H-6": 2009,
    "B-52": 1961,
    "TEL-1": 1960,
    "TEL-2": 1965,
    "Smerch Battery": 1987,
    "Uragan Battery": 1975,
    "Grad Battery": 1963,
    "M270 Battery": 1983,
    "HIMARS Cell": 2005,
    "TOS-1": 2001,
    "SPH Column": 1960,
    "Tank Company": 1940,
    "IFV Column": 1966,
    "EW Truck": 1970,
    "Krasukha-style": 2014,
    "Leer-style": 2015,
    "Divnomorye-style": 2018,
    "SEAD Package": 1980,
    "Jammer Drone": 2010,
    "Low Observable UAV": 2010,
}

ENEMY_FAMILY_MIN_YEARS = {
    "Recon UAV": 1980,
    "Strike Aircraft": 1939,
    "Bomber Cell": 1939,
    "TEL Platoon": 1953,
    "MLRS Troop": 1941,
    "Armored Probe": 1939,
    "Stand-In Jammer": 1965,
    "Ground Jammer": 1960,
}

ENEMY_LABEL_FAMILIES = {
    "Orlan": "Recon UAV",
    "Forpost": "Recon UAV",
    "Bayraktar": "Recon UAV",
    "Reaper": "Recon UAV",
    "Predator": "Recon UAV",
    "Hermes": "Recon UAV",
    "Heron": "Recon UAV",
    "Watchkeeper": "Recon UAV",
    "Mohajer": "Recon UAV",
    "Ababil": "Recon UAV",
    "Wing Loong": "Recon UAV",
    "CH-4": "Recon UAV",
    "Lancet Team": "Recon UAV",
    "Harop Cell": "Recon UAV",
    "Jammer Drone": "Stand-In Jammer",
    "Low Observable UAV": "Recon UAV",
    "Su-24": "Strike Aircraft",
    "Su-34": "Strike Aircraft",
    "F-16": "Strike Aircraft",
    "Tornado": "Strike Aircraft",
    "Gripen": "Strike Aircraft",
    "Mirage": "Strike Aircraft",
    "Tu-22": "Bomber Cell",
    "H-6": "Bomber Cell",
    "B-52": "Bomber Cell",
    "TEL-1": "TEL Platoon",
    "TEL-2": "TEL Platoon",
    "Smerch Battery": "MLRS Troop",
    "Uragan Battery": "MLRS Troop",
    "Grad Battery": "MLRS Troop",
    "M270 Battery": "MLRS Troop",
    "HIMARS Cell": "MLRS Troop",
    "TOS-1": "MLRS Troop",
    "SPH Column": "Armored Probe",
    "Tank Company": "Armored Probe",
    "IFV Column": "Armored Probe",
    "EW Truck": "Ground Jammer",
    "Krasukha-style": "Ground Jammer",
    "Leer-style": "Ground Jammer",
    "Divnomorye-style": "Ground Jammer",
    "SEAD Package": "Stand-In Jammer",
}

PROJECTILE_FAMILY_BY_NAME = {family[0]: family for family in PROJECTILE_FAMILIES}
DEFENSE_FAMILY_BY_NAME = {family[0]: family for family in DEFENSE_FAMILIES}
ENEMY_FAMILY_BY_NAME = {family[0]: family for family in ENEMY_FAMILIES}

EW_ACTION_MIN_YEARS = {
    "EMCON Silence": 1935,
    "Decoy Emitters": 1960,
    "ECCM Sweep": 1970,
    "Burn Through": 1980,
    "Directional Noise Gate": 1985,
}

PROFILE_BLOCK_YEAR_OFFSETS = {
    "": 0,
    "Extended Range": 4,
    "Low Observable": 15,
    "Terminal Seeker": 10,
    "Improved Fire-Control": 5,
    "Extended Magazine": 3,
    "Night Package": 0,
    "Heavy Package": 0,
    "EW Package": 8,
}


def _projectile_family_for_label(label: str, index: int) -> tuple[str, str, float, float, float, int, str]:
    family_name = PROJECTILE_LABEL_FAMILIES.get(label)
    if family_name is not None:
        return PROJECTILE_FAMILY_BY_NAME[family_name]
    return PROJECTILE_FAMILIES[index % len(PROJECTILE_FAMILIES)]


def _defense_family_for_label(label: str, index: int) -> tuple[str, str, float, float, int, int, float, str]:
    family_name = DEFENSE_LABEL_FAMILIES.get(label)
    if family_name is not None:
        return DEFENSE_FAMILY_BY_NAME[family_name]
    return DEFENSE_FAMILIES[index % len(DEFENSE_FAMILIES)]


def _enemy_family_for_label(
    label: str,
    index: int,
) -> tuple[str, str, float, float, int, int, str, tuple[str, ...], bool, float, float, float, float, float, float]:
    family_name = ENEMY_LABEL_FAMILIES.get(label)
    if family_name is not None:
        return ENEMY_FAMILY_BY_NAME[family_name]
    return ENEMY_FAMILIES[index % len(ENEMY_FAMILIES)]


RADAR_ARCHITECTURE_TAGS = {
    "Chain-era Early Warning": "early_warning",
    "WW2 Fire-Control Dish": "fire_control",
    "Height-Finder": "height_finder",
    "VHF Search": "vhf",
    "Pulse-Doppler Search": "pulse_doppler",
    "Counter-Battery Radar": "counter_battery",
    "Passive ESM Sensor": "passive",
    "PESA Engagement Radar": "pesa",
    "X-band ABM AESA": "abm_aesa",
    "Networked 3D AESA": "aesa_3d",
    "GaN AESA Multirole": "gan_aesa",
    "EASA Training Alias": "gan_aesa",
}

RADAR_ARCHITECTURE_MIN_YEARS = {
    "early_warning": 1935,
    "fire_control": 1940,
    "height_finder": 1950,
    "vhf": 1950,
    "pulse_doppler": 1970,
    "counter_battery": 1970,
    "passive": 1980,
    "pesa": 1975,
    "abm_aesa": 1990,
    "aesa_3d": 2000,
    "gan_aesa": 2010,
}


def _variant_year(base_year: int, block: str) -> int:
    year = base_year + PROFILE_BLOCK_YEAR_OFFSETS.get(block, 0)
    if block == "Low Observable":
        year = max(year, 1990)
    if block == "Terminal Seeker":
        year = max(year, 1980)
    if block == "Improved Fire-Control":
        year = max(year, 1960)
    if block == "EW Package":
        year = max(year, 1960)
    return min(2026, year)


def _projectile_catalog_year(label: str, family: str, block: str) -> int:
    base_year = max(PROJECTILE_LABEL_YEARS.get(label, 1970), PROJECTILE_FAMILY_MIN_YEARS.get(family, 1970))
    return _variant_year(base_year, block)


def _defense_catalog_year(label: str, family: str, block: str) -> int:
    base_year = max(DEFENSE_LABEL_YEARS.get(label, 1970), DEFENSE_FAMILY_MIN_YEARS.get(family, 1970))
    return _variant_year(base_year, block)


def _enemy_catalog_year(label: str, family: str, block: str) -> int:
    base_year = max(ENEMY_LABEL_YEARS.get(label, 1970), ENEMY_FAMILY_MIN_YEARS.get(family, 1970))
    return _variant_year(base_year, block)


def _radar_scan_pattern(sensor_type: str, category: str) -> str:
    text = f"{sensor_type} {category}".lower()
    if "aesa" in text or "easa" in text:
        return "aesa_multi_beam"
    if "pesa" in text:
        return "pesa_sector"
    if "pulse-doppler" in text or "doppler" in text:
        return "pulse_doppler"
    if "height" in text:
        return "height_finder"
    if "fixed early" in text:
        return "fixed_lobe"
    if "fire-control" in text or "guidance" in text or "illuminator" in text:
        return "narrow_fire_control"
    return "mechanical_sweep"


def _radar_hud_style(name: str, era: str, sensor_type: str, category: str) -> str:
    text = f"{name} {sensor_type} {category}".lower()
    if any(token in text for token in ("p-", "snr", "91n", "92n", "96l", "nebo", "gamma", "protivnik", "podlet", "vostok", "rezonans", "krasukha")):
        return "soviet_green"
    if any(token in text for token in ("jy-", "ylc", "type ", "hq-", "rajendra", "swordfish")):
        return "eastern_amber"
    if "ww2" in era.lower() or "chain" in text or "scr-" in text or "freya" in text or "wuerzburg" in text:
        return "early_analog"
    if "naval" in text or "spy-" in text or "sampson" in text or "sea fire" in text:
        return "naval_blue"
    if "aesa" in text or "easa" in text or "digital" in text or "networked" in era.lower():
        return "glass_tactical"
    return "western_ppi"


def _height_accuracy_for(sensor_type: str, category: str, precision: float) -> float:
    text = f"{sensor_type} {category}".lower()
    value = 0.55 + precision * 0.42
    if "height" in text or "3d" in text:
        value += 0.35
    if "aesa" in text or "easa" in text:
        value += 0.32
    if "pesa" in text:
        value += 0.18
    if "fixed early" in text or "2d" in text:
        value -= 0.26
    return max(0.25, value)


def _elevation_coverage_for(sensor_type: str, category: str) -> float:
    text = f"{sensor_type} {category}".lower()
    if "fixed early" in text:
        return 24.0
    if "height" in text:
        return 72.0
    if "fire-control" in text or "guidance" in text:
        return 62.0
    if "aesa" in text or "easa" in text:
        return 82.0
    if "pesa" in text:
        return 68.0
    return 48.0


def _beam_width_for(sensor_type: str, band: str, precision: float) -> float:
    text = f"{sensor_type} {band}".lower()
    width = 4.4 / max(0.45, precision)
    if "vhf" in text or "hf" in text:
        width *= 1.55
    if "j-band" in text or "x-band" in text or "x/" in text:
        width *= 0.72
    if "aesa" in text or "easa" in text:
        width *= 0.58
    elif "pesa" in text:
        width *= 0.76
    return max(0.35, width)


def _projectile_display_name(label: str, family: str, block: str) -> str:
    fit = f" {block}" if block else ""
    return f"{label} {family}{fit}"


def _defense_display_name(label: str, family: str, block: str) -> str:
    fit = f" {block}" if block else ""
    return f"{label} {family}{fit}"


def _defense_compatibility_tokens(label: str, family: str, category: str) -> tuple[str, ...]:
    if category == "gun":
        return (label, "fire-control", "counter-battery", "tracking")
    if category == "directed-energy":
        return (label, "AESA", "digital", "glass", "LTAMDS")
    if "ABM" in family or label in {"Patriot", "THAAD", "Arrow", "SM-3"}:
        return (label, "ballistic-defense", "PESA", "AESA", "AN/TPY", "LTAMDS")
    if label in {"NASAMS", "IRIS-T SLM", "Crotale", "MICA VL", "CAMM", "Sea Ceptor"}:
        return (label, "3D", "Sentinel", "AN/MPQ-64", "AESA")
    return (label, "engagement", "fire-control", "3D", "PESA", "AESA")


def _enemy_display_name(label: str, family: str, block: str, platform: str) -> str:
    fit = f" {block}" if block else ""
    if label in AIRCRAFT_NAME_OVERRIDES:
        if "Jammer" in family or "SEAD" in label:
            mission = "SEAD Flight"
        elif "Bomber" in family:
            mission = "Bomber Flight"
        else:
            mission = "Strike Flight"
        return f"{AIRCRAFT_NAME_OVERRIDES[label]} {mission}{fit}"
    if label in UAV_NAME_OVERRIDES:
        mission = "EW UAV" if "Jammer" in label or "Jammer" in family else "Recon UAV"
        return f"{UAV_NAME_OVERRIDES[label]} {mission}{fit}"
    if label in GROUND_NAME_OVERRIDES:
        role = "Assault Group" if platform == "ground" and "Armored" in family else family
        return f"{GROUND_NAME_OVERRIDES[label]} {role}{fit}"
    if "Package" in label:
        return f"{label}{fit}"
    return f"{label} {family}{fit}"


def _make_radar_profile(
    name: str,
    *,
    era: str,
    sensor_type: str,
    band: str,
    category: str,
    radar_range: float,
    noise: float,
    ew_power: float,
    ew_regen: float,
    terrain: float,
    health: int,
    cost: int,
    color: str,
    abilities: tuple[str, ...],
    pros: tuple[str, ...],
    cons: tuple[str, ...],
    scan_rate: float,
    low_altitude: float,
    stealth: float,
    jamming: float,
    precision: float,
    index: int,
    year_override: int | None = None,
) -> RadarProfile:
    year = year_override if year_override is not None else _year_for_era(era, index)
    scan_pattern = _radar_scan_pattern(sensor_type, category)
    hud_style = _radar_hud_style(name, era, sensor_type, category)
    return RadarProfile(
        name,
        range=radar_range,
        noise=noise,
        ew_power=ew_power,
        ew_regen=ew_regen,
        terrain_resistance=terrain,
        health=health,
        cost=cost,
        color=color,
        abilities=abilities,
        era=era,
        sensor_type=sensor_type,
        band=band,
        category=category,
        pros=pros,
        cons=cons,
        scan_rate=scan_rate,
        low_altitude_factor=low_altitude,
        stealth_detection=stealth,
        jamming_resistance=jamming,
        tracking_precision=precision,
        year=year,
        decade=_decade_for_year(year),
        antenna_type=sensor_type,
        scan_pattern=scan_pattern,
        hud_style=hud_style,
        height_accuracy=_height_accuracy_for(sensor_type, category, precision),
        elevation_coverage=_elevation_coverage_for(sensor_type, category),
        beam_width=_beam_width_for(sensor_type, band, precision),
    )


def _radar_behavior_for(sensor_type: str, band: str, category: str) -> tuple[float, float, float, float, float]:
    text = f"{sensor_type} {band} {category}".lower()
    scan_rate = 1.0
    low_altitude = 1.0
    stealth = 0.16
    jamming = 0.18
    precision = 1.0

    if "fixed early" in text or "ww2" in text:
        scan_rate -= 0.34
        low_altitude -= 0.26
        precision -= 0.20
    if "height" in text:
        low_altitude -= 0.10
        precision += 0.06
    if "fire-control" in text or "engagement" in text or "guidance" in text:
        scan_rate += 0.16
        precision += 0.24
    if "pulse-doppler" in text or "mti" in text:
        low_altitude += 0.18
        jamming += 0.10
    if "pesa" in text:
        scan_rate += 0.32
        jamming += 0.20
        precision += 0.22
    if "aesa" in text or "easa" in text:
        scan_rate += 0.56
        low_altitude += 0.24
        stealth += 0.20
        jamming += 0.36
        precision += 0.38
    if "gan" in text or "digital" in text:
        scan_rate += 0.16
        jamming += 0.14
        precision += 0.12
    if "vhf" in text or "hf" in text:
        stealth += 0.24
        precision -= 0.16
        low_altitude -= 0.08
    if "j-band" in text or "x/" in text or "x-band" in text:
        precision += 0.18
        stealth -= 0.04
    if "counter-battery" in text:
        precision += 0.18
        scan_rate += 0.10
    if "passive" in text:
        stealth += 0.14
        jamming += 0.24
        scan_rate -= 0.12

    return (
        max(0.38, scan_rate),
        max(0.35, low_altitude),
        max(0.02, stealth),
        max(0.02, jamming),
        max(0.42, precision),
    )


def _install_historical_radars() -> None:
    for index, (
        name,
        era,
        sensor_type,
        band,
        category,
        radar_range,
        noise,
        ew_power,
        ew_regen,
        terrain,
        health,
        color,
    ) in enumerate(HISTORICAL_RADAR_ROSTER):
        scan_rate, low_altitude, stealth, jamming, precision = _radar_behavior_for(sensor_type, band, category)
        RADAR_PROFILES[name] = _make_radar_profile(
            name,
            era=era,
            sensor_type=sensor_type,
            band=band,
            category=category,
            radar_range=radar_range,
            noise=noise,
            ew_power=ew_power,
            ew_regen=ew_regen,
            terrain=terrain,
            health=health,
            cost=65 + index * 8,
            color=color,
            abilities=(category, sensor_type, band),
            pros=(f"{era} operator flavor", f"{category} role"),
            cons=("fictional balance stats", "not real tactical data"),
            scan_rate=scan_rate,
            low_altitude=low_altitude,
            stealth=stealth,
            jamming=jamming,
            precision=precision,
            index=index,
            year_override=HISTORICAL_RADAR_YEARS.get(name),
        )


def _extend_projectile_profiles() -> None:
    for index, label in enumerate(PUBLIC_STYLE_PROJECTILES):
        family, role, speed, turn, rcs, damage, color = _projectile_family_for_label(label, index)
        for block_index, (block, block_speed, cost_bonus) in enumerate(PROFILE_BLOCKS):
            name = _projectile_display_name(label, family, block)
            if name in PROJECTILE_PROFILES:
                continue
            variant_index = index * len(PROFILE_BLOCKS) + block_index
            year = _projectile_catalog_year(label, family, block)
            terrain_following = role in {"cruise", "drone"} or "Skimmer" in family
            radar_seeking = role == "anti-radiation" or "HARM" in label or "Kh-31" in label or "Kh-58" in label
            PROJECTILE_PROFILES[name] = ProjectileProfile(
                name,
                speed * block_speed * _variant_factor(variant_index, 1.0, 0.04),
                max(0.03, turn * _variant_factor(variant_index + 2, 1.0, 0.05)),
                max(0.22, rcs * _variant_factor(variant_index + 4, 1.0, 0.06)),
                color,
                damage=damage + (1 if variant_index % 11 == 0 else 0),
                score_value=18 + variant_index % 90,
                cost=16 + cost_bonus + (variant_index % 14) * 5,
                ammo=max(1, 12 - (variant_index % 9)),
                role=role,
                terrain_following=terrain_following,
                radar_seeking=radar_seeking,
                acceleration=8.0 + (variant_index % 5) * 4.0 if role in {"rocket", "anti-radiation", "ballistic"} else 1.5 if role == "bomb" else 2.0,
                max_speed=speed * block_speed * _variant_factor(variant_index, 1.32, 0.04),
                altitude_profile="terrain-following" if terrain_following else role,
                cruise_altitude=180.0 + (variant_index % 9) * 220.0 if terrain_following else 700.0 + (variant_index % 11) * 260.0,
                ballistic_apogee=2200.0 + (variant_index % 10) * 520.0,
                year=year,
                decade=_decade_for_year(year),
            )


def _extend_defense_profiles() -> None:
    for index, label in enumerate(PUBLIC_STYLE_DEFENSES):
        family, category, speed, radius, ammo, cost, power, color = _defense_family_for_label(label, index)
        for block_index, (block, block_speed, cost_bonus) in enumerate(DEFENSE_BLOCKS):
            name = _defense_display_name(label, family, block)
            if name in INTERCEPTOR_PROFILES:
                continue
            variant_index = index * len(DEFENSE_BLOCKS) + block_index
            year = _defense_catalog_year(label, family, block)
            INTERCEPTOR_PROFILES[name] = InterceptorProfile(
                name,
                speed * block_speed * _variant_factor(variant_index + 1, 1.0, 0.035),
                max(5.0, radius * _variant_factor(variant_index + 3, 1.0, 0.04)),
                color,
                ammo=max(2, ammo - (variant_index % 6)),
                cost=cost + cost_bonus + (variant_index % 10) * 3,
                power_cost=max(0.2, power * _variant_factor(variant_index + 5, 1.0, 0.08)),
                category=category,
                year=year,
                decade=_decade_for_year(year),
                compatible_radars=_defense_compatibility_tokens(label, family, category),
            )


def _extend_radar_profiles() -> None:
    for index, label in enumerate(PUBLIC_STYLE_RADARS):
        label_year = RADAR_LABEL_YEARS[label]
        allowed_tags = RADAR_LABEL_TAGS[label]
        for architecture_index, architecture in enumerate(RADAR_ARCHITECTURES):
            (
                family,
                era,
                sensor_type,
                band,
                category,
                radar_range,
                noise,
                ew_power,
                ew_regen,
                terrain,
                health,
                color,
                abilities,
                pros,
                cons,
                base_scan,
                base_low_altitude,
                base_stealth,
                base_jamming,
                base_precision,
            ) = architecture
            architecture_tag = RADAR_ARCHITECTURE_TAGS[family]
            if architecture_tag not in allowed_tags:
                continue
            architecture_year = RADAR_ARCHITECTURE_MIN_YEARS[architecture_tag]
            for block_index, (block, year_offset, block_factor) in enumerate(RADAR_VARIANT_BLOCKS):
                year = max(label_year, architecture_year) + year_offset
                if year > 2026:
                    continue
                era_for_year = _radar_era_for_year(year)
                variant_index = ((index * len(RADAR_ARCHITECTURES)) + architecture_index) * len(RADAR_VARIANT_BLOCKS) + block_index
                suffix = f" {block}" if block else ""
                name = f"{label} {family}{suffix}"
                if name in RADAR_PROFILES:
                    continue
                RADAR_PROFILES[name] = _make_radar_profile(
                    name,
                    era=era_for_year,
                    sensor_type=sensor_type,
                    band=band,
                    category=category,
                    radar_range=radar_range * block_factor * _variant_factor(variant_index + 2, 1.0, 0.04),
                    noise=max(0.42, noise * _variant_factor(variant_index + 4, 1.0, 0.05) / block_factor),
                    ew_power=ew_power * block_factor * _variant_factor(variant_index + 1, 1.0, 0.045),
                    ew_regen=max(1.5, ew_regen * _variant_factor(variant_index + 3, 1.0, 0.04)),
                    terrain=min(0.90, max(0.12, terrain * _variant_factor(variant_index + 5, 1.0, 0.05))),
                    health=health + (variant_index % 3),
                    cost=70 + RADAR_ERA_ORDER.index(era_for_year) * 28 + (index % 6) * 11 + block_index * 12,
                    color=color,
                    abilities=abilities + (f"{year} catalog",),
                    pros=pros,
                    cons=cons,
                    scan_rate=max(0.35, base_scan * block_factor * _variant_factor(variant_index + 1, 1.0, 0.035)),
                    low_altitude=max(0.35, base_low_altitude * _variant_factor(variant_index + 2, 1.0, 0.035)),
                    stealth=max(0.02, base_stealth * _variant_factor(variant_index + 3, 1.0, 0.04)),
                    jamming=max(0.02, base_jamming * block_factor * _variant_factor(variant_index + 4, 1.0, 0.04)),
                    precision=max(0.42, base_precision * block_factor * _variant_factor(variant_index + 5, 1.0, 0.035)),
                    index=variant_index,
                    year_override=year,
                )


def _extend_enemy_profiles() -> None:
    for index, label in enumerate(PUBLIC_STYLE_ENEMIES):
        (
            family,
            platform,
            speed,
            interval,
            health,
            score,
            color,
            projectile_names,
            can_damage,
            standoff,
            stealth_period,
            stealth_duration,
            signature,
            jammer_radius,
            jammer_strength,
        ) = _enemy_family_for_label(label, index)
        for block_index, (block, block_speed, score_bonus) in enumerate(ENEMY_BLOCKS):
            year = _enemy_catalog_year(label, family, block)
            if block == "EW Package" and year < 1960:
                continue
            if block == "Night Package" and year < 1940:
                year = 1940
            if jammer_strength > 0 and year < 1960:
                year = 1960
            name = _enemy_display_name(label, family, block, platform)
            if name in ENEMY_PROFILES:
                continue
            variant_index = index * len(ENEMY_BLOCKS) + block_index
            variant_jammer = jammer_strength + (0.22 if block == "EW Package" else 0.0)
            ENEMY_PROFILES[name] = EnemyProfile(
                name,
                speed * block_speed * _variant_factor(variant_index + 1, 1.0, 0.04),
                max(2.5, interval * _variant_factor(variant_index + 2, 1.0, 0.045)),
                health + (1 if variant_index % 13 == 0 or block == "Heavy Package" else 0),
                score + score_bonus + variant_index % 60,
                color,
                projectile_names=projectile_names,
                platform=platform,
                can_damage_base=can_damage,
                standoff_radius=standoff * _variant_factor(variant_index + 3, 1.0, 0.035),
                stealth_period=stealth_period + (1.5 if block == "Night Package" else 0.0),
                stealth_duration=stealth_duration + (0.6 if block == "Night Package" else 0.0),
                signature=max(0.18, signature * _variant_factor(variant_index + 4, 1.0, 0.06) * (0.86 if block == "Night Package" else 1.0)),
                jammer_radius=jammer_radius + (30.0 if block == "EW Package" and variant_jammer else 0.0),
                jammer_strength=variant_jammer,
                ghost_rate=0.45 + (0.12 if block == "EW Package" else 0.0) if variant_jammer else 0.0,
                altitude=0.0 if platform == "ground" else 500.0 + (variant_index % 9) * 320.0 + (600.0 if "Bomber" in family else 0.0),
                year=year,
                decade=_decade_for_year(year),
            )


def _sort_catalogs() -> None:
    global PROJECTILE_PROFILES, INTERCEPTOR_PROFILES, RADAR_PROFILES, ENEMY_PROFILES
    PROJECTILE_PROFILES = dict(sorted(PROJECTILE_PROFILES.items(), key=lambda item: (item[1].year, item[1].role, item[0])))
    INTERCEPTOR_PROFILES = dict(sorted(INTERCEPTOR_PROFILES.items(), key=lambda item: (item[1].year, item[1].category, item[0])))
    RADAR_PROFILES = dict(
        sorted(
            RADAR_PROFILES.items(),
            key=lambda item: (
                item[1].year,
                item[1].decade,
                item[1].category,
                item[1].sensor_type,
                item[0],
            ),
        )
    )
    ENEMY_PROFILES = dict(sorted(ENEMY_PROFILES.items(), key=lambda item: (item[1].year, item[1].platform, item[0])))


def extend_catalogs() -> None:
    _install_historical_radars()
    _extend_projectile_profiles()
    _extend_defense_profiles()
    _extend_radar_profiles()
    _extend_enemy_profiles()
    _sort_catalogs()


extend_catalogs()


INTERCEPTOR_PROFILES.update(
    {
        "LRAD Sonic Disruptor": InterceptorProfile(
            "LRAD Sonic Disruptor",
            220.0,
            42.0,
            "#8ecae6",
            ammo=9,
            cost=18,
            power_cost=3.0,
            category="sonic",
            year=2004,
            decade="2000s",
            compatible_radars=("3D", "AESA", "digital", "Sentinel"),
        ),
        "Parametric Sonic Array": InterceptorProfile(
            "Parametric Sonic Array",
            310.0,
            26.0,
            "#bde0fe",
            ammo=7,
            cost=26,
            power_cost=4.6,
            category="sonic",
            year=2016,
            decade="2010s",
            compatible_radars=("AESA", "digital", "LTAMDS", "tracking"),
        ),
        "Counter-UAS Sonic Fence": InterceptorProfile(
            "Counter-UAS Sonic Fence",
            170.0,
            66.0,
            "#caf0f8",
            ammo=12,
            cost=14,
            power_cost=2.2,
            category="sonic",
            year=2023,
            decade="2020s+",
            compatible_radars=("AESA", "digital", "Sentinel", "Giraffe"),
        ),
    }
)
_sort_catalogs()


@dataclass(slots=True)
class DirectionalEffect:
    kind: str
    origin: Vector2
    bearing_degrees: float
    range: float
    width_degrees: float
    until: float
    strength: float
    color: str
    label: str


@dataclass(slots=True)
class HostileRadarSite:
    site_id: int
    profile: RadarProfile
    position: Vector2
    health: int
    bearing_degrees: float = 0.0
    auto_scan: bool = True
    active: bool = True
    jammed_until: float = 0.0
    last_fix_report_at: float = 0.0


@dataclass(slots=True)
class EnemyTrack:
    enemy_id: int
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
    target_role: str = "air"
    revealed: bool = False
    jamming: float = 0.0

    def predict(self, timestamp: float) -> Vector2:
        dt = max(0.0, timestamp - self.last_timestamp)
        return self.position + self.velocity * dt

    def predict_altitude(self, timestamp: float) -> float:
        dt = max(0.0, timestamp - self.last_timestamp)
        return max(0.0, self.altitude + self.vertical_velocity * dt)


@dataclass(slots=True)
class SimulationWorld:
    radar_radius: float = 480.0
    base_position: Vector2 = Vector2(0.0, 0.0)
    interceptor_speed: float = INTERCEPTOR_PROFILES["Iron Dome Tamir"].speed
    rng: Random = field(default_factory=lambda: Random(7))
    tracker: RadarTracker = field(default_factory=lambda: RadarTracker(stale_after=8.0))
    projectiles: dict[int, Projectile] = field(default_factory=dict)
    interceptors: dict[int, Interceptor] = field(default_factory=dict)
    enemies: dict[int, Enemy] = field(default_factory=dict)
    enemy_tracks: dict[int, EnemyTrack] = field(default_factory=dict)
    radar_sites: dict[int, RadarSite] = field(default_factory=dict)
    hostile_radar_sites: dict[int, HostileRadarSite] = field(default_factory=dict)
    field_effects: list[DirectionalEffect] = field(default_factory=list)
    time: float = 0.0
    score: int = 0
    base_health: int = 10
    budget_points: int = 0
    game_mode: str = "sandbox"
    radar_profile_name: str = "AN/MPQ-64 Sentinel"
    map_profile_name: str = "Coastal Plain"
    radar_bearing_degrees: float = 90.0
    radar_manual_aim: bool = False
    radar_health: int = 6
    ew_power: float = 80.0
    wave_number: int = 0
    next_wave_at: float = 0.0
    next_auto_interceptor_at: float = 0.0
    next_random_event_at: float = 12.0
    story_stage: int = 0
    pending_hq_call: str | None = None
    hq_orders_completed: int = 0
    radiological_until: float = 0.0
    radar_stuck_until: float = 0.0
    radar_stuck_pending_break: bool = False
    radar_repair_needed: bool = False
    radar_repair_sequence: tuple[str, ...] = ()
    radar_repair_index: int = 0
    next_radar_fault_check_at: float = 5.0
    player_projectile_id: int | None = None
    player_projectile_profile_name: str = "9M22U Grad Rocket"
    player_control: Vector2 = ZERO
    eccm_until: float = 0.0
    burn_through_until: float = 0.0
    decoy_until: float = 0.0
    radar_silent_until: float = 0.0
    directional_ew_until: float = 0.0
    directional_ew_bearing_degrees: float = 90.0
    directional_ew_strength: float = 0.0
    next_ghost_at: float = 3.0
    ghost_track_ids: set[int] = field(default_factory=set)
    defense_inventory: dict[str, int] = field(default_factory=dict)
    projectile_inventory: dict[str, int] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    manual_aim_point: Vector2 | None = None
    reactor_power: float = 42.0
    reactor_temperature: float = 315.0
    coolant_level: float = 82.0
    turbine_load: float = 50.0
    control_rod_position: float = 55.0
    containment_integrity: float = 100.0
    pumps_online: bool = True
    pump_a_online: bool = True
    pump_b_online: bool = True
    steam_pressure: float = 55.0
    generator_output: float = 42.0
    grid_demand: float = 50.0
    feedwater_flow: float = 82.0
    turbine_vibration: float = 12.0
    plant_alarm: bool = False
    plant_blackout: bool = False
    next_plant_event_at: float = 16.0
    plant_message: str = "Plant simulator ready"
    _projectile_ids: count = field(default_factory=lambda: count(1))
    _interceptor_ids: count = field(default_factory=lambda: count(1))
    _enemy_ids: count = field(default_factory=lambda: count(1))
    _radar_site_ids: count = field(default_factory=lambda: count(1))
    _hostile_radar_site_ids: count = field(default_factory=lambda: count(1))
    _ghost_ids: count = field(default_factory=lambda: count(-1, -1))

    def __post_init__(self) -> None:
        radar = self.current_radar
        self.radar_health = radar.health
        self.ew_power = radar.ew_power
        self.reset_inventory()

    @property
    def current_radar(self) -> RadarProfile:
        return RADAR_PROFILES[self.radar_profile_name]

    @property
    def current_map(self) -> MapProfile:
        return MAP_PROFILES[self.map_profile_name]

    @property
    def radar_destroyable(self) -> bool:
        return self.game_mode in {"budget_waves", "ground_assault", "linked_defense"}

    @property
    def radar_alive(self) -> bool:
        return any(True for _profile, _position, _health, _bearing in self._active_radar_sources())

    @property
    def primary_radar_online(self) -> bool:
        return self.radar_health > 0 and not self.radar_repair_needed and self.time >= self.radar_stuck_until

    @property
    def is_eccm_active(self) -> bool:
        return self.time < self.eccm_until

    @property
    def is_burn_through_active(self) -> bool:
        return self.time < self.burn_through_until

    @property
    def is_decoy_active(self) -> bool:
        return self.time < self.decoy_until

    @property
    def is_radar_silent(self) -> bool:
        return self.time < self.radar_silent_until

    @property
    def is_directional_ew_active(self) -> bool:
        return self.time < self.directional_ew_until

    def radar_fov_degrees(self, radar: RadarProfile) -> float:
        text = f"{radar.name} {radar.sensor_type} {radar.category} {radar.scan_pattern}".lower()
        if "passive" in text:
            return 360.0
        if "counter-battery" in text or "weapon-locating" in text:
            return 96.0
        if radar.scan_pattern == "fixed_lobe":
            return 86.0
        if radar.scan_pattern == "height_finder":
            return 34.0
        if radar.scan_pattern == "narrow_fire_control":
            return 46.0
        if radar.scan_pattern == "pesa_sector":
            return 118.0
        if radar.scan_pattern == "aesa_multi_beam":
            if "ballistic" in radar.category.lower():
                return 92.0
            if "naval" in text:
                return 240.0
            return 168.0
        return 360.0

    def radar_fov_shape(self, radar: RadarProfile) -> str:
        text = f"{radar.name} {radar.sensor_type} {radar.category} {radar.scan_pattern}".lower()
        if "passive" in text:
            return "passive"
        if "counter-battery" in text or "weapon-locating" in text:
            return "counter_battery"
        if radar.scan_pattern == "fixed_lobe":
            return "fixed_lobe"
        if radar.scan_pattern == "height_finder":
            return "height_finder"
        if "naval" in text:
            return "naval"
        if radar.scan_pattern == "aesa_multi_beam":
            return "square"
        if radar.scan_pattern == "pesa_sector":
            return "sector"
        if radar.scan_pattern == "narrow_fire_control":
            return "narrow_sector"
        return "circle"

    def radar_requires_sweep_contact(self, radar: RadarProfile) -> bool:
        text = f"{radar.name} {radar.sensor_type} {radar.category} {radar.scan_pattern}".lower()
        if "passive" in text:
            return False
        if radar.scan_pattern in {"fixed_lobe", "height_finder", "narrow_fire_control", "pesa_sector", "aesa_multi_beam"}:
            return False
        return self.radar_fov_shape(radar) == "circle" or radar.scan_pattern in {"mechanical", "mechanical_sweep", "pulse_doppler"}

    def radar_sweep_beam_degrees(self, radar: RadarProfile) -> float:
        if not self.radar_requires_sweep_contact(radar):
            return self.radar_fov_degrees(radar)
        text = f"{radar.name} {radar.sensor_type} {radar.band} {radar.scan_pattern}".lower()
        beam = 10.0 + radar.beam_width * 1.6
        if "pulse_doppler" in text or "pulse-doppler" in text:
            beam += 4.0
        if "mechanical" in text or radar.scan_rate < 0.9:
            beam += 5.0
        if "early" in text or radar.year < 1960:
            beam += 4.0
        return max(8.0, min(34.0, beam))

    def radar_sweep_speed_degrees(self, radar: RadarProfile) -> float:
        speed = 16.0 + radar.scan_rate * 34.0
        if radar.scan_pattern == "pulse_doppler":
            speed += 8.0
        if self.radar_requires_sweep_contact(radar):
            speed += 4.0
        return max(12.0, min(96.0, speed))

    def radar_simultaneous_region_count(self, radar: RadarProfile) -> int:
        if radar.scan_pattern == "aesa_multi_beam":
            if "naval" in f"{radar.name} {radar.category}".lower():
                return 4
            return 3
        if radar.scan_pattern == "pesa_sector" and radar.tracking_precision >= 1.35:
            return 3
        return 1

    def radar_region_width_degrees(self, radar: RadarProfile) -> float:
        fov = self.radar_fov_degrees(radar)
        count = self.radar_simultaneous_region_count(radar)
        if count <= 1:
            return fov
        if radar.scan_pattern == "aesa_multi_beam":
            return max(30.0, min(58.0, fov / (count + 0.45)))
        return max(26.0, min(44.0, fov / (count + 0.65)))

    def radar_region_bearings(self, radar: RadarProfile, bearing_degrees: float) -> tuple[float, ...]:
        count = self.radar_simultaneous_region_count(radar)
        if count <= 1:
            return (_normalize_degrees(bearing_degrees),)
        fov = self.radar_fov_degrees(radar)
        if count == 3:
            offsets = (-fov * 0.34, 0.0, fov * 0.34)
        else:
            offsets = (-fov * 0.36, -fov * 0.12, fov * 0.12, fov * 0.36)
        return tuple(_normalize_degrees(bearing_degrees + offset) for offset in offsets)

    def radar_multiregion_covers_bearing(self, radar: RadarProfile, bearing_degrees: float, target_bearing: float) -> bool:
        width = self.radar_region_width_degrees(radar)
        return any(abs(_angle_delta_degrees(target_bearing, region_bearing)) <= width / 2.0 for region_bearing in self.radar_region_bearings(radar, bearing_degrees))

    def radar_track_mode(self, radar: RadarProfile, target_role: str = "unknown") -> str:
        text = f"{radar.name} {radar.sensor_type} {radar.category} {radar.scan_pattern}".lower()
        role = target_role.lower()
        if "passive" in text:
            return "bearing-only"
        if radar.scan_pattern == "height_finder":
            return "height-only"
        if radar.scan_pattern == "fixed_lobe":
            return "early-warning"
        if "counter-battery" in text or "weapon-locating" in text:
            return "weapon-locating" if role in {"ballistic", "rocket"} else "ballistic-only"
        if any(token in text for token in ("fire-control", "guidance", "illuminator", "engagement")):
            return "fire-control"
        if radar.scan_pattern in {"pesa_sector", "aesa_multi_beam"}:
            return "track-while-scan"
        if "3d" in text or "pulse" in text or "doppler" in text:
            return "surveillance-track"
        return "search-cue"

    def radar_track_engageable(self, radar: RadarProfile, target_role: str = "unknown") -> bool:
        mode = self.radar_track_mode(radar, target_role)
        if mode in {"bearing-only", "height-only", "early-warning", "ballistic-only", "search-cue"}:
            return False
        if mode == "weapon-locating":
            return target_role in {"ballistic", "rocket"}
        return True

    def radar_track_quality(self, radar: RadarProfile, target_role: str = "unknown") -> float:
        mode = self.radar_track_mode(radar, target_role)
        quality_by_mode = {
            "bearing-only": 0.24,
            "height-only": 0.28,
            "early-warning": 0.34,
            "search-cue": 0.42,
            "ballistic-only": 0.46,
            "surveillance-track": 0.66,
            "weapon-locating": 0.72,
            "track-while-scan": 0.82,
            "fire-control": 0.94,
        }
        return min(1.0, quality_by_mode.get(mode, 0.55) + max(0.0, radar.tracking_precision - 1.0) * 0.10)

    def _target_adjusted_radar_range(
        self,
        radar: RadarProfile,
        health: int,
        radar_position: Vector2,
        target_position: Vector2,
        *,
        radar_cross_section: float = 1.0,
        altitude: float = 1200.0,
        target_role: str = "unknown",
        terrain_following: bool = False,
        emitter: bool = False,
        include_jamming: bool = True,
    ) -> float:
        base_range = self._effective_radar_range(radar, health, self.current_map)
        text = f"{radar.name} {radar.sensor_type} {radar.band} {radar.category}".lower()
        role = target_role.lower()
        rcs_factor = min(1.32, max(0.38, 0.52 + radar_cross_section ** 0.45 * 0.34 + radar.stealth_detection * 0.24))

        if "passive" in text:
            passive_emitter_factor = 0.90 if emitter else 0.16
            terrain_mask = 1.0 - self.current_map.terrain_shadow * (0.36 if altitude < 400.0 else 0.14)
            return base_range * passive_emitter_factor * max(0.55, rcs_factor) * max(0.30, terrain_mask)

        low_altitude = max(0.0, 1.0 - min(1.0, altitude / 320.0))
        terrain_loss = self.current_map.terrain_shadow * low_altitude * max(0.12, 1.16 - radar.low_altitude_factor)
        clutter_loss = self.current_map.clutter * (0.32 if altitude < 550.0 else 0.14)
        altitude_bonus = 1.0 + min(0.18, max(0.0, altitude - 1200.0) / 16000.0)
        horizon_bonus = 1.0 + min(0.16, altitude / 9000.0)
        if altitude < 90.0:
            horizon_bonus -= 0.12

        band_bonus = 1.0
        if any(token in text for token in ("hf", "vhf", "uhf")):
            band_bonus += 0.12 if radar_cross_section < 0.72 else 0.02
            if altitude < 250.0:
                band_bonus -= 0.10
        if any(token in text for token in ("x/", "x-band", "j-band")):
            band_bonus += 0.08 if radar_cross_section >= 0.55 else -0.06
            if altitude < 180.0:
                band_bonus -= 0.08
        if "l-band" in text or "s-band" in text:
            band_bonus += 0.04

        role_bonus = 1.0
        if role == "ballistic" and radar.category in {"ballistic-defense", "counter-battery"}:
            role_bonus += 0.22
        if role in {"cruise", "drone"} or terrain_following:
            role_bonus -= max(0.04, 0.18 - radar.low_altitude_factor * 0.05)
        if role == "anti-radiation" and radar.scan_pattern in {"aesa_multi_beam", "pesa_sector", "narrow_fire_control"}:
            role_bonus += 0.08
        if role == "ground":
            role_bonus -= self.current_map.terrain_shadow * 0.20 + self.current_map.clutter * 0.08
            if "passive" in text:
                role_bonus -= 0.16
            if any(token in radar.category.lower() for token in ("3d", "surveillance", "engagement", "fire-control")):
                role_bonus += 0.05

        jamming = self.jamming_level_at(target_position) if include_jamming else 0.0
        jamming_loss = min(0.45, jamming * max(0.04, 0.22 - radar.jamming_resistance * 0.10))
        if emitter and radar.scan_pattern in {"aesa_multi_beam", "pesa_sector"}:
            jamming_loss *= 0.75
        directional_loss = self.directional_ew_level_at(target_position) * 0.52 if include_jamming else 0.0

        return max(25.0, base_range * rcs_factor * altitude_bonus * horizon_bonus * band_bonus * role_bonus * max(0.18, 1.0 - terrain_loss - clutter_loss - jamming_loss - directional_loss))

    def radar_source_covers_position(
        self,
        radar: RadarProfile,
        radar_position: Vector2,
        health: int,
        bearing_degrees: float,
        target_position: Vector2,
        *,
        radar_cross_section: float = 1.0,
        altitude: float = 1200.0,
        target_role: str = "unknown",
        terrain_following: bool = False,
        emitter: bool = False,
        include_jamming: bool = True,
    ) -> bool:
        effective_range = self._target_adjusted_radar_range(
            radar,
            health,
            radar_position,
            target_position,
            radar_cross_section=radar_cross_section,
            altitude=altitude,
            target_role=target_role,
            terrain_following=terrain_following,
            emitter=emitter,
            include_jamming=include_jamming,
        )
        delta = target_position - radar_position
        distance = delta.magnitude()
        if distance > effective_range:
            return False

        if self.radar_simultaneous_region_count(radar) > 1:
            target_bearing = _bearing_between(radar_position, target_position)
            return self.radar_multiregion_covers_bearing(radar, bearing_degrees, target_bearing)

        shape = self.radar_fov_shape(radar)
        if shape == "passive":
            return max(abs(delta.x), abs(delta.y)) <= effective_range * 0.74
        if shape == "square":
            bearing = bearing_degrees * pi / 180.0
            along = delta.x * cos(bearing) + delta.y * sin(bearing)
            cross = -delta.x * sin(bearing) + delta.y * cos(bearing)
            return -effective_range * 0.12 <= along <= effective_range and abs(cross) <= effective_range * 0.58

        fov = self.radar_fov_degrees(radar)
        if fov >= 359.0:
            return True
        target_bearing = _bearing_between(radar_position, target_position)
        return abs(_angle_delta_degrees(target_bearing, bearing_degrees)) <= fov / 2.0

    def radar_source_detects_position_now(
        self,
        radar: RadarProfile,
        radar_position: Vector2,
        health: int,
        bearing_degrees: float,
        target_position: Vector2,
        *,
        radar_cross_section: float = 1.0,
        altitude: float = 1200.0,
        target_role: str = "unknown",
        terrain_following: bool = False,
        emitter: bool = False,
        include_jamming: bool = True,
    ) -> bool:
        if not self.radar_source_covers_position(
            radar,
            radar_position,
            health,
            bearing_degrees,
            target_position,
            radar_cross_section=radar_cross_section,
            altitude=altitude,
            target_role=target_role,
            terrain_following=terrain_following,
            emitter=emitter,
            include_jamming=include_jamming,
        ):
            return False
        if not self.radar_requires_sweep_contact(radar):
            return True
        target_bearing = _bearing_between(radar_position, target_position)
        return abs(_angle_delta_degrees(target_bearing, bearing_degrees)) <= self.radar_sweep_beam_degrees(radar) / 2.0

    def reset_inventory(self) -> None:
        self.defense_inventory = {name: profile.ammo for name, profile in INTERCEPTOR_PROFILES.items()}
        self.projectile_inventory = {name: profile.ammo for name, profile in PROJECTILE_PROFILES.items()}

    def set_game_mode(self, mode: str, *, player_projectile_name: str | None = None) -> None:
        if mode not in GAME_MODES:
            raise ValueError(f"unknown game mode: {mode}")
        self.game_mode = mode
        self.clear_arena(reset_score=True)
        self.player_projectile_profile_name = player_projectile_name or self.player_projectile_profile_name
        if mode == "projectile":
            self.spawn_player_projectile(self.player_projectile_profile_name)
            self.next_auto_interceptor_at = self.time + 2.0
        elif mode in {"waves", "budget_waves", "ground_assault", "linked_defense"}:
            self.next_wave_at = self.time + 1.0
        elif mode == "story":
            self.next_wave_at = self.time + 4.0
            self.next_random_event_at = self.time + 10.0
            self.pending_hq_call = STORY_CALLS[0]
        elif mode == "nuclear_plant":
            self.next_plant_event_at = self.time + 14.0
            self.plant_message = "Plant board online. Hold output near grid demand."
        if mode == "budget_waves":
            self.budget_points = 450
        elif mode == "ground_assault":
            self.budget_points = 300
        elif mode == "linked_defense":
            self.budget_points = 250
        self.events.append(f"Mode set to {mode}")

    def clear_arena(self, *, reset_score: bool = False) -> None:
        self.projectiles.clear()
        self.interceptors.clear()
        self.enemies.clear()
        self.enemy_tracks.clear()
        self.radar_sites.clear()
        self.hostile_radar_sites.clear()
        self.field_effects.clear()
        self.tracker = RadarTracker(stale_after=8.0)
        self.ghost_track_ids.clear()
        self.player_projectile_id = None
        self.player_control = ZERO
        self.wave_number = 0
        self.next_wave_at = self.time + 1.0
        self.next_auto_interceptor_at = self.time + 2.0
        self.next_ghost_at = self.time + 3.0
        self.next_random_event_at = self.time + 12.0
        self.story_stage = 0
        self.pending_hq_call = None
        self.hq_orders_completed = 0
        self.radiological_until = 0.0
        self.radar_stuck_until = 0.0
        self.radar_stuck_pending_break = False
        self.radar_repair_needed = False
        self.radar_repair_sequence = ()
        self.radar_repair_index = 0
        self.next_radar_fault_check_at = self.time + 5.0
        self.manual_aim_point = None
        self.eccm_until = 0.0
        self.burn_through_until = 0.0
        self.decoy_until = 0.0
        self.radar_silent_until = 0.0
        self.directional_ew_until = 0.0
        self.directional_ew_strength = 0.0
        radar = self.current_radar
        self.radar_health = radar.health
        self.ew_power = radar.ew_power
        self.reset_inventory()
        self._reset_plant()
        if reset_score:
            self.score = 0
            self.base_health = 10
            self.budget_points = 0

    def _reset_plant(self) -> None:
        self.reactor_power = 42.0
        self.reactor_temperature = 315.0
        self.coolant_level = 82.0
        self.turbine_load = 50.0
        self.control_rod_position = 55.0
        self.containment_integrity = 100.0
        self.pumps_online = True
        self.pump_a_online = True
        self.pump_b_online = True
        self.steam_pressure = 55.0
        self.generator_output = 42.0
        self.grid_demand = 50.0
        self.feedwater_flow = 82.0
        self.turbine_vibration = 12.0
        self.plant_alarm = False
        self.plant_blackout = False
        self.next_plant_event_at = self.time + 16.0
        self.plant_message = "Plant simulator ready"

    def set_radar_profile(self, profile_name: str) -> bool:
        profile = RADAR_PROFILES[profile_name]
        if self.game_mode in {"budget_waves", "linked_defense"} and self.budget_points < profile.cost:
            self.events.append(f"Need {profile.cost} points for {profile.name}")
            return False
        if self.game_mode in {"budget_waves", "linked_defense"}:
            self.budget_points -= profile.cost
        self.radar_profile_name = profile_name
        self.radar_health = profile.health
        self.ew_power = min(profile.ew_power, self.ew_power + profile.ew_power * 0.35)
        self.radar_manual_aim = False
        self.events.append(f"{profile.name} radar online")
        return True

    def place_radar_site(self, profile_name: str, position: Vector2, *, bearing_degrees: float | None = None) -> RadarSite | None:
        profile = RADAR_PROFILES[profile_name]
        if len(self.radar_sites) >= 6:
            self.events.append("Radar site map is full")
            return None
        if self.game_mode in {"budget_waves", "linked_defense"} and self.budget_points < profile.cost:
            self.events.append(f"Need {profile.cost} points to place {profile.name}")
            return None
        if self.game_mode in {"budget_waves", "linked_defense"}:
            self.budget_points -= profile.cost
        site = RadarSite(
            site_id=next(self._radar_site_ids),
            profile=profile,
            position=position.clamp(-WORLD_HALF_SIZE, WORLD_HALF_SIZE, -WORLD_HALF_SIZE, WORLD_HALF_SIZE),
            health=profile.health,
            bearing_degrees=_normalize_degrees(self.radar_bearing_degrees if bearing_degrees is None else bearing_degrees),
            auto_scan=True,
        )
        self.radar_sites[site.site_id] = site
        self.events.append(f"Placed radar site #{site.site_id}: {profile.name}")
        return site

    def spawn_hostile_radar(self, profile_name: str = "P-18 Spoon Rest", position: Vector2 | None = None) -> HostileRadarSite:
        profile = RADAR_PROFILES[profile_name]
        spawn = position if position is not None else self._edge_position()
        site = HostileRadarSite(
            site_id=next(self._hostile_radar_site_ids),
            profile=profile,
            position=spawn.clamp(-WORLD_HALF_SIZE, WORLD_HALF_SIZE, -WORLD_HALF_SIZE, WORLD_HALF_SIZE),
            health=max(2, profile.health // 2),
            bearing_degrees=_bearing_between(spawn, self.base_position),
            auto_scan=True,
        )
        self.hostile_radar_sites[site.site_id] = site
        self.events.append(f"Hostile radar #{site.site_id} online: {profile.name}")
        return site

    def set_map_profile(self, profile_name: str) -> None:
        self.map_profile_name = profile_name
        self.events.append(f"Map set to {profile_name}")

    def aim_primary_radar_at(self, point: Vector2) -> None:
        self.radar_bearing_degrees = _bearing_between(self.base_position, point)
        self.radar_manual_aim = True
        self.events.append(f"Radar scan bearing set {self.radar_bearing_degrees:03.0f} deg")

    def slew_primary_radar(self, delta_degrees: float) -> None:
        self.radar_bearing_degrees = _normalize_degrees(self.radar_bearing_degrees + delta_degrees)
        self.radar_manual_aim = True
        self.events.append(f"Radar scan bearing set {self.radar_bearing_degrees:03.0f} deg")

    def resume_auto_radar_scan(self) -> None:
        self.radar_manual_aim = False
        self.events.append("Radar scan returned to auto sweep")

    def manual_spawn_projectile(self, profile_name: str) -> Projectile | None:
        profile = PROJECTILE_PROFILES[profile_name]
        if self.projectile_inventory.get(profile_name, 0) <= 0:
            self.events.append(f"No {profile.name} rounds left")
            return None
        if self.game_mode in {"budget_waves", "linked_defense"} and self.budget_points < profile.cost:
            self.events.append(f"Need {profile.cost} points for {profile.name}")
            return None
        self.projectile_inventory[profile_name] -= 1
        if self.game_mode in {"budget_waves", "linked_defense"}:
            self.budget_points -= profile.cost
        return self.spawn_projectile(profile_name)

    def spawn_projectile(
        self,
        profile_name: str,
        *,
        owner: str = "enemy",
        launcher_enemy_id: int | None = None,
        launcher_platform: str = "",
        position: Vector2 | None = None,
        direction: Vector2 | None = None,
        player_controlled: bool = False,
    ) -> Projectile:
        profile = PROJECTILE_PROFILES[profile_name]
        spawn = position if position is not None else self._edge_position()
        aim_offset = Vector2(self.rng.uniform(-90, 90), self.rng.uniform(-90, 90))
        travel_direction = direction if direction is not None and direction.magnitude() > 0 else self.base_position + aim_offset - spawn
        if travel_direction.magnitude() == 0:
            travel_direction = Vector2(0.0, -1.0)
        altitude = self._initial_projectile_altitude(profile)
        projectile = Projectile(
            projectile_id=next(self._projectile_ids),
            profile=profile,
            position=spawn,
            velocity=travel_direction.normalized() * profile.speed,
            owner=owner,
            launcher_enemy_id=launcher_enemy_id,
            launcher_platform=launcher_platform,
            player_controlled=player_controlled,
            altitude=altitude,
            vertical_velocity=self._initial_projectile_vertical_velocity(profile, altitude),
        )
        self.projectiles[projectile.projectile_id] = projectile
        return projectile

    def _initial_projectile_altitude(self, profile: ProjectileProfile) -> float:
        if profile.terrain_following:
            return min(180.0, max(45.0, profile.cruise_altitude * 0.16))
        if profile.role == "drone":
            return 260.0
        if profile.role == "cruise":
            return min(900.0, max(120.0, profile.cruise_altitude * 0.55))
        if profile.role == "bomb":
            return min(1800.0, max(650.0, profile.cruise_altitude))
        if profile.role == "anti-radiation":
            return 950.0
        if profile.role == "ballistic":
            return 80.0
        if profile.role == "rocket":
            return 120.0
        return max(80.0, profile.cruise_altitude)

    def _initial_projectile_vertical_velocity(self, profile: ProjectileProfile, altitude: float) -> float:
        if profile.role == "ballistic":
            return max(260.0, profile.ballistic_apogee * 0.08)
        if profile.role == "rocket":
            return 80.0
        if profile.role == "anti-radiation":
            return 18.0
        if profile.role == "bomb":
            return -55.0
        if profile.terrain_following or profile.role in {"cruise", "drone"}:
            return 0.0
        return altitude * 0.02

    def spawn_random_projectile(self) -> Projectile:
        return self.spawn_projectile(self.rng.choice(tuple(PROJECTILE_PROFILES)))

    def spawn_enemy(self, profile_name: str) -> Enemy:
        profile = ENEMY_PROFILES[profile_name]
        spawn = self._edge_position()
        speed_mult = self.current_map.ground_speed_mult if profile.platform == "ground" else 1.0
        direction = (self.base_position - spawn).normalized()
        enemy = Enemy(
            enemy_id=next(self._enemy_ids),
            profile=profile,
            position=spawn,
            velocity=direction * profile.speed * speed_mult,
            next_launch_at=self.time + self.rng.uniform(1.0, 2.5),
            health=profile.health,
            altitude=0.0 if profile.platform == "ground" else profile.altitude,
        )
        self.enemies[enemy.enemy_id] = enemy
        return enemy

    def spawn_random_enemy(self) -> Enemy:
        return self.spawn_enemy(self.rng.choice(tuple(ENEMY_PROFILES)))

    def spawn_player_projectile(self, profile_name: str) -> Projectile:
        self.player_projectile_profile_name = profile_name
        if self.player_projectile_id in self.projectiles:
            existing = self.projectiles[self.player_projectile_id]
            existing.profile = PROJECTILE_PROFILES[profile_name]
            existing.velocity = existing.velocity.normalized() * existing.profile.speed
            return existing

        spawn = Vector2(0.0, WORLD_HALF_SIZE)
        direction = (self.base_position - spawn).normalized()
        projectile = self.spawn_projectile(
            profile_name,
            owner="player",
            position=spawn,
            direction=direction,
            player_controlled=True,
        )
        self.player_projectile_id = projectile.projectile_id
        self.events.append(f"Player controlling {projectile.profile.name} #{projectile.projectile_id}")
        return projectile

    def set_player_control(self, control: Vector2) -> None:
        self.player_control = control

    def use_defender_ew(self, action_name: str) -> bool:
        if not self.radar_alive:
            self.events.append("EW unavailable: radar destroyed")
            return False
        action = EW_ACTIONS[action_name]
        min_year = EW_ACTION_MIN_YEARS.get(action.name, 1935)
        if self.current_radar.year < min_year:
            self.events.append(f"{action.name} requires {min_year}s-era EW equipment")
            return False
        if self.ew_power < action.cost:
            self.events.append(f"Need {action.cost:.0f} EW power for {action.name}")
            return False
        self.ew_power -= action.cost
        if action.effect == "eccm":
            self.eccm_until = self.time + action.duration
            for track_id in tuple(self.ghost_track_ids):
                self.tracker.remove(track_id)
            self.ghost_track_ids.clear()
            self.events.append("ECCM sweep: ghost tracks cleared")
        elif action.effect == "burn":
            self.burn_through_until = self.time + action.duration
            self.events.append("Burn-through mode raised track quality")
        elif action.effect == "decoy":
            self.decoy_until = self.time + action.duration
            self.events.append("Defensive decoys radiating")
        elif action.effect == "silent":
            self.radar_silent_until = self.time + action.duration
            self.events.append("EMCON silence: radar emissions reduced")
        elif action.effect == "directional":
            self.directional_ew_until = self.time + action.duration
            self.directional_ew_bearing_degrees = self.radar_bearing_degrees
            self.directional_ew_strength = min(1.0, 0.72 + self.current_radar.jamming_resistance * 0.24)
            self.field_effects.append(
                DirectionalEffect(
                    "directional-ew",
                    self.base_position,
                    self.directional_ew_bearing_degrees,
                    430.0,
                    58.0,
                    self.directional_ew_until,
                    self.directional_ew_strength,
                    "#ff70a6",
                    "DIR EW",
                )
            )
            for site in self.hostile_radar_sites.values():
                if self.directional_ew_level_at(site.position) > 0.25:
                    site.jammed_until = max(site.jammed_until, self.directional_ew_until)
            self.events.append(f"Directional EW blackout {self.directional_ew_bearing_degrees:03.0f} deg")
        return True

    def activate_eccm(self) -> bool:
        return self.use_defender_ew("ECCM Sweep")

    def answer_hq_call(self) -> str | None:
        if self.pending_hq_call is None:
            self.events.append("HQ line is quiet")
            return None
        call = self.pending_hq_call
        self.pending_hq_call = None
        self.hq_orders_completed += 1
        self.story_stage += 1
        if self.game_mode == "story":
            if self.story_stage == 1:
                self.spawn_enemy("Scout UAV")
            elif self.story_stage == 2:
                self.use_defender_ew("Burn Through")
            elif self.story_stage == 3:
                self.spawn_enemy("SEAD Aircraft")
            elif self.story_stage >= 4:
                self._trigger_random_event("Mortar Wave")
        elif self.game_mode == "nuclear_plant":
            self.score += 10
        self.events.append("HQ acknowledged")
        return call

    def set_manual_aim_point(self, point: Vector2) -> None:
        self.manual_aim_point = point.clamp(-WORLD_HALF_SIZE, WORLD_HALF_SIZE, -WORLD_HALF_SIZE, WORLD_HALF_SIZE)
        self.events.append(f"Manual aim set ({self.manual_aim_point.x:.0f}, {self.manual_aim_point.y:.0f})")

    def repair_radar_wire(self, color: str) -> bool:
        if not self.radar_repair_needed:
            self.events.append("No radar wire repair needed")
            return False
        expected = self.radar_repair_sequence[self.radar_repair_index]
        if color != expected:
            self.radar_repair_index = 0
            self.score -= 5
            self.events.append(f"Wrong wire: repair sequence reset after {color}")
            return False
        self.radar_repair_index += 1
        if self.radar_repair_index < len(self.radar_repair_sequence):
            self.events.append(f"{color.title()} wire seated")
            return True
        self.radar_repair_needed = False
        self.radar_repair_sequence = ()
        self.radar_repair_index = 0
        self.radar_stuck_until = 0.0
        self.radar_stuck_pending_break = False
        self.radar_health = max(1, self.current_radar.health // 2)
        self.next_radar_fault_check_at = self.time + 10.0
        self.events.append("Radar repair complete: scope restored")
        return True

    def repair_summary(self) -> str:
        if not self.radar_repair_needed:
            if self.time < self.radar_stuck_until:
                return f"Radar stuck {self.radar_stuck_until - self.time:.1f}s"
            return "Repair board clear"
        progress = self.radar_repair_index
        total = len(self.radar_repair_sequence)
        next_wire = self.radar_repair_sequence[progress] if progress < total else "done"
        return f"Wire repair {progress}/{total}; next {next_wire}"

    def manual_cannon_fire(self, profile_name: str, aim_point: Vector2 | None = None) -> bool:
        profile = INTERCEPTOR_PROFILES[profile_name]
        if profile.category != "gun":
            self.events.append("Manual fire is cannon-only")
            return False
        if not self._defense_compatible_with_current_radar(profile):
            return False
        if not self._consume_defense(profile):
            return False
        target_point = aim_point or self.manual_aim_point
        if target_point is None:
            tracks = [track for track in self.tracker.tracks if not self.is_ghost_track(track.projectile_id)]
            if not tracks:
                self.events.append("No track for manual cannon fire")
                return False
            target_point = min(tracks, key=lambda track: track.position.distance_to(self.base_position)).predict(self.time + 0.35)
        kill_radius = profile.blast_radius * 1.4
        projectile = self._nearest_projectile_to(target_point, kill_radius)
        if projectile is not None:
            projectile.active = False
            self.tracker.remove(projectile.projectile_id)
            self.projectiles.pop(projectile.projectile_id, None)
            self.score += projectile.profile.score_value
            self.events.append(f"Manual cannon splash: {projectile.profile.name}")
            return True
        enemy = self._nearest_visible_enemy_to(target_point, kill_radius)
        if enemy is not None:
            enemy.health -= 1
            if enemy.health <= 0:
                enemy.active = False
                self.enemies.pop(enemy.enemy_id, None)
                self.enemy_tracks.pop(enemy.enemy_id, None)
                self.score += enemy.profile.score_value
                self.events.append(f"Manual cannon destroyed {enemy.profile.name}")
            else:
                self.events.append(f"Manual cannon hit {enemy.profile.name}")
            return True
        self.events.append("Manual cannon miss")
        return False

    def use_sonic_weapon(self, profile_name: str, aim_point: Vector2 | None = None) -> bool:
        profile = INTERCEPTOR_PROFILES[profile_name]
        if profile.category != "sonic":
            self.events.append("Sonic pulse requires a sonic defense item")
            return False
        if not self._defense_compatible_with_current_radar(profile):
            return False
        if not self._consume_defense(profile):
            return False
        target_point = aim_point or self.manual_aim_point
        bearing = self.radar_bearing_degrees if target_point is None else _bearing_between(self.base_position, target_point)
        max_range = profile.speed
        width = profile.blast_radius
        self.field_effects.append(
            DirectionalEffect(
                "sonic",
                self.base_position,
                bearing,
                max_range,
                width,
                self.time + 0.65,
                1.0,
                profile.color,
                "SONIC",
            )
        )

        disrupted = 0
        for projectile in list(self.projectiles.values()):
            if not projectile.active or projectile.owner == "player":
                continue
            factor = _cone_factor(self.base_position, bearing, projectile.position, max_range, width)
            if factor <= 0 or projectile.altitude > 720.0:
                continue
            if projectile.profile.role == "drone" or (projectile.profile.role == "cruise" and projectile.velocity.magnitude() < 125.0):
                projectile.active = False
                self.tracker.remove(projectile.projectile_id)
                self.projectiles.pop(projectile.projectile_id, None)
                self.score += max(4, projectile.profile.score_value // 2)
                disrupted += 1
            elif projectile.profile.role in {"anti-radiation", "cruise"}:
                wobble = Vector2(self.rng.uniform(-0.45, 0.45), self.rng.uniform(-0.45, 0.45))
                direction = (projectile.velocity.normalized() + wobble * factor).normalized()
                projectile.velocity = direction * projectile.velocity.magnitude()
                disrupted += 1

        for enemy in self.enemies.values():
            if not enemy.active:
                continue
            factor = _cone_factor(self.base_position, bearing, enemy.position, max_range, width)
            if factor <= 0:
                continue
            if enemy.profile.platform == "ground" or "uav" in enemy.profile.name.lower() or "drone" in enemy.profile.name.lower():
                enemy.revealed_until = max(enemy.revealed_until, self.time + 1.4 * factor)
                if factor > 0.62 and enemy.profile.platform != "air":
                    enemy.health -= 1
                    disrupted += 1
                    if enemy.health <= 0:
                        enemy.active = False
                        self.enemy_tracks.pop(enemy.enemy_id, None)
                        self.score += enemy.profile.score_value

        for site in self.hostile_radar_sites.values():
            if not site.active or site.health <= 0:
                continue
            factor = _cone_factor(self.base_position, bearing, site.position, max_range, width)
            if factor <= 0:
                continue
            site.jammed_until = max(site.jammed_until, self.time + 1.0 + factor)
            if factor > 0.70:
                site.health -= 1
                disrupted += 1
                if site.health <= 0:
                    site.active = False
                    self.score += 45

        self.events.append(f"Sonic cone pulse disrupted {disrupted} contacts")
        return True

    def plant_insert_rods(self) -> None:
        self.control_rod_position = min(100.0, self.control_rod_position + 12.0)
        self.plant_message = "Control rods inserted"
        self.events.append(self.plant_message)

    def plant_withdraw_rods(self) -> None:
        self.control_rod_position = max(0.0, self.control_rod_position - 10.0)
        self.plant_message = "Control rods withdrawn"
        self.events.append(self.plant_message)

    def plant_toggle_pumps(self) -> None:
        target = not (self.pump_a_online or self.pump_b_online)
        self.pump_a_online = target
        self.pump_b_online = target
        self.pumps_online = target
        self.plant_message = "Both coolant pump trains online" if target else "Both coolant pump trains offline"
        self.events.append(self.plant_message)

    def plant_toggle_pump_a(self) -> None:
        self.pump_a_online = not self.pump_a_online
        self.pumps_online = self.pump_a_online or self.pump_b_online
        self.plant_message = "Coolant pump A online" if self.pump_a_online else "Coolant pump A offline"
        self.events.append(self.plant_message)

    def plant_toggle_pump_b(self) -> None:
        self.pump_b_online = not self.pump_b_online
        self.pumps_online = self.pump_a_online or self.pump_b_online
        self.plant_message = "Coolant pump B online" if self.pump_b_online else "Coolant pump B offline"
        self.events.append(self.plant_message)

    def plant_scram(self) -> None:
        self.control_rod_position = 100.0
        self.reactor_power = min(self.reactor_power, 18.0)
        self.plant_message = "SCRAM: emergency shutdown"
        self.events.append(self.plant_message)

    def plant_vent_steam(self) -> None:
        self.reactor_temperature = max(240.0, self.reactor_temperature - 35.0)
        self.coolant_level = max(0.0, self.coolant_level - 7.0)
        self.steam_pressure = max(10.0, self.steam_pressure - 16.0)
        self.plant_message = "Steam vented"
        self.events.append(self.plant_message)

    def plant_raise_load(self) -> None:
        self.turbine_load = min(100.0, self.turbine_load + 10.0)
        self.plant_message = "Turbine load increased"
        self.events.append(self.plant_message)

    def plant_lower_load(self) -> None:
        self.turbine_load = max(0.0, self.turbine_load - 10.0)
        self.plant_message = "Turbine load reduced"
        self.events.append(self.plant_message)

    def step(self, dt: float) -> None:
        if dt <= 0:
            raise ValueError("dt must be positive")
        self.time += dt
        if self.game_mode == "nuclear_plant":
            self._step_plant(dt)
            self._maybe_trigger_plant_event()
            return
        self._regenerate_power(dt)
        self._advance_radar_sweeps(dt)
        self._step_hostile_radars(dt)
        self._advance_mode_before_motion()
        self._step_enemies(dt)
        self._step_projectiles(dt)
        self._step_interceptors(dt)
        self._cleanup_inactive()
        self._scan()
        self.tracker.prune(self.time)
        self._prune_enemy_tracks()
        self._cleanup_stale_ghosts()
        self._cleanup_field_effects()
        self._maybe_fault_primary_radar()
        self._maybe_trigger_random_event()
        self._maybe_trigger_story_call()
        self._advance_mode_after_scan()

    def _advance_radar_sweeps(self, dt: float) -> None:
        primary_fov = self.radar_fov_degrees(self.current_radar)
        if (primary_fov < 359.0 or self.radar_requires_sweep_contact(self.current_radar)) and not self.radar_manual_aim and self.primary_radar_online:
            speed = self.radar_sweep_speed_degrees(self.current_radar)
            self.radar_bearing_degrees = _normalize_degrees(self.radar_bearing_degrees + speed * dt)
        for site in self.radar_sites.values():
            if not site.active or site.health <= 0 or not site.auto_scan:
                continue
            if self.radar_fov_degrees(site.profile) >= 359.0 and not self.radar_requires_sweep_contact(site.profile):
                continue
            speed = self.radar_sweep_speed_degrees(site.profile)
            site.bearing_degrees = _normalize_degrees(site.bearing_degrees + speed * dt)
        for site in self.hostile_radar_sites.values():
            if not site.active or site.health <= 0 or not site.auto_scan or self.time < site.jammed_until:
                continue
            if self.radar_fov_degrees(site.profile) >= 359.0 and not self.radar_requires_sweep_contact(site.profile):
                continue
            speed = self.radar_sweep_speed_degrees(site.profile)
            site.bearing_degrees = _normalize_degrees(site.bearing_degrees + speed * dt)

    def _step_plant(self, dt: float) -> None:
        pump_trains = (0.5 if self.pump_a_online else 0.0) + (0.5 if self.pump_b_online else 0.0)
        self.pumps_online = pump_trains > 0.0
        blackout_factor = 0.28 if self.plant_blackout else 1.0
        pump_efficiency = max(0.04, pump_trains * blackout_factor)
        reactivity = max(0.0, 1.0 - self.control_rod_position / 100.0)
        grid_error = self.grid_demand - self.generator_output
        self.turbine_load = min(100.0, max(0.0, self.turbine_load + grid_error * 0.006 * dt))
        self.reactor_power += (reactivity * 20.0 - self.turbine_load * 0.075 - self.reactor_power * 0.042) * dt
        self.reactor_power = min(125.0, max(0.0, self.reactor_power))
        self.feedwater_flow += ((75.0 + pump_efficiency * 25.0) - self.feedwater_flow) * 0.06 * dt
        self.coolant_level += (self.feedwater_flow * 0.048 * pump_efficiency - self.reactor_power * 0.019 - 0.38) * dt
        self.coolant_level = min(100.0, max(0.0, self.coolant_level))
        cooling = self.coolant_level * pump_efficiency * 0.13
        self.reactor_temperature += (self.reactor_power * 0.43 - cooling - self.turbine_load * 0.035) * dt
        self.reactor_temperature = max(120.0, self.reactor_temperature)
        self.steam_pressure += (self.reactor_power * 0.30 - self.turbine_load * 0.22 - self.steam_pressure * 0.018) * dt
        self.steam_pressure = min(120.0, max(0.0, self.steam_pressure))
        target_output = min(self.reactor_power, self.turbine_load, self.steam_pressure)
        self.generator_output += (target_output - self.generator_output) * 0.11 * dt
        self.generator_output = min(120.0, max(0.0, self.generator_output))
        vibration_target = abs(self.generator_output - self.grid_demand) * 0.22 + (100.0 - self.coolant_level) * 0.08
        self.turbine_vibration += (vibration_target - self.turbine_vibration) * 0.08 * dt
        self.plant_alarm = (
            self.reactor_temperature > 720
            or self.coolant_level < 28
            or self.reactor_power > 105
            or self.steam_pressure > 105
            or self.turbine_vibration > 34
        )
        if self.plant_alarm:
            thermal_penalty = max(0.0, self.reactor_temperature - 650.0) * 0.003
            pressure_penalty = max(0.0, self.steam_pressure - 95.0) * 0.012
            coolant_penalty = max(0.0, 30.0 - self.coolant_level) * 0.04
            self.containment_integrity = max(0.0, self.containment_integrity - (thermal_penalty + pressure_penalty + coolant_penalty) * dt)
            self.score -= 1
            self.plant_message = "Plant ALARM: stabilize reactor conditions"
        elif (
            35 <= self.reactor_power <= 95
            and 260 <= self.reactor_temperature <= 650
            and abs(self.generator_output - self.grid_demand) < 16
        ):
            self.score += 1
            self.plant_message = "Grid synchronized"
        if self.containment_integrity <= 0:
            self.running_failure()

    def running_failure(self) -> None:
        self.base_health = 0
        self.plant_message = "Plant containment failed"
        self.events.append(self.plant_message)

    def jamming_level_at(self, position: Vector2) -> float:
        level = 0.0
        for enemy in self.enemies.values():
            if not enemy.active or enemy.profile.jammer_strength <= 0:
                continue
            if not self.is_enemy_visible(enemy) and self.current_radar.name == "P-18 Spoon Rest":
                continue
            distance = position.distance_to(enemy.position)
            if distance > enemy.profile.jammer_radius:
                continue
            falloff = 1.0 - 0.65 * (distance / enemy.profile.jammer_radius)
            level += enemy.profile.jammer_strength * max(0.0, falloff)
        if self.is_eccm_active:
            level *= 0.38
        if self.is_burn_through_active:
            level *= 0.55
        level *= max(0.20, 1.0 - self.current_radar.jamming_resistance * 0.62)
        return min(2.5, level)

    def active_jammer_count(self) -> int:
        return sum(1 for enemy in self.enemies.values() if enemy.active and enemy.profile.jammer_strength > 0)

    def is_ghost_track(self, track_id: int) -> bool:
        return track_id in self.ghost_track_ids

    def _enemy_source_signature_visible(self, enemy: Enemy, radar: RadarProfile) -> bool:
        if not enemy.active:
            return False
        if self.time < enemy.revealed_until:
            return True
        if self.is_eccm_active or self.is_burn_through_active:
            return True
        radar_signature_bonus = radar.stealth_detection
        if "vhf" in radar.band.lower() or "hf" in radar.band.lower():
            radar_signature_bonus += 0.22
        if "aesa" in radar.sensor_type.lower() or "easa" in radar.sensor_type.lower():
            radar_signature_bonus += 0.10
        if "passive" in radar.sensor_type.lower() and enemy.profile.jammer_strength > 0:
            radar_signature_bonus += 0.34
        map_penalty = self.current_map.clutter * 0.22 + self.current_map.terrain_shadow * 0.28
        if enemy.profile.platform == "ground":
            map_penalty += self.current_map.terrain_shadow * 0.16
        if enemy.profile.signature + radar_signature_bonus < 0.55 + map_penalty:
            return False
        if enemy.profile.stealth_period <= 0:
            return True
        stealth_bonus = max(0.35, 1.0 - radar.stealth_detection * 0.72)
        phase = (self.time + enemy.enemy_id * 0.73) % enemy.profile.stealth_period
        return phase >= enemy.profile.stealth_duration * stealth_bonus

    def is_enemy_visible(self, enemy: Enemy) -> bool:
        if not enemy.active:
            return False
        for radar, position, health, bearing in self._active_radar_sources():
            if not self.radar_source_covers_position(
                radar,
                position,
                health,
                bearing,
                enemy.position,
                radar_cross_section=enemy.profile.signature,
                altitude=enemy.altitude,
                target_role=enemy.profile.platform,
                terrain_following=enemy.profile.platform == "ground",
                emitter=enemy.profile.jammer_strength > 0,
                include_jamming=False,
            ):
                continue
            if self._enemy_source_signature_visible(enemy, radar):
                return True
        return False

    def _enemy_track_stale_after(self, track: EnemyTrack) -> float:
        base = {
            "bearing-only": 1.4,
            "height-only": 1.4,
            "early-warning": 3.0,
            "search-cue": 2.2,
            "ballistic-only": 2.0,
            "surveillance-track": 5.5,
            "weapon-locating": 2.8,
            "track-while-scan": 4.2,
            "fire-control": 3.4,
        }.get(track.track_mode, 3.0)
        if track.revealed:
            base += 0.8
        if self.is_eccm_active or self.is_burn_through_active:
            base += 0.7
        if track.target_role == "ground":
            base *= 0.82
        return base

    def _enemy_weapon_quality_threshold(self, track: EnemyTrack) -> float:
        threshold = 0.34
        if track.track_mode == "fire-control":
            threshold = 0.28
        elif track.track_mode == "track-while-scan":
            threshold = 0.32
        elif track.target_role == "ground":
            threshold = 0.40
        if self.is_burn_through_active:
            threshold -= 0.06
        return max(0.20, threshold)

    def enemy_track_for(self, enemy_id: int, *, require_engageable: bool = False) -> EnemyTrack | None:
        track = self.enemy_tracks.get(enemy_id)
        if track is None:
            return None
        if self.time - track.last_timestamp > self._enemy_track_stale_after(track):
            return None
        if require_engageable and (not track.engageable or track.confidence < self._enemy_weapon_quality_threshold(track)):
            return None
        return track

    def tracked_enemies(self, *, require_engageable: bool = False) -> tuple[Enemy, ...]:
        return tuple(
            enemy
            for enemy in self.enemies.values()
            if enemy.active and self.enemy_track_for(enemy.enemy_id, require_engageable=require_engageable) is not None
        )

    def visible_enemies(self) -> tuple[Enemy, ...]:
        return self.tracked_enemies()

    def ew_summary(self) -> str:
        jamming = self.jamming_level_at(self.base_position)
        effects = []
        if self.is_eccm_active:
            effects.append("ECCM")
        if self.is_burn_through_active:
            effects.append("BURN")
        if self.is_decoy_active:
            effects.append("DECOY")
        if self.is_radar_silent:
            effects.append("EMCON")
        if self.is_directional_ew_active:
            effects.append("DIR")
        effect_text = ",".join(effects) if effects else "none"
        return f"EW {self.ew_power:4.0f}/{self.current_radar.ew_power:.0f} | Jam {jamming:.2f} | {effect_text}"

    def directional_ew_level_at(self, position: Vector2) -> float:
        if not self.is_directional_ew_active:
            return 0.0
        cone = _cone_factor(
            self.base_position,
            self.directional_ew_bearing_degrees,
            position,
            max_range=430.0,
            width_degrees=58.0,
        )
        return min(1.0, cone * self.directional_ew_strength)

    def active_field_effects(self) -> tuple[DirectionalEffect, ...]:
        return tuple(effect for effect in self.field_effects if self.time < effect.until)

    def ammo_summary(self, profile_name: str) -> str:
        ammo = self.defense_inventory.get(profile_name, 0)
        return f"{ammo} left"

    def projectile_ammo_summary(self, profile_name: str) -> str:
        ammo = self.projectile_inventory.get(profile_name, 0)
        return f"{ammo} left"

    def plant_summary(self) -> str:
        pumps = f"A:{'on' if self.pump_a_online else 'off'} B:{'on' if self.pump_b_online else 'off'}"
        alarm = "ALARM" if self.plant_alarm else "stable"
        return (
            f"Plant {alarm} | Power {self.reactor_power:.0f}% | Output {self.generator_output:.0f}/{self.grid_demand:.0f}% | "
            f"Temp {self.reactor_temperature:.0f} | Coolant {self.coolant_level:.0f}% | "
            f"Pressure {self.steam_pressure:.0f}% | Rods {self.control_rod_position:.0f}% | Pumps {pumps}"
        )

    def _regenerate_power(self, dt: float) -> None:
        if not self.radar_alive:
            self.ew_power = 0.0
            return
        regen = self.current_radar.ew_regen
        if self.is_radar_silent:
            regen *= 0.55
        self.ew_power = min(self.current_radar.ew_power, self.ew_power + regen * dt)

    def _step_hostile_radars(self, _dt: float) -> None:
        for site in self.hostile_radar_sites.values():
            if not site.active or site.health <= 0:
                continue
            if self.directional_ew_level_at(site.position) > 0.25:
                site.jammed_until = max(site.jammed_until, self.directional_ew_until)
            if self.time < site.jammed_until:
                continue
            if self.hostile_radar_has_fix_on_base(site) and self.time - site.last_fix_report_at > 5.0:
                site.last_fix_report_at = self.time
                self.events.append(f"Hostile radar #{site.site_id} has a fire-control fix")

    def hostile_radar_has_fix_on_base(self, site: HostileRadarSite) -> bool:
        if not site.active or site.health <= 0 or self.time < site.jammed_until:
            return False
        if self.directional_ew_level_at(site.position) > 0.25:
            return False
        return self.radar_source_detects_position_now(
            site.profile,
            site.position,
            site.health,
            site.bearing_degrees,
            self.base_position,
            radar_cross_section=3.0,
            altitude=35.0,
            target_role="radar",
            emitter=self.radar_alive and not self.is_radar_silent,
            include_jamming=False,
        )

    def hostile_radar_pressure(self) -> int:
        return sum(1 for site in self.hostile_radar_sites.values() if self.hostile_radar_has_fix_on_base(site))

    def _enemy_fire_control_aim_point(self, enemy: Enemy) -> Vector2:
        if not self.hostile_radar_sites:
            return self.base_position
        fixes = self.hostile_radar_pressure()
        if fixes <= 0:
            spread = 70.0 if enemy.profile.platform == "ground" else 42.0
        else:
            spread = max(6.0, 24.0 - fixes * 6.0)
        return self.base_position + Vector2(self.rng.uniform(-spread, spread), self.rng.uniform(-spread, spread))

    def _advance_mode_before_motion(self) -> None:
        if self.game_mode == "projectile" and self.player_projectile_id not in self.projectiles:
            self.spawn_player_projectile(self.player_projectile_profile_name)
            self.next_auto_interceptor_at = self.time + 2.0
        elif self.game_mode in {"waves", "budget_waves", "ground_assault", "linked_defense"} and not self.enemies and self.time >= self.next_wave_at:
            self._spawn_wave()

    def _maybe_trigger_story_call(self) -> None:
        if self.game_mode != "story" or self.pending_hq_call is not None:
            return
        if self.time < self.next_wave_at:
            return
        call = STORY_CALLS[min(self.story_stage, len(STORY_CALLS) - 1)]
        self.pending_hq_call = call
        self.next_wave_at = self.time + 18.0
        self.events.append("HQ phone ringing")

    def _maybe_trigger_random_event(self) -> None:
        if self.game_mode not in {"waves", "budget_waves", "ground_assault", "linked_defense", "story"}:
            return
        if self.time < self.next_random_event_at:
            return
        event_name = self.rng.choice(RANDOM_EVENTS)
        self._trigger_random_event(event_name)
        self.next_random_event_at = self.time + self.rng.uniform(16.0, 28.0)

    def _trigger_random_event(self, event_name: str) -> None:
        if event_name == "Mortar Wave":
            for _ in range(4 + min(self.wave_number, 4)):
                self.spawn_projectile("81mm Mortar Bomb")
            self.events.append("Event: mortar wave")
        elif event_name == "Drone Swarm":
            for _ in range(5 + min(self.wave_number, 5)):
                self.spawn_projectile("Shahed-style Loiterer")
            self.events.append("Event: drone swarm")
        elif event_name == "SEAD Raid":
            self.spawn_enemy("SEAD Aircraft")
            self.spawn_projectile("AGM-88 HARM")
            self.events.append("Event: SEAD raid")
        elif event_name == "Ground Push":
            for _ in range(3):
                self.spawn_enemy(self.rng.choice(("MLRS Battery", "Armored Column", "TEL Vehicle")))
            self.events.append("Event: ground push")
        elif event_name == "Ghost Storm":
            self.spawn_enemy("EW Aircraft")
            self.next_ghost_at = self.time
            self.events.append("Event: ghost storm")
        elif event_name == "Radiological Alert":
            self.radiological_until = self.time + 22.0
            self.events.append("Event: radiological alert")

    def _maybe_trigger_plant_event(self) -> None:
        if self.game_mode != "nuclear_plant" or self.time < self.next_plant_event_at:
            return
        self._trigger_plant_event(self.rng.choice(PLANT_EVENTS))
        self.next_plant_event_at = self.time + self.rng.uniform(18.0, 34.0)

    def _trigger_plant_event(self, event_name: str) -> None:
        if event_name == "Grid Demand Surge":
            self.grid_demand = min(95.0, self.grid_demand + 18.0)
            self.plant_message = "Plant event: grid demand surge"
        elif event_name == "Coolant Pump Trip":
            if self.pump_a_online:
                self.pump_a_online = False
            else:
                self.pump_b_online = False
            self.pumps_online = self.pump_a_online or self.pump_b_online
            self.plant_message = "Plant event: coolant pump trip"
        elif event_name == "Feedwater Drop":
            self.feedwater_flow = max(25.0, self.feedwater_flow - 24.0)
            self.coolant_level = max(20.0, self.coolant_level - 10.0)
            self.plant_message = "Plant event: feedwater drop"
        elif event_name == "Steam Valve Drift":
            self.steam_pressure = min(115.0, self.steam_pressure + 18.0)
            self.plant_message = "Plant event: steam valve drift"
        elif event_name == "Control Rod Drift":
            self.control_rod_position = max(0.0, self.control_rod_position - 8.0)
            self.plant_message = "Plant event: control rod drift"
        elif event_name == "Turbine Vibration":
            self.turbine_vibration = min(60.0, self.turbine_vibration + 16.0)
            self.plant_message = "Plant event: turbine vibration"
        elif event_name == "Training Inspection":
            self.score += 25
            self.plant_message = "Plant event: training inspection passed"
        self.events.append(self.plant_message)

    def _nearest_projectile_to(self, point: Vector2, radius: float) -> Projectile | None:
        candidates = [
            projectile
            for projectile in self.projectiles.values()
            if projectile.active and projectile.position.distance_to(point) <= radius
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda projectile: projectile.position.distance_to(point))

    def _nearest_visible_enemy_to(self, point: Vector2, radius: float) -> Enemy | None:
        candidates = [
            enemy
            for enemy in self.tracked_enemies()
            if (track := self.enemy_track_for(enemy.enemy_id)) is not None and track.position.distance_to(point) <= radius
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda enemy: self.enemy_track_for(enemy.enemy_id).position.distance_to(point))

    def _advance_mode_after_scan(self) -> None:
        if self.game_mode != "projectile" or self.player_projectile_id not in self.projectiles:
            return
        if self.time < self.next_auto_interceptor_at:
            return
        interceptor = self.deploy_interceptor(self.player_projectile_id, "NASAMS AMRAAM", ignore_inventory=True)
        self.next_auto_interceptor_at = self.time + (2.6 if interceptor else 0.9)
        if interceptor:
            self.events.append(f"Base fired {interceptor.profile.name} at player projectile")

    def _spawn_wave(self) -> None:
        self.wave_number += 1
        if self.game_mode == "ground_assault":
            pool = ["MLRS Battery", "Armored Column", "TEL Vehicle"]
            if self.wave_number >= 3:
                pool.append("Radar Jammer")
        else:
            pool = ["Scout UAV"]
            if self.wave_number >= 2:
                pool.append("Bomber")
            if self.wave_number >= 3:
                pool.extend(("Radar Jammer", "Stealth UAV"))
            if self.wave_number >= 4:
                pool.extend(("TEL Vehicle", "SEAD Aircraft"))
            if self.wave_number >= 5:
                pool.append("EW Aircraft")

        difficulty = self.wave_number + (2 if self.game_mode == "budget_waves" else 0)
        enemy_count = min(2 + difficulty, 10)
        for _ in range(enemy_count):
            self.spawn_enemy(self.rng.choice(pool))
        if self.game_mode in {"budget_waves", "linked_defense"}:
            self.budget_points += 80 + self.wave_number * 25
        if self.wave_number % 2 == 0:
            self.spawn_random_projectile()
        self.next_wave_at = self.time + max(6.0, 13.0 - min(self.wave_number, 7))
        self.events.append(f"Wave {self.wave_number} inbound")

    def _step_enemies(self, dt: float) -> None:
        for enemy in list(self.enemies.values()):
            if not enemy.active:
                continue
            self._update_enemy_velocity(enemy)
            enemy.step(dt)
            if self.time >= enemy.next_launch_at:
                profile_name = self.rng.choice(enemy.profile.projectile_names)
                aim_point = self._enemy_fire_control_aim_point(enemy)
                launched = self.spawn_projectile(
                    profile_name,
                    owner="enemy-vehicle" if enemy.profile.platform == "ground" else "enemy",
                    launcher_enemy_id=enemy.enemy_id,
                    launcher_platform=enemy.profile.platform,
                    position=enemy.position,
                    direction=aim_point - enemy.position,
                )
                launched.altitude = max(launched.altitude, enemy.altitude * 0.85)
                enemy.revealed_until = max(enemy.revealed_until, self.time + (0.45 if enemy.profile.platform == "ground" else 0.30))
                enemy.next_launch_at = self.time + enemy.profile.launch_interval
                self.events.append(f"{enemy.profile.name} #{enemy.enemy_id} launched {profile_name}")
            if enemy.profile.can_damage_base and enemy.position.distance_to(self.base_position) < BASE_RADIUS + 8:
                enemy.active = False
                self.base_health = max(0, self.base_health - 2)
                self.score -= 50
                self.events.append(f"{enemy.profile.name} reached the base")

    def _update_enemy_velocity(self, enemy: Enemy) -> None:
        if enemy.profile.platform == "radar":
            enemy.velocity = ZERO
            enemy.altitude = 0.0
            enemy.vertical_velocity = 0.0
            return
        to_base = self.base_position - enemy.position
        distance = max(1.0, to_base.magnitude())
        speed_mult = self.current_map.ground_speed_mult if enemy.profile.platform == "ground" else 1.0
        speed = enemy.profile.speed * speed_mult
        if enemy.profile.platform != "ground" and distance < enemy.profile.standoff_radius:
            tangent = Vector2(-to_base.y, to_base.x).normalized()
            away = (enemy.position - self.base_position).normalized() * 0.25
            enemy.velocity = (tangent + away).normalized() * speed
        elif enemy.profile.platform == "ground" and distance < enemy.profile.standoff_radius:
            tangent = Vector2(-to_base.y, to_base.x).normalized()
            enemy.velocity = (tangent * 0.45 + to_base.normalized() * 0.55).normalized() * speed
        else:
            enemy.velocity = to_base.normalized() * speed
        if enemy.profile.platform == "ground":
            enemy.altitude = 0.0
            enemy.vertical_velocity = 0.0
        else:
            target_altitude = enemy.profile.altitude + sin(self.time * 0.35 + enemy.enemy_id) * 90.0
            enemy.vertical_velocity += (target_altitude - enemy.altitude) * 0.02
            enemy.vertical_velocity *= 0.94

    def _step_projectiles(self, dt: float) -> None:
        for projectile in list(self.projectiles.values()):
            if not projectile.active:
                continue
            if projectile.player_controlled:
                self._steer_player_projectile(projectile, dt)
            elif projectile.profile.radar_seeking:
                self._guide_anti_radiation(projectile, dt)
            elif projectile.profile.terrain_following or projectile.profile.role in {"cruise", "drone", "rocket", "bomb"}:
                self._guide_aerodynamic_projectile(projectile, dt)
            self._apply_map_projectile_effects(projectile, dt)
            self._update_projectile_altitude(projectile, dt)
            previous_position = projectile.position
            projectile.step(dt)
            if projectile.owner == "player" and self._check_hostile_radar_hit(projectile, previous_position):
                continue
            if self._segment_hits_base(previous_position, projectile.position):
                self._handle_projectile_hit(projectile)
            elif projectile.position.magnitude() > WORLD_HALF_SIZE * 1.4:
                projectile.active = False
                self.tracker.remove(projectile.projectile_id)
                if projectile.owner == "player":
                    self.score -= 10
                    self.events.append("Player projectile left the arena")

    def _guide_anti_radiation(self, projectile: Projectile, dt: float) -> None:
        if projectile.owner == "player":
            target_site = self._nearest_hostile_radar_to(projectile.position)
            if target_site is not None:
                desired = (target_site.position - projectile.position).normalized()
            else:
                wander = Vector2(self.rng.uniform(-0.6, 0.6), self.rng.uniform(-0.6, 0.6))
                desired = (projectile.velocity.normalized() + wander).normalized()
        elif not self.radar_alive or self.is_radar_silent:
            wander = Vector2(self.rng.uniform(-0.6, 0.6), self.rng.uniform(-0.6, 0.6))
            desired = (projectile.velocity.normalized() + wander).normalized()
        else:
            desired = (self.base_position - projectile.position).normalized()
        blend = min(1.0, projectile.profile.turn_rate * dt)
        direction = (projectile.velocity.normalized() * (1.0 - blend) + desired * blend).normalized()
        projectile.velocity = direction * projectile.profile.speed

    def _nearest_hostile_radar_to(self, position: Vector2) -> HostileRadarSite | None:
        active_sites = [site for site in self.hostile_radar_sites.values() if site.active and site.health > 0]
        if not active_sites:
            return None
        return min(active_sites, key=lambda site: site.position.distance_to(position))

    def _guide_aerodynamic_projectile(self, projectile: Projectile, dt: float) -> None:
        target = self.base_position
        desired = (target - projectile.position).normalized()
        if desired.magnitude() == 0:
            return
        current = projectile.velocity.normalized()
        if current.magnitude() == 0:
            current = desired
        weave_strength = 0.05 if projectile.profile.terrain_following else 0.025
        lateral = Vector2(-desired.y, desired.x) * (sin(self.time * 1.7 + projectile.projectile_id) * weave_strength)
        desired = (desired + lateral).normalized()
        turn_factor = projectile.profile.turn_rate
        if projectile.profile.role == "rocket":
            turn_factor *= 0.55
        blend = min(1.0, max(0.02, turn_factor) * dt)
        direction = (current * (1.0 - blend) + desired * blend).normalized()
        speed = max(projectile.velocity.magnitude(), projectile.profile.speed * 0.92)
        projectile.velocity = direction * speed

    def _apply_map_projectile_effects(self, projectile: Projectile, dt: float) -> None:
        speed = projectile.velocity.magnitude()
        if projectile.profile.acceleration > 0 and projectile.profile.max_speed > speed:
            direction = projectile.velocity.normalized()
            speed = min(projectile.profile.max_speed, speed + projectile.profile.acceleration * dt)
            projectile.velocity = direction * speed
        drag = self.current_map.projectile_drag
        if projectile.profile.terrain_following:
            drag *= 0.7
        if projectile.profile.role == "ballistic":
            drag *= 0.45
        if projectile.profile.role == "drone":
            drag *= 1.2
        if projectile.profile.role == "bomb":
            drag *= 1.05
        projectile.velocity = projectile.velocity * max(0.75, 1.0 - drag * dt)

    def _update_projectile_altitude(self, projectile: Projectile, dt: float) -> None:
        profile = projectile.profile
        distance_to_base = projectile.position.distance_to(self.base_position)
        if profile.role == "ballistic":
            gravity = 190.0 + (45.0 if distance_to_base < 180 else 0.0)
            projectile.vertical_velocity -= gravity * dt
            if distance_to_base < 110:
                projectile.vertical_velocity -= 160.0 * dt
            if projectile.altitude > profile.ballistic_apogee:
                projectile.vertical_velocity = min(projectile.vertical_velocity, -60.0)
            return
        if profile.role == "rocket":
            target = 700.0 if distance_to_base > 170 else 120.0
        elif profile.role == "anti-radiation":
            target = 850.0 if distance_to_base > 160 else 160.0
        elif profile.terrain_following:
            target = 70.0 + self.current_map.terrain_shadow * 130.0
        elif profile.role == "drone":
            target = 240.0
        elif profile.role == "cruise":
            target = 420.0
        elif profile.role == "bomb":
            target = 0.0
        else:
            target = profile.cruise_altitude
        projectile.vertical_velocity += (target - projectile.altitude) * 0.06 * dt
        projectile.vertical_velocity *= max(0.82, 1.0 - 0.18 * dt)

    def _handle_projectile_hit(self, projectile: Projectile) -> None:
        projectile.active = False
        self.tracker.remove(projectile.projectile_id)
        if projectile.owner == "player":
            self.score += 100
            self.events.append("Player projectile hit the base")
            return
        if projectile.profile.radar_seeking and self.radar_destroyable:
            damage = max(1, projectile.profile.damage)
            if self.is_decoy_active:
                damage = max(0, damage - 1)
            self.radar_health = max(0, self.radar_health - damage)
            self.score -= 35 * damage
            self.events.append(f"{projectile.profile.name} damaged radar")
            if self.radar_health == 0:
                self.events.append("Primary radar destroyed")
            return
        self.base_health = max(0, self.base_health - projectile.profile.damage)
        self.score -= projectile.profile.damage * 20
        self.events.append(f"{projectile.profile.name} hit the base")

    def _segment_hits_base(self, start: Vector2, end: Vector2) -> bool:
        return self._segment_hits_circle(start, end, self.base_position, BASE_RADIUS)

    def _segment_hits_circle(self, start: Vector2, end: Vector2, center: Vector2, radius: float) -> bool:
        segment = end - start
        length_squared = segment.dot(segment)
        if length_squared == 0:
            return end.distance_to(center) < radius
        t = (center - start).dot(segment) / length_squared
        closest = start + segment * min(1.0, max(0.0, t))
        return closest.distance_to(center) < radius

    def _check_hostile_radar_hit(self, projectile: Projectile, previous_position: Vector2) -> bool:
        for site in self.hostile_radar_sites.values():
            if not site.active or site.health <= 0:
                continue
            if not self._segment_hits_circle(previous_position, projectile.position, site.position, BASE_RADIUS + 10.0):
                continue
            site.health -= max(1, projectile.profile.damage)
            projectile.active = False
            self.tracker.remove(projectile.projectile_id)
            self.projectiles.pop(projectile.projectile_id, None)
            if site.health <= 0:
                site.active = False
                self.score += 60
                self.events.append(f"Destroyed hostile radar #{site.site_id}: {site.profile.name}")
            else:
                self.score += 20
                self.events.append(f"Damaged hostile radar #{site.site_id}: {site.profile.name}")
            return True
        return False

    def _step_interceptors(self, dt: float) -> None:
        for interceptor in list(self.interceptors.values()):
            if not interceptor.active:
                continue
            interceptor.step(dt)
            if interceptor.target_kind == "enemy":
                self._check_enemy_intercept(interceptor)
            else:
                self._check_projectile_intercept(interceptor)

    def _check_projectile_intercept(self, interceptor: Interceptor) -> None:
        target = self.projectiles.get(interceptor.target_id)
        if not target or not target.active:
            interceptor.active = False
            return
        if interceptor.position.distance_to(target.position) <= interceptor.profile.blast_radius:
            target.active = False
            interceptor.active = False
            self.tracker.remove(target.projectile_id)
            if target.owner == "player":
                self.score -= 50
                self.events.append("Player projectile was intercepted")
            else:
                reward = target.profile.score_value
                self.score += reward
                if self.game_mode in {"budget_waves", "linked_defense"}:
                    self.budget_points += max(8, reward // 3)
                self.events.append(f"Intercepted {target.profile.name} #{target.projectile_id}")

    def _check_enemy_intercept(self, interceptor: Interceptor) -> None:
        target = self.enemies.get(interceptor.target_id)
        if not target or not target.active:
            interceptor.active = False
            return
        if interceptor.position.distance_to(target.position) <= interceptor.profile.blast_radius:
            target.health -= 1
            interceptor.active = False
            if target.health <= 0:
                target.active = False
                self.enemy_tracks.pop(target.enemy_id, None)
                self.score += target.profile.score_value
                if self.game_mode in {"budget_waves", "linked_defense"}:
                    self.budget_points += max(15, target.profile.score_value // 3)
                self.events.append(f"Destroyed {target.profile.name} #{target.enemy_id}")
            else:
                self.events.append(f"Hit {target.profile.name} #{target.enemy_id}")

    def _cleanup_inactive(self) -> None:
        self.projectiles = {pid: projectile for pid, projectile in self.projectiles.items() if projectile.active}
        self.interceptors = {iid: interceptor for iid, interceptor in self.interceptors.items() if interceptor.active}
        self.enemies = {eid: enemy for eid, enemy in self.enemies.items() if enemy.active}
        self.enemy_tracks = {eid: track for eid, track in self.enemy_tracks.items() if eid in self.enemies}
        self.radar_sites = {sid: site for sid, site in self.radar_sites.items() if site.active and site.health > 0}
        self.hostile_radar_sites = {sid: site for sid, site in self.hostile_radar_sites.items() if site.active and site.health > 0}
        if self.player_projectile_id not in self.projectiles:
            self.player_projectile_id = None

    def _active_radar_sources(self) -> tuple[tuple[RadarProfile, Vector2, int, float], ...]:
        sources: list[tuple[RadarProfile, Vector2, int, float]] = []
        if self.primary_radar_online:
            sources.append((self.current_radar, self.base_position, self.radar_health, self.radar_bearing_degrees))
        for site in self.radar_sites.values():
            if site.active and site.health > 0:
                sources.append((site.profile, site.position, site.health, site.bearing_degrees))
        return tuple(sources)

    def _effective_radar_range(self, radar: RadarProfile, health: int, map_profile: MapProfile) -> float:
        health_factor = 0.45 + 0.55 * (health / radar.health)
        passive_bonus = 0.32 if "passive" in radar.sensor_type.lower() else 0.0
        range_factor = (0.22 + passive_bonus) if self.is_radar_silent else 1.0
        scan_range_bonus = min(0.18, max(-0.12, (radar.scan_rate - 1.0) * 0.06))
        fov = self.radar_fov_degrees(radar)
        fov_range_bonus = 0.0 if fov >= 359.0 else min(0.20, (180.0 - min(fov, 180.0)) / 520.0)
        if self.radar_fov_shape(radar) == "fixed_lobe":
            fov_range_bonus -= 0.06
        effective_range = radar.range * map_profile.radar_range_mult * health_factor * range_factor * (1.0 + scan_range_bonus + fov_range_bonus)
        if self.time < self.radiological_until:
            effective_range *= 0.86
        return effective_range

    def _maybe_fault_primary_radar(self) -> None:
        if self.radar_health <= 0 or self.radar_repair_needed:
            return
        if self.radar_stuck_pending_break and self.time >= self.radar_stuck_until:
            self.radar_stuck_pending_break = False
            if self.rng.random() < 0.35:
                wires = ("red", "blue", "green", "yellow")
                self.radar_repair_sequence = tuple(self.rng.sample(wires, 3))
                self.radar_repair_index = 0
                self.radar_repair_needed = True
                self.events.append("Radar servo fault: repair wire board opened")
            else:
                self.events.append("Radar sweep unstuck")
            self.next_radar_fault_check_at = self.time + 8.0
            return
        if self.time < self.next_radar_fault_check_at or self.time < self.radar_stuck_until:
            return
        stress = self.jamming_level_at(self.base_position) + self.current_map.clutter * 0.45
        if self.time < self.radiological_until:
            stress += 0.35
        self.next_radar_fault_check_at = self.time + self.rng.uniform(3.0, 6.0)
        if stress > 0.45 and self.rng.random() < min(0.30, 0.04 + stress * 0.08):
            self.radar_stuck_until = self.time + self.rng.uniform(2.0, 4.2)
            self.radar_stuck_pending_break = True
            self.events.append("Radar sweep stuck: watch for servo fault")

    def _scan(self) -> None:
        self._maybe_create_ghost_track()
        sources = self._active_radar_sources()
        if not sources:
            return
        map_profile = self.current_map
        radiation_noise = 0.22 if self.time < self.radiological_until else 0.0
        self.radar_radius = max(self._effective_radar_range(radar, health, map_profile) for radar, _position, health, _bearing in sources)
        covered_projectile_ids: set[int] = set()
        for projectile in self.projectiles.values():
            coverage_sources = [
                source
                for source in sources
                if self.radar_source_covers_position(
                    source[0],
                    source[1],
                    source[2],
                    source[3],
                    projectile.position,
                    radar_cross_section=projectile.profile.radar_cross_section,
                    altitude=projectile.altitude,
                    target_role=projectile.profile.role,
                    terrain_following=projectile.profile.terrain_following,
                    emitter=projectile.profile.radar_seeking or projectile.profile.role == "anti-radiation",
                )
            ]
            if not coverage_sources:
                continue
            covered_projectile_ids.add(projectile.projectile_id)
            candidate_sources = [
                source
                for source in coverage_sources
                if self.radar_source_detects_position_now(
                    source[0],
                    source[1],
                    source[2],
                    source[3],
                    projectile.position,
                    radar_cross_section=projectile.profile.radar_cross_section,
                    altitude=projectile.altitude,
                    target_role=projectile.profile.role,
                    terrain_following=projectile.profile.terrain_following,
                    emitter=projectile.profile.radar_seeking or projectile.profile.role == "anti-radiation",
                )
            ]
            if not candidate_sources:
                continue
            source = max(
                candidate_sources,
                key=lambda item: self._target_adjusted_radar_range(
                    item[0],
                    item[2],
                    item[1],
                    projectile.position,
                    radar_cross_section=projectile.profile.radar_cross_section,
                    altitude=projectile.altitude,
                    target_role=projectile.profile.role,
                    terrain_following=projectile.profile.terrain_following,
                    emitter=projectile.profile.radar_seeking or projectile.profile.role == "anti-radiation",
                )
                - projectile.position.distance_to(item[1]),
            )
            radar, radar_position, health, _bearing = source
            track_mode = self.radar_track_mode(radar, projectile.profile.role)
            effective_range = self._target_adjusted_radar_range(
                radar,
                health,
                radar_position,
                projectile.position,
                radar_cross_section=projectile.profile.radar_cross_section,
                altitude=projectile.altitude,
                target_role=projectile.profile.role,
                terrain_following=projectile.profile.terrain_following,
                emitter=projectile.profile.radar_seeking or projectile.profile.role == "anti-radiation",
            )
            distance = projectile.position.distance_to(radar_position)

            jamming = self.jamming_level_at(projectile.position)
            effective_jamming = max(0.0, jamming * (1.0 - radar.jamming_resistance * 0.70))
            terrain_shadow = map_profile.terrain_shadow * (1.0 - radar.terrain_resistance)
            elevation_angle = degrees(atan2(projectile.altitude, max(distance, 1.0)))
            elevation_limit = radar.elevation_coverage + radar.beam_width
            if track_mode == "early-warning":
                elevation_limit += radar.beam_width * 1.4
            elif track_mode in {"track-while-scan", "fire-control", "weapon-locating"}:
                elevation_limit += radar.beam_width * 0.45
            if elevation_angle > elevation_limit:
                continue
            height_edge_penalty = max(0.0, elevation_angle - radar.elevation_coverage * 0.82) * 0.012
            if track_mode == "early-warning":
                height_edge_penalty *= 0.45
            low_altitude_penalty = 0.0
            if projectile.altitude < 180.0:
                low_altitude_penalty = max(0.0, 1.08 - radar.low_altitude_factor) * 0.22
            if projectile.altitude > 3800.0 and radar.category not in {"height-finder", "3D search", "ballistic-defense", "long-range 3D"}:
                height_edge_penalty += 0.10
            if projectile.profile.terrain_following:
                terrain_shadow *= max(0.72, 1.55 - radar.low_altitude_factor * 0.38)
            if projectile.profile.role == "ballistic" and radar.category in {"ballistic-defense", "counter-battery"}:
                terrain_shadow *= 0.65
            scan_penalty = max(0.0, 1.0 - radar.scan_rate) * 0.16
            if track_mode == "early-warning":
                scan_penalty *= 0.55
            elif track_mode in {"track-while-scan", "fire-control"}:
                scan_penalty *= 0.35
            precision_bonus = max(0.0, radar.tracking_precision - 1.0) * 0.08
            track_quality = self.radar_track_quality(radar, projectile.profile.role)
            range_margin = max(0.0, min(1.0, (effective_range - distance) / max(effective_range, 1.0)))
            mode_miss_adjust = {
                "bearing-only": 0.10,
                "height-only": 0.08,
                "early-warning": -0.08,
                "search-cue": 0.04,
                "ballistic-only": 0.03,
                "surveillance-track": -0.02,
                "weapon-locating": -0.05,
                "track-while-scan": -0.06,
                "fire-control": -0.08,
            }.get(track_mode, 0.0)
            miss_chance = min(
                0.78,
                max(
                    0.02,
                    terrain_shadow
                    + effective_jamming * 0.16
                    + map_profile.clutter * 0.08
                    + radiation_noise
                    + scan_penalty
                    + height_edge_penalty
                    + low_altitude_penalty
                    + (1.0 - range_margin) * 0.10
                    + mode_miss_adjust
                    - precision_bonus,
                ),
            )
            if self.is_burn_through_active:
                miss_chance *= 0.45
            if self.rng.random() < miss_chance:
                continue

            mode_noise = {
                "bearing-only": 4.0,
                "height-only": 3.2,
                "early-warning": 2.6,
                "search-cue": 2.0,
                "ballistic-only": 1.9,
                "surveillance-track": 1.25,
                "track-while-scan": 0.90,
                "fire-control": 0.62,
                "weapon-locating": 0.82,
            }.get(track_mode, 1.0)
            noise = radar.noise * (3.0 / projectile.profile.radar_cross_section) * mode_noise
            precision_factor = max(0.35, 1.28 - radar.tracking_precision * 0.22)
            band_precision = 0.84 if "j-band" in radar.band.lower() or "x/" in radar.band.lower() or "x-band" in radar.band.lower() else 1.0
            noise *= precision_factor * band_precision
            noise *= 1.0 + map_profile.clutter + effective_jamming * 2.6 + radiation_noise * 2.0
            observed = Vector2(
                projectile.position.x + self.rng.uniform(-noise, noise),
                projectile.position.y + self.rng.uniform(-noise, noise),
            )
            if track_mode == "bearing-only":
                bearing = _bearing_between(radar_position, projectile.position)
                noisy_bearing = bearing + self.rng.uniform(-10.0, 10.0)
                approximate_range = distance * self.rng.uniform(0.72, 1.28)
                radians = noisy_bearing * pi / 180.0
                observed = radar_position + Vector2(cos(radians), sin(radians)) * approximate_range
            height_noise = noise * max(18.0, 150.0 / radar.height_accuracy)
            if radar.scan_pattern == "fixed_lobe":
                height_noise *= 2.4
            elif radar.scan_pattern == "height_finder":
                height_noise *= 0.42
            observed_altitude = max(0.0, projectile.altitude + self.rng.uniform(-height_noise, height_noise))
            engageable = self.radar_track_engageable(radar, projectile.profile.role)
            track = self.tracker.update(Observation(projectile.projectile_id, observed, self.time, observed_altitude, radar.name, track_mode, engageable))
            if not engageable:
                track.confidence = min(track.confidence, 0.54 if track_mode in {"early-warning", "search-cue"} else 0.42)
            track.confidence = min(track.confidence, max(0.18, track_quality + range_margin * 0.16))
            if effective_jamming > 0:
                track.confidence = max(0.05, track.confidence - min(0.45, effective_jamming * 0.15))
            if self.is_burn_through_active:
                track.confidence = min(1.0, track.confidence + 0.18)
            if radar.category in {"engagement", "fire-control", "ballistic-defense"}:
                track.confidence = min(1.0, track.confidence + 0.04)
            if radar.height_accuracy > 1.35:
                track.confidence = min(1.0, track.confidence + 0.03)
        self._scan_enemy_tracks(sources, map_profile, radiation_noise)
        for track in tuple(self.tracker.tracks):
            if track.projectile_id in self.ghost_track_ids or track.projectile_id in covered_projectile_ids:
                continue
            if track.projectile_id in self.projectiles:
                self.tracker.remove(track.projectile_id)

    def _scan_enemy_tracks(
        self,
        sources: tuple[tuple[RadarProfile, Vector2, int, float], ...],
        map_profile: MapProfile,
        radiation_noise: float,
    ) -> None:
        for enemy in self.enemies.values():
            if not enemy.active:
                continue
            coverage_sources = [
                source
                for source in sources
                if self.radar_source_covers_position(
                    source[0],
                    source[1],
                    source[2],
                    source[3],
                    enemy.position,
                    radar_cross_section=enemy.profile.signature,
                    altitude=enemy.altitude,
                    target_role=enemy.profile.platform,
                    terrain_following=enemy.profile.platform == "ground",
                    emitter=enemy.profile.jammer_strength > 0,
                )
                and self._enemy_source_signature_visible(enemy, source[0])
            ]
            if not coverage_sources:
                continue
            candidate_sources = [
                source
                for source in coverage_sources
                if self.radar_source_detects_position_now(
                    source[0],
                    source[1],
                    source[2],
                    source[3],
                    enemy.position,
                    radar_cross_section=enemy.profile.signature,
                    altitude=enemy.altitude,
                    target_role=enemy.profile.platform,
                    terrain_following=enemy.profile.platform == "ground",
                    emitter=enemy.profile.jammer_strength > 0,
                )
            ]
            if not candidate_sources:
                continue
            source = max(
                candidate_sources,
                key=lambda item: self._target_adjusted_radar_range(
                    item[0],
                    item[2],
                    item[1],
                    enemy.position,
                    radar_cross_section=enemy.profile.signature,
                    altitude=enemy.altitude,
                    target_role=enemy.profile.platform,
                    terrain_following=enemy.profile.platform == "ground",
                    emitter=enemy.profile.jammer_strength > 0,
                )
                - enemy.position.distance_to(item[1]),
            )
            self._observe_enemy_track(enemy, source, map_profile, radiation_noise)

    def _observe_enemy_track(
        self,
        enemy: Enemy,
        source: tuple[RadarProfile, Vector2, int, float],
        map_profile: MapProfile,
        radiation_noise: float,
    ) -> None:
        radar, radar_position, health, _bearing = source
        track_mode = self.radar_track_mode(radar, enemy.profile.platform)
        effective_range = self._target_adjusted_radar_range(
            radar,
            health,
            radar_position,
            enemy.position,
            radar_cross_section=enemy.profile.signature,
            altitude=enemy.altitude,
            target_role=enemy.profile.platform,
            terrain_following=enemy.profile.platform == "ground",
            emitter=enemy.profile.jammer_strength > 0,
        )
        distance = enemy.position.distance_to(radar_position)
        jamming = self.jamming_level_at(enemy.position)
        effective_jamming = max(0.0, jamming * (1.0 - radar.jamming_resistance * 0.72))
        terrain_shadow = map_profile.terrain_shadow * (1.0 - radar.terrain_resistance)
        if enemy.profile.platform == "ground":
            terrain_shadow += map_profile.clutter * 0.18 + map_profile.terrain_shadow * 0.14
        elevation_angle = degrees(atan2(enemy.altitude, max(distance, 1.0)))
        elevation_limit = radar.elevation_coverage + radar.beam_width
        if track_mode in {"early-warning", "search-cue"}:
            elevation_limit += radar.beam_width * 1.2
        elif track_mode in {"track-while-scan", "fire-control"}:
            elevation_limit += radar.beam_width * 0.55
        if elevation_angle > elevation_limit:
            return
        height_edge_penalty = max(0.0, elevation_angle - radar.elevation_coverage * 0.82) * 0.010
        if enemy.profile.platform == "ground":
            low_altitude_penalty = max(0.0, 1.12 - radar.low_altitude_factor) * 0.24
        elif enemy.altitude < 220.0:
            low_altitude_penalty = max(0.0, 1.08 - radar.low_altitude_factor) * 0.18
        else:
            low_altitude_penalty = 0.0
        signature_penalty = max(0.0, 0.78 - enemy.profile.signature) * 0.20
        if self.time < enemy.revealed_until:
            signature_penalty *= 0.25
        scan_penalty = max(0.0, 1.0 - radar.scan_rate) * 0.13
        if track_mode in {"track-while-scan", "fire-control"}:
            scan_penalty *= 0.35
        track_quality = self.radar_track_quality(radar, enemy.profile.platform)
        range_margin = max(0.0, min(1.0, (effective_range - distance) / max(effective_range, 1.0)))
        mode_miss_adjust = {
            "bearing-only": 0.12,
            "height-only": 0.16,
            "early-warning": 0.03,
            "search-cue": 0.02,
            "ballistic-only": 0.10,
            "surveillance-track": -0.02,
            "weapon-locating": 0.04,
            "track-while-scan": -0.05,
            "fire-control": -0.08,
        }.get(track_mode, 0.0)
        miss_chance = min(
            0.82,
            max(
                0.02,
                terrain_shadow
                + effective_jamming * 0.17
                + map_profile.clutter * 0.07
                + radiation_noise
                + scan_penalty
                + height_edge_penalty
                + low_altitude_penalty
                + signature_penalty
                + (1.0 - range_margin) * 0.10
                + mode_miss_adjust
                - max(0.0, radar.tracking_precision - 1.0) * 0.07,
            ),
        )
        if self.is_burn_through_active:
            miss_chance *= 0.48
        if self.rng.random() < miss_chance:
            return

        mode_noise = {
            "bearing-only": 5.0,
            "height-only": 4.2,
            "early-warning": 3.0,
            "search-cue": 2.3,
            "ballistic-only": 2.4,
            "surveillance-track": 1.35,
            "weapon-locating": 1.6,
            "track-while-scan": 0.95,
            "fire-control": 0.66,
        }.get(track_mode, 1.4)
        noise = radar.noise * (4.0 / max(0.22, enemy.profile.signature)) * mode_noise
        precision_factor = max(0.35, 1.30 - radar.tracking_precision * 0.22)
        band_precision = 0.84 if "j-band" in radar.band.lower() or "x/" in radar.band.lower() or "x-band" in radar.band.lower() else 1.0
        if enemy.profile.platform == "ground":
            noise *= 1.28
        noise *= precision_factor * band_precision
        noise *= 1.0 + map_profile.clutter + effective_jamming * 2.2 + radiation_noise * 1.7
        observed = Vector2(
            enemy.position.x + self.rng.uniform(-noise, noise),
            enemy.position.y + self.rng.uniform(-noise, noise),
        )
        if track_mode == "bearing-only":
            bearing = _bearing_between(radar_position, enemy.position)
            noisy_bearing = bearing + self.rng.uniform(-12.0, 12.0)
            approximate_range = distance * self.rng.uniform(0.70, 1.30)
            radians = noisy_bearing * pi / 180.0
            observed = radar_position + Vector2(cos(radians), sin(radians)) * approximate_range
        height_noise = noise * max(12.0, 115.0 / radar.height_accuracy)
        if enemy.profile.platform == "ground":
            height_noise *= 0.20
        elif radar.scan_pattern == "height_finder":
            height_noise *= 0.45
        observed_altitude = max(0.0, enemy.altitude + self.rng.uniform(-height_noise, height_noise))
        engageable = self.radar_track_engageable(radar, enemy.profile.platform)
        track = self._update_enemy_track(
            enemy,
            observed,
            observed_altitude,
            radar.name,
            track_mode,
            engageable,
            revealed=self.time < enemy.revealed_until,
            jamming=effective_jamming,
        )
        if not engageable:
            track.confidence = min(track.confidence, 0.54 if track_mode in {"early-warning", "search-cue"} else 0.42)
        track.confidence = min(track.confidence, max(0.16, track_quality + range_margin * 0.15))
        if effective_jamming > 0:
            track.confidence = max(0.05, track.confidence - min(0.42, effective_jamming * 0.14))
        if self.is_burn_through_active:
            track.confidence = min(1.0, track.confidence + 0.16)
        if radar.category in {"engagement", "fire-control", "ballistic-defense", "long-range 3D"}:
            track.confidence = min(1.0, track.confidence + 0.03)

    def _update_enemy_track(
        self,
        enemy: Enemy,
        observed: Vector2,
        observed_altitude: float,
        source_name: str,
        track_mode: str,
        engageable: bool,
        *,
        revealed: bool,
        jamming: float,
    ) -> EnemyTrack:
        track = self.enemy_tracks.get(enemy.enemy_id)
        if track is None:
            track = EnemyTrack(
                enemy_id=enemy.enemy_id,
                position=observed,
                altitude=observed_altitude,
                last_timestamp=self.time,
                source_name=source_name,
                track_mode=track_mode,
                engageable=engageable,
                target_role=enemy.profile.platform,
                revealed=revealed,
                jamming=jamming,
            )
            self.enemy_tracks[enemy.enemy_id] = track
            return track

        dt = self.time - track.last_timestamp
        if dt <= 0:
            track.position = observed
            track.altitude = observed_altitude
            track.source_name = source_name
            track.track_mode = track_mode
            track.engageable = engageable
            track.target_role = enemy.profile.platform
            track.revealed = revealed
            track.jamming = jamming
            return track

        measured_velocity = (observed - track.position) / dt
        measured_vertical_velocity = (observed_altitude - track.altitude) / dt
        smoothing = 0.42 if engageable else 0.30
        if track.target_role == "ground":
            smoothing *= 0.80
        track.velocity = track.velocity * (1.0 - smoothing) + measured_velocity * smoothing
        track.vertical_velocity = track.vertical_velocity * (1.0 - smoothing) + measured_vertical_velocity * smoothing
        track.position = observed
        track.altitude = observed_altitude
        track.last_timestamp = self.time
        track.samples += 1
        track.source_name = source_name
        track.track_mode = track_mode
        track.engageable = engageable
        track.target_role = enemy.profile.platform
        track.revealed = revealed
        track.jamming = jamming
        track.confidence = min(1.0, track.confidence + (0.14 if engageable else 0.08))
        return track

    def _prune_enemy_tracks(self) -> None:
        stale_ids = [
            enemy_id
            for enemy_id, track in self.enemy_tracks.items()
            if enemy_id not in self.enemies or self.time - track.last_timestamp > self._enemy_track_stale_after(track)
        ]
        for enemy_id in stale_ids:
            del self.enemy_tracks[enemy_id]

    def _maybe_create_ghost_track(self) -> None:
        if not self.radar_alive or self.is_eccm_active or self.is_burn_through_active or self.time < self.next_ghost_at:
            return
        jammers = [enemy for enemy in self.enemies.values() if enemy.active and enemy.profile.ghost_rate > 0]
        if not jammers:
            return

        jammer = self.rng.choice(jammers)
        total_rate = sum(enemy.profile.ghost_rate for enemy in jammers)
        offset = Vector2(self.rng.uniform(-90, 90), self.rng.uniform(-90, 90))
        ghost_position = (jammer.position + offset).clamp(-WORLD_HALF_SIZE, WORLD_HALF_SIZE, -WORLD_HALF_SIZE, WORLD_HALF_SIZE)
        ghost_id = next(self._ghost_ids)
        self.ghost_track_ids.add(ghost_id)
        ghost_altitude = self.rng.uniform(80.0, 3200.0)
        track = self.tracker.update(Observation(ghost_id, ghost_position, self.time, ghost_altitude))
        track.velocity = Vector2(self.rng.uniform(-35, 35), self.rng.uniform(-35, 35))
        track.vertical_velocity = self.rng.uniform(-120, 120)
        track.confidence = 0.14
        self.next_ghost_at = self.time + max(1.2, 4.6 / (1.0 + total_rate + self.current_map.clutter))
        self.events.append("EW created a ghost track")

    def _cleanup_stale_ghosts(self) -> None:
        active_track_ids = {track.projectile_id for track in self.tracker.tracks}
        self.ghost_track_ids.intersection_update(active_track_ids)

    def _cleanup_field_effects(self) -> None:
        self.field_effects = [effect for effect in self.field_effects if self.time < effect.until]

    def best_intercept_for(
        self,
        projectile_id: int,
        interceptor_profile_name: str = "Iron Dome Tamir",
        *,
        speed_override: float | None = None,
    ) -> InterceptSolution | None:
        track = next((item for item in self.tracker.tracks if item.projectile_id == projectile_id), None)
        if track is None:
            return None
        if not track.engageable or track.confidence < 0.20:
            return None
        profile = INTERCEPTOR_PROFILES[interceptor_profile_name]
        return solve_intercept(
            self.base_position,
            track.position,
            track.velocity,
            speed_override or profile.speed,
            max_time=20.0,
        )

    def _radar_link_text(self) -> str:
        profiles = [self.current_radar]
        profiles.extend(site.profile for site in self.radar_sites.values() if site.active and site.health > 0)
        return " ".join(
            " ".join(
                (
                    profile.name,
                    profile.sensor_type,
                    profile.band,
                    profile.category,
                    profile.scan_pattern,
                    " ".join(profile.abilities),
                )
            )
            for profile in profiles
        ).lower()

    def _defense_compatible_with_current_radar(self, profile: InterceptorProfile) -> bool:
        if self.game_mode != "linked_defense":
            return True
        if not self.radar_alive:
            self.events.append("Linked defense blocked: no operational radar source")
            return False
        radar_text = self._radar_link_text()
        tokens = profile.compatible_radars
        if tokens:
            if any(token.lower() in radar_text for token in tokens):
                return True
            self.events.append(f"{profile.name} cannot link to {self.current_radar.name}")
            return False
        if profile.category == "gun" and any(token in radar_text for token in ("fire-control", "counter-battery", "tracking")):
            return True
        if profile.category == "missile" and any(token in radar_text for token in ("engagement", "3d", "pesa", "aesa", "guidance")):
            return True
        if profile.category == "directed-energy" and any(token in radar_text for token in ("aesa", "digital", "glass")):
            return True
        self.events.append(f"{profile.name} cannot link to {self.current_radar.name}")
        return False

    def deploy_interceptor(
        self,
        projectile_id: int,
        interceptor_profile_name: str = "Iron Dome Tamir",
        *,
        speed_override: float | None = None,
        ignore_inventory: bool = False,
    ) -> Interceptor | None:
        if projectile_id in self.ghost_track_ids:
            self.events.append("Interceptor ignored ghost track")
            return None
        profile = INTERCEPTOR_PROFILES[interceptor_profile_name]
        if not self._defense_compatible_with_current_radar(profile):
            return None
        if not ignore_inventory and not self._consume_defense(profile):
            return None
        solution = self.best_intercept_for(projectile_id, interceptor_profile_name, speed_override=speed_override)
        if solution is None:
            if not ignore_inventory:
                self.defense_inventory[profile.name] += 1
            return None

        interceptor = Interceptor(
            interceptor_id=next(self._interceptor_ids),
            profile=profile,
            target_kind="projectile",
            target_id=projectile_id,
            position=self.base_position,
            velocity=solution.interceptor_velocity,
            intercept_point=solution.point,
            time_remaining=solution.time,
        )
        self.interceptors[interceptor.interceptor_id] = interceptor
        return interceptor

    def best_enemy_intercept_for(
        self,
        enemy_id: int,
        interceptor_profile_name: str = "Iron Dome Tamir",
        *,
        speed_override: float | None = None,
    ) -> InterceptSolution | None:
        enemy = self.enemies.get(enemy_id)
        track = self.enemy_track_for(enemy_id, require_engageable=True)
        if enemy is None or track is None:
            return None
        profile = INTERCEPTOR_PROFILES[interceptor_profile_name]
        return solve_intercept(
            self.base_position,
            track.predict(self.time),
            track.velocity,
            speed_override or profile.speed,
            max_time=20.0,
        )

    def deploy_interceptor_at_enemy(
        self,
        enemy_id: int,
        interceptor_profile_name: str = "Iron Dome Tamir",
        *,
        speed_override: float | None = None,
    ) -> Interceptor | None:
        profile = INTERCEPTOR_PROFILES[interceptor_profile_name]
        if not self._defense_compatible_with_current_radar(profile):
            return None
        if not self._consume_defense(profile):
            return None
        solution = self.best_enemy_intercept_for(enemy_id, interceptor_profile_name, speed_override=speed_override)
        if solution is None:
            self.defense_inventory[profile.name] += 1
            self.events.append("No weapon-quality enemy track")
            return None

        interceptor = Interceptor(
            interceptor_id=next(self._interceptor_ids),
            profile=profile,
            target_kind="enemy",
            target_id=enemy_id,
            position=self.base_position,
            velocity=solution.interceptor_velocity,
            intercept_point=solution.point,
            time_remaining=solution.time,
        )
        self.interceptors[interceptor.interceptor_id] = interceptor
        return interceptor

    def _consume_defense(self, profile: InterceptorProfile) -> bool:
        if self.defense_inventory.get(profile.name, 0) <= 0:
            self.events.append(f"{profile.name} out of ammo")
            return False
        if self.game_mode in {"budget_waves", "linked_defense"} and self.budget_points < profile.cost:
            self.events.append(f"Need {profile.cost} points for {profile.name}")
            return False
        if self.ew_power < profile.power_cost:
            self.events.append(f"Need {profile.power_cost:.1f} EW power for {profile.name}")
            return False
        self.defense_inventory[profile.name] -= 1
        self.ew_power -= profile.power_cost
        if self.game_mode in {"budget_waves", "linked_defense"}:
            self.budget_points -= profile.cost
        return True

    def consume_events(self) -> tuple[str, ...]:
        events = tuple(self.events)
        self.events.clear()
        return events

    def _steer_player_projectile(self, projectile: Projectile, dt: float) -> None:
        if self.player_control.magnitude() == 0:
            return
        current = projectile.velocity.normalized()
        desired = self.player_control.normalized()
        blend = min(1.0, max(0.16, projectile.profile.turn_rate) * dt * 3.0)
        new_direction = (current * (1.0 - blend) + desired * blend).normalized()
        projectile.velocity = new_direction * projectile.profile.speed

    def _edge_position(self) -> Vector2:
        angle = self.rng.uniform(0, 2 * pi)
        return Vector2(cos(angle), sin(angle)) * WORLD_HALF_SIZE
