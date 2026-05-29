from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class SourceSpec:
    value: str


@dataclass(slots=True)
class CandidateArticle:
    source: str
    resolved_source: str
    kind: str
    text: str
    title: str = ""
    pmcid: str | None = None
    academic_score: float = 0.0
    commercial_alignment_score: float = 0.0
    combined_score: float = 0.0


@dataclass(slots=True)
class CommercialMethodSignal:
    company: str
    program: str
    target_cell_type: str
    method_module: str
    details: str
    public_evidence_url: str
    confidence: str
    should_prioritize_in_anchor: bool = True
    should_deprioritize_in_doe: bool = True


@dataclass(slots=True)
class AnalysisConfig:
    sources: list[str]
    target_cell_type: str
    article_limit: int = 10
    start_cell_type_hint: str = "iPSC"
    max_candidate_files: int = 5000
    max_chars_per_article: int = 22000
    openai_model: str = "gpt-4.1-mini"
    output_dir: Path | None = None
    include_commercial_web_search: bool = True
    workflow_mode: str = "single-agent-v2"
    commercial_search_notes: str = (
        "Use commercial/public methods to influence the anchor protocol, but do not "
        "automatically promote proprietary or under-described supplements into the first DOE."
    )


@dataclass(slots=True)
class AnalysisArtifacts:
    candidates: list[CandidateArticle] = field(default_factory=list)
    commercial_signals: list[CommercialMethodSignal] = field(default_factory=list)
    article_extractions: list[dict[str, Any]] = field(default_factory=list)
    initial_summary: dict[str, Any] = field(default_factory=dict)
    review_summary: dict[str, Any] = field(default_factory=dict)
    doe_summary: dict[str, Any] = field(default_factory=dict)
