from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .llm_client import LLMClient
from .models import AnalysisArtifacts, AnalysisConfig, CandidateArticle
from .prompts import (
    ARTICLE_EXTRACTION_SCHEMA,
    ARTICLE_EXTRACTION_SYSTEM_PROMPT,
    DOE_SYNTHESIS_SCHEMA_V2,
    DOE_SYNTHESIS_SYSTEM_PROMPT_V2,
    INITIAL_SYNTHESIS_SCHEMA,
    INITIAL_SYNTHESIS_SYSTEM_PROMPT,
    REVIEW_SCHEMA,
    REVIEW_SYSTEM_PROMPT,
)
from .render import render_bundle_txt, save_outputs
from .sources import expand_sources
from .web_search import (
    commercial_anchor_rules,
    commercial_doe_deprioritization_rules,
    infer_commercial_signals,
)


DOE_ENTRY_RULE = (
    "A factor may enter DOE Round 1 only if it is explicit, controllable, and supported by repeat academic evidence, "
    "or by one academic source plus one explicit public commercial source. Proprietary or under-described commercial-only factors must not enter DOE Round 1."
)


def _truncate(text: str, max_chars: int) -> str:
    return text if len(text) <= max_chars else text[:max_chars]


def _candidate_sort_key(candidate: CandidateArticle) -> tuple[float, float]:
    return (candidate.academic_score, len(candidate.text))


def _extract_article(llm: LLMClient, config: AnalysisConfig, candidate: CandidateArticle) -> dict[str, Any]:
    prompt = (
        f"Target cell type: {config.target_cell_type}\n"
        f"Starting cell hint: {config.start_cell_type_hint}\n"
        f"Source: {candidate.resolved_source}\n\n"
        "Read the following article text and extract the differentiation protocol as structured JSON.\n\n"
        f"{_truncate(candidate.text, config.max_chars_per_article)}"
    )
    result = llm.json_response(ARTICLE_EXTRACTION_SYSTEM_PROMPT, prompt, ARTICLE_EXTRACTION_SCHEMA)
    result["source"] = candidate.resolved_source
    result["pmcid"] = candidate.pmcid or ""
    result["academic_score"] = candidate.academic_score
    result["commercial_alignment_score"] = candidate.commercial_alignment_score
    return result


def _signal_dicts(config: AnalysisConfig, signals: list[Any]) -> dict[str, Any]:
    return {
        "notes": config.commercial_search_notes,
        "signals": [signal.__dict__ for signal in signals],
        "anchor_bias_rules": commercial_anchor_rules(),
        "doe_deprioritization_rules": commercial_doe_deprioritization_rules(),
        "doe_entry_rule": DOE_ENTRY_RULE,
    }


def _build_common_payload(config: AnalysisConfig, article_extractions: list[dict[str, Any]], signals: list[Any]) -> dict[str, Any]:
    relevant_articles = [a for a in article_extractions if a.get("relevant")]
    return {
        "target_cell_type": config.target_cell_type,
        "article_extractions": relevant_articles,
        "commercial_evidence_layer": _signal_dicts(config, signals),
        "required_rules": {
            "anchor_bias_rules": commercial_anchor_rules(),
            "doe_deprioritization_rules": commercial_doe_deprioritization_rules(),
            "doe_entry_rule": DOE_ENTRY_RULE,
            "article_decision_labels": [
                "included_for_anchor",
                "included_for_doe",
                "included_only_for_background",
                "excluded",
            ],
            "factor_role_labels": [
                "anchor_core",
                "anchor_optional",
                "doe_screen",
                "defer_to_round2",
                "commercial_anchor_only",
                "exclude",
            ],
        },
    }


def _synthesize_initial(
    llm: LLMClient,
    config: AnalysisConfig,
    article_extractions: list[dict[str, Any]],
    signals: list[Any],
) -> dict[str, Any]:
    payload = _build_common_payload(config, article_extractions, signals)
    payload["synthesis_stage"] = "initial_v1"
    return llm.json_response(
        INITIAL_SYNTHESIS_SYSTEM_PROMPT,
        json.dumps(payload, ensure_ascii=False, indent=2),
        INITIAL_SYNTHESIS_SCHEMA,
    )


def _review_initial(
    llm: LLMClient,
    config: AnalysisConfig,
    article_extractions: list[dict[str, Any]],
    signals: list[Any],
    initial_summary: dict[str, Any],
) -> dict[str, Any]:
    payload = _build_common_payload(config, article_extractions, signals)
    payload["initial_summary_v1"] = initial_summary
    payload["review_focus"] = [
        "scientific coherence",
        "protocol family mixing",
        "anchor-vs-DOE separation",
        "commercial method influence",
        "experimental interpretability",
    ]
    return llm.json_response(
        REVIEW_SYSTEM_PROMPT,
        json.dumps(payload, ensure_ascii=False, indent=2),
        REVIEW_SCHEMA,
    )


def _synthesize_doe_v2(
    llm: LLMClient,
    config: AnalysisConfig,
    article_extractions: list[dict[str, Any]],
    signals: list[Any],
    initial_summary: dict[str, Any] | None = None,
    review_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = _build_common_payload(config, article_extractions, signals)
    if initial_summary:
        payload["initial_summary_v1"] = initial_summary
    if review_summary:
        payload["review_agent_critique"] = review_summary
    payload["synthesis_stage"] = "final_v2"
    return llm.json_response(
        DOE_SYNTHESIS_SYSTEM_PROMPT_V2,
        json.dumps(payload, ensure_ascii=False, indent=2),
        DOE_SYNTHESIS_SCHEMA_V2,
    )


def run_analysis(config: AnalysisConfig) -> tuple[dict[str, Any], str, AnalysisArtifacts]:
    artifacts = AnalysisArtifacts()
    llm = LLMClient(model=config.openai_model)

    artifacts.candidates = expand_sources(config.sources, config.target_cell_type, config.max_candidate_files)
    artifacts.candidates.sort(key=_candidate_sort_key, reverse=True)

    if config.include_commercial_web_search:
        artifacts.commercial_signals = infer_commercial_signals(config.target_cell_type)

    chosen = artifacts.candidates[: config.article_limit]
    for candidate in chosen:
        artifacts.article_extractions.append(_extract_article(llm, config, candidate))

    if config.workflow_mode == "multi-agent-review":
        artifacts.initial_summary = _synthesize_initial(
            llm,
            config,
            artifacts.article_extractions,
            artifacts.commercial_signals,
        )
        artifacts.review_summary = _review_initial(
            llm,
            config,
            artifacts.article_extractions,
            artifacts.commercial_signals,
            artifacts.initial_summary,
        )
        artifacts.doe_summary = _synthesize_doe_v2(
            llm,
            config,
            artifacts.article_extractions,
            artifacts.commercial_signals,
            initial_summary=artifacts.initial_summary,
            review_summary=artifacts.review_summary,
        )
    else:
        artifacts.doe_summary = _synthesize_doe_v2(
            llm,
            config,
            artifacts.article_extractions,
            artifacts.commercial_signals,
        )

    bundle = {
        "config": config.__dict__ | {"output_dir": str(config.output_dir) if config.output_dir else None},
        "commercial_signals": [signal.__dict__ for signal in artifacts.commercial_signals],
        "candidates": [candidate.__dict__ for candidate in artifacts.candidates],
        "article_extractions": artifacts.article_extractions,
        "initial_summary": artifacts.initial_summary,
        "review_summary": artifacts.review_summary,
        "doe_summary": artifacts.doe_summary,
    }
    txt = render_bundle_txt(bundle)
    return artifacts.doe_summary, txt, artifacts


def run_and_save(config: AnalysisConfig, stem: str | None = None) -> tuple[Path, Path]:
    _, txt, artifacts = run_analysis(config)
    output_dir = config.output_dir or Path.cwd()
    stem = stem or config.target_cell_type.lower().replace(" ", "_") + "_doe"
    bundle = {
        "config": config.__dict__ | {"output_dir": str(config.output_dir) if config.output_dir else None},
        "commercial_signals": [signal.__dict__ for signal in artifacts.commercial_signals],
        "candidates": [candidate.__dict__ for candidate in artifacts.candidates],
        "article_extractions": artifacts.article_extractions,
        "initial_summary": artifacts.initial_summary,
        "review_summary": artifacts.review_summary,
        "doe_summary": artifacts.doe_summary,
    }
    return save_outputs(output_dir, stem, bundle, txt)
