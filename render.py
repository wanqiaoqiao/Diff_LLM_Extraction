from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _append_lines(lines: list[str], values: list[str]) -> None:
    for value in values:
        lines.append(f"- {value}")


def render_summary_txt(doe_summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"Title: {doe_summary.get('target_cell_type', 'Unknown')} DOE Summary")
    lines.append("")

    families = doe_summary.get("protocol_families", [])
    if families:
        lines.append("Protocol Families:")
        for family in families:
            lines.append(
                f"- {family.get('family_id', '')} | {family.get('family_name', '')} | "
                f"dominant={family.get('dominant', False)} | articles={', '.join(family.get('article_ids', []))}"
            )
            lines.append(f"  Why grouped: {family.get('why_grouped', '')}")
        lines.append("")

    selected = doe_summary.get("selected_strategy", {})
    if selected:
        lines.append("Selected Strategy:")
        lines.append(
            f"- mode={selected.get('mode', '')} | family={selected.get('family_id', '')} | why={selected.get('why_selected', '')}"
        )
        lines.append("")

    lines.append("Consensus Stage Map:")
    for stage in doe_summary.get("consensus_stage_map", []):
        lines.append(f"- {stage.get('stage_name', '')}: {stage.get('time_range', '')}")
        lines.append(f"  Cell state: {stage.get('cell_state_summary', '')}")
        media = "; ".join(stage.get("basal_media", []))
        if media:
            lines.append(f"  Basal media: {media}")
        for factor in stage.get("factor_ranges", []):
            lines.append(
                f"  Factor: {factor.get('factor_name', '')} | Range: {factor.get('concentration_range', '')} | "
                f"Role: {factor.get('role', '')} | Support: {factor.get('support_count', 0)}"
            )
            lines.append(f"  Evidence IDs: {', '.join(factor.get('supporting_article_ids', []))}")
            rationale = factor.get("rationale", "")
            if rationale:
                lines.append(f"  Why: {rationale}")
        lines.append("")

    anchor_v2 = doe_summary.get("anchor_protocol_v2", {})
    anchor_v1 = doe_summary.get("recommended_anchor_protocol", [])
    lines.append("Recommended Anchor Protocol:")
    if anchor_v2.get("stages"):
        for stage in anchor_v2.get("stages", []):
            lines.append(
                f"- {stage.get('stage_name', '')} | {stage.get('time_range', '')} | {stage.get('basal_medium', '')}"
            )
            lines.append(f"  Cell state: {stage.get('cell_state', '')}")
            for factor in stage.get("factors", []):
                lines.append(
                    f"  Factor: {factor.get('name', '')} | {factor.get('concentration', '')} | role={factor.get('role', '')}"
                )
                lines.append(f"  Why selected: {factor.get('why_selected', '')}")
            go_no_go = stage.get("go_no_go", {})
            if go_no_go:
                lines.append(f"  Go markers: {', '.join(go_no_go.get('positive_markers', []))}")
                lines.append(f"  Exclusion markers: {', '.join(go_no_go.get('negative_markers', []))}")
                lines.append(f"  Decision rule: {go_no_go.get('decision_rule', '')}")
    else:
        for stage in anchor_v1:
            lines.append(
                f"- {stage.get('stage_name', '')} | {stage.get('time_range', '')} | "
                f"{stage.get('basal_medium', '')} | Factors: {'; '.join(stage.get('factors', []))}"
            )
    lines.append("")

    doe = doe_summary.get("doe_v2", doe_summary.get("doe", {}))
    lines.append("DOE:")
    lines.append(f"Objective: {doe.get('round_1_objective', doe.get('objective', ''))}")
    if doe.get("doe_entry_rule"):
        lines.append(f"DOE entry rule: {doe.get('doe_entry_rule', '')}")
    lines.append("Response variables:")
    _append_lines(lines, doe.get("response_variables", []))
    lines.append("Screening factors:")
    for factor in doe.get("screening_factors", []):
        lines.append(
            f"- {factor.get('name', '')} | Stage: {factor.get('stage', '')} | Role: {factor.get('role', '')} | Levels: {', '.join(factor.get('levels', []))}"
        )
        if factor.get("why_in_doe"):
            lines.append(f"  Why in DOE: {factor.get('why_in_doe', '')}")
        if factor.get("why_not_anchor_only"):
            lines.append(f"  Why not anchor only: {factor.get('why_not_anchor_only', '')}")
        if factor.get("rationale"):
            lines.append(f"  Rationale: {factor.get('rationale', '')}")
    if doe.get("deferred_factors"):
        lines.append("Deferred factors:")
        for factor in doe.get("deferred_factors", []):
            lines.append(f"- {factor.get('name', '')} | role={factor.get('role', '')} | why={factor.get('why_deferred', '')}")
    lines.append("Fixed conditions:")
    _append_lines(lines, doe.get("fixed_conditions", []))
    if doe.get("deferred_modifiers"):
        lines.append("Deferred modifiers:")
        _append_lines(lines, doe.get("deferred_modifiers", []))
    lines.append("")

    logic = doe_summary.get("logic_and_basis", {})
    lines.append("Logic and Basis:")
    lines.append(f"Selection logic: {logic.get('selection_logic', '')}")
    lines.append(f"Aggregation logic: {logic.get('aggregation_logic', '')}")
    if logic.get("conflicts"):
        lines.append("Conflicts:")
        _append_lines(lines, logic.get("conflicts", []))
    if logic.get("assumptions"):
        lines.append("Assumptions:")
        _append_lines(lines, logic.get("assumptions", []))
    if logic.get("limitations"):
        lines.append("Limitations:")
        _append_lines(lines, logic.get("limitations", []))
    if logic.get("self_check"):
        lines.append("Self-check:")
        _append_lines(lines, logic.get("self_check", []))
    if logic.get("response_to_review"):
        lines.append("Response to review:")
        _append_lines(lines, logic.get("response_to_review", []))
    lines.append("")

    commercial = doe_summary.get("commercial_method_influence", {})
    if commercial:
        lines.append("Commercial Method Influence:")
        lines.append("Anchor bias rules:")
        _append_lines(lines, commercial.get("anchor_bias_rules", []))
        lines.append("DOE deprioritization rules:")
        _append_lines(lines, commercial.get("doe_deprioritization_rules", []))
        lines.append("Signals used:")
        _append_lines(lines, commercial.get("signals_used", []))
        if commercial.get("anchor_bias_only"):
            lines.append("Anchor bias only:")
            _append_lines(lines, commercial.get("anchor_bias_only", []))
        if commercial.get("doe_exclusions"):
            lines.append("DOE exclusions:")
            _append_lines(lines, commercial.get("doe_exclusions", []))

    return "\n".join(lines).strip() + "\n"


def render_bundle_txt(bundle: dict[str, Any]) -> str:
    lines: list[str] = []
    config = bundle.get("config", {})
    lines.append(f"Workflow mode: {config.get('workflow_mode', 'single-agent-v2')}")
    lines.append("")

    initial_summary = bundle.get("initial_summary", {})
    if initial_summary:
        lines.append("Initial Synthesis V1:")
        lines.append(f"- target: {initial_summary.get('target_cell_type', '')}")
        if initial_summary.get("logic_and_basis", {}).get("selection_logic"):
            lines.append(f"- selection logic: {initial_summary['logic_and_basis'].get('selection_logic', '')}")
        lines.append("")

    review_summary = bundle.get("review_summary", {})
    if review_summary:
        lines.append("Review Agent Critique:")
        lines.append(f"Overall judgment: {review_summary.get('overall_judgment', '')}")
        for finding in review_summary.get("findings", []):
            lines.append(
                f"- [{finding.get('severity', '')}] {finding.get('category', '')}: {finding.get('issue', '')}"
            )
            lines.append(f"  Why it matters: {finding.get('why_it_matters', '')}")
            lines.append(f"  Fix: {finding.get('fix', '')}")
        lines.append("")

    lines.append(render_summary_txt(bundle.get("doe_summary", {})).rstrip())
    return "\n".join(lines).strip() + "\n"


def save_outputs(output_dir: Path, stem: str, artifacts: dict[str, Any], txt: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{stem}.json"
    txt_path = output_dir / f"{stem}.txt"
    json_path.write_text(json.dumps(artifacts, ensure_ascii=False, indent=2), encoding="utf-8")
    txt_path.write_text(txt, encoding="utf-8")
    return json_path, txt_path
