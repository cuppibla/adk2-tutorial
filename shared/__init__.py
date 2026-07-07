"""Shared building blocks used across the ADK 2 orchestration levels (L2–L4).

L0 and L1 are intentionally self-contained (no imports from here) so the first
two rungs of the ladder have nothing extra to read. Everything from L2 onward
reuses these schemas and the canned marathon scenarios.
"""
from .schemas import (
    WeatherData,
    CourseData,
    FitnessData,
    RaceStrategy,
    BundledRunData,
    SpecialistInput,
    SpecialistResponse,
    DecomposerOutput,
    ResearchFinding,
    DeepResearchBriefing,
)
from .scenarios import SCENARIOS, scenario, slow_mo

__all__ = [
    "WeatherData",
    "CourseData",
    "FitnessData",
    "RaceStrategy",
    "BundledRunData",
    "SpecialistInput",
    "SpecialistResponse",
    "DecomposerOutput",
    "ResearchFinding",
    "DeepResearchBriefing",
    "SCENARIOS",
    "scenario",
    "slow_mo",
]
