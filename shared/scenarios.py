"""Canned scenario data for reproducible demos.

Real fetches would hit weather APIs, GIS services, Strava, etc. For the tutorial
we hardcode three scenarios (HOT / NORMAL / COLD) selected via the
MARATHON_SCENARIO env var, with an optional MARATHON_SLOW_MO multiplier on the
simulated fetch latencies (handy on stage to stretch the parallel-pulse window).
"""
from __future__ import annotations

import os
from typing import Any

from .schemas import CourseData, FitnessData, WeatherData


SCENARIOS: dict[str, dict[str, Any]] = {
    "HOT": {
        "weather": WeatherData(
            temp_f=78, wind_mph=12, wind_direction="headwind",
            humidity_pct=70, conditions="sunny",
        ),
        "course": CourseData(
            name="Boston Marathon", distance_mi=26.2,
            total_elevation_gain_ft=815, hardest_mile=20,
            hardest_mile_grade_pct=4.5,
        ),
        "fitness": FitnessData(
            avg_pace_per_mile_sec=450,  # 7:30 / mile
            longest_recent_run_mi=22, weekly_mileage_mi=55,
        ),
    },
    "NORMAL": {
        "weather": WeatherData(
            temp_f=58, wind_mph=4, wind_direction="calm",
            humidity_pct=55, conditions="overcast",
        ),
        "course": CourseData(
            name="Berlin Marathon", distance_mi=26.2,
            total_elevation_gain_ft=240, hardest_mile=0,
            hardest_mile_grade_pct=0.5,
        ),
        "fitness": FitnessData(
            avg_pace_per_mile_sec=420,  # 7:00 / mile
            longest_recent_run_mi=24, weekly_mileage_mi=65,
        ),
    },
    "COLD": {
        "weather": WeatherData(
            temp_f=35, wind_mph=15, wind_direction="crosswind",
            humidity_pct=65, conditions="cloudy",
        ),
        "course": CourseData(
            name="Chicago Marathon", distance_mi=26.2,
            total_elevation_gain_ft=140, hardest_mile=0,
            hardest_mile_grade_pct=0.3,
        ),
        "fitness": FitnessData(
            avg_pace_per_mile_sec=440,  # 7:20 / mile
            longest_recent_run_mi=22, weekly_mileage_mi=60,
        ),
    },
}


def scenario() -> dict[str, Any]:
    """Return the currently selected scenario dict (HOT / NORMAL / COLD)."""
    name = os.environ.get("MARATHON_SCENARIO", "HOT").upper()
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario {name!r}; expected HOT/NORMAL/COLD")
    return SCENARIOS[name]


def slow_mo() -> float:
    """Multiplier on simulated fetch latencies (env var MARATHON_SLOW_MO)."""
    try:
        return float(os.environ.get("MARATHON_SLOW_MO", "1.0"))
    except ValueError:
        return 1.0
