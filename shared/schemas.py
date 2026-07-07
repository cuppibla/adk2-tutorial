"""Pydantic schemas that flow between nodes in the marathon workflows.

Structured I/O is how ADK 2 keeps typed data moving between function nodes and
agents. An agent with `output_schema=RaceStrategy` is forced to emit valid JSON
for that model; a function node downstream receives it as a typed object.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ─── Pillar 1 (graph workflow) ────────────────────────────────────────────────

class WeatherData(BaseModel):
    temp_f: float
    wind_mph: float
    wind_direction: str
    humidity_pct: int
    conditions: str


class CourseData(BaseModel):
    name: str
    distance_mi: float
    total_elevation_gain_ft: int
    hardest_mile: int
    hardest_mile_grade_pct: float


class FitnessData(BaseModel):
    avg_pace_per_mile_sec: int
    longest_recent_run_mi: float
    weekly_mileage_mi: int


class RaceStrategy(BaseModel):
    target_finish: str = Field(
        description="Clean finish time only, format H:MM:SS. Example: '3:30:00'. "
        "Do NOT include explanations, parentheticals, or extra commentary."
    )
    pacing_advice: str = Field(description="One concise sentence about race pacing strategy.")
    fueling_plan: str = Field(description="One concise sentence about hydration and nutrition.")
    gear: str = Field(description="One concise sentence about clothing and equipment.")
    key_warning: str = Field(description="One concise sentence flagging the biggest risk for this race.")


class BundledRunData(BaseModel):
    """Shape of the JoinNode payload — keys match the upstream function names."""
    fetch_weather: WeatherData
    analyze_course: CourseData
    pull_fitness: FitnessData


# ─── Pillar 2 (collaborative agents) ──────────────────────────────────────────

class SpecialistInput(BaseModel):
    """Payload the concierge coordinator hands to each specialist subagent."""
    user_question: str = Field(description="The runner's free-form question.")
    current_strategy: RaceStrategy = Field(description="The strategy generated in L2.")
    runner_data: BundledRunData = Field(description="The original bundled weather/course/fitness data.")


class SpecialistResponse(BaseModel):
    """Structured response each specialist returns to the coordinator."""
    concern_level: Literal["none", "minor", "moderate", "serious"] = Field(
        description="Severity of the concern this specialist raises."
    )
    recommendation: str = Field(description="One concise sentence with the actionable recommendation.")
    reasoning: str = Field(description="One concise sentence with the why, referencing specific data.")


# ─── Pillar 3 (dynamic workflow) ──────────────────────────────────────────────

class DecomposerOutput(BaseModel):
    """Output of the decompose agent — the research plan."""
    plan_summary: str = Field(
        description="One sentence explaining how you decomposed the question."
    )
    sub_questions: list[str] = Field(
        description="3-7 specific, non-overlapping sub-questions that together "
                    "comprehensively answer the user's main question.",
        min_length=3,
        max_length=7,
    )


class ResearchFinding(BaseModel):
    """Output of one research agent invocation — findings on a single sub-question."""
    summary: str = Field(
        description="Concise 2-3 sentence summary of findings on this sub-question."
    )
    key_facts: list[str] = Field(
        description="3-5 specific factual points or actionable insights discovered.",
        min_length=2,
        max_length=5,
    )
    needs_deeper: bool = Field(
        description="True if these findings reveal a topic that warrants deeper "
                    "recursive investigation. Set False if the question is fully answered."
    )
    deeper_questions: list[str] = Field(
        default_factory=list,
        description="If needs_deeper is True, 1-3 specific, well-formed deeper "
                    "questions to investigate. Empty list if needs_deeper is False.",
        max_length=3,
    )


class DeepResearchBriefing(BaseModel):
    """Final synthesized output of the deep research workflow."""
    headline: str = Field(
        description="One-sentence headline summarizing the most important takeaway."
    )
    sections: list[str] = Field(
        description="3-6 thematic paragraphs covering the research areas.",
        min_length=3,
        max_length=6,
    )
    key_warnings: list[str] = Field(
        description="2-4 actionable warnings or critical considerations.",
        min_length=1,
        max_length=4,
    )
    summary: str = Field(
        description="Closing paragraph that ties everything together actionably."
    )
