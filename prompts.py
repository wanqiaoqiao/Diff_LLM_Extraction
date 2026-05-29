ARTICLE_EXTRACTION_SYSTEM_PROMPT = """You extract stepwise stem-cell differentiation protocols from articles.

Return JSON only.

Your job:
- Read the article text.
- Decide if it is relevant to the requested target cell type.
- Extract the starting state, all intermediate cell states, the final state, stage timing, basal medium, factors, concentrations, markers, and short evidence sentences.
- Be conservative and avoid guessing.

Rules:
- Only include protocol-relevant content.
- Preserve original time windows when possible.
- Leave fields empty if not explicit.
- Include notes on uncertainty and any branch-specific protocol logic.
"""

INITIAL_SYNTHESIS_SYSTEM_PROMPT = """You are the first synthesis agent.

Return JSON only and follow the schema exactly.

Task:
- Use the academic article extractions as the primary evidence layer.
- Use commercial/public method signals as a secondary evidence layer.
- Propose an initial anchor protocol and initial DOE.
- Be practical, but do not overclaim certainty.

Rules:
- You may use commercial/public signals to bias the anchor protocol toward manufacturable and scalable modules.
- Do not automatically place proprietary or under-described commercial factors into DOE Round 1.
- If the literature is heterogeneous, say so.
- Keep the first version useful even if it still contains unresolved conflicts.
"""

REVIEW_SYSTEM_PROMPT = """You are the second review agent.

Return JSON only and follow the schema exactly.

Task:
- Review the initial anchor protocol and DOE critically.
- Judge whether the synthesis is scientifically coherent, procedurally sensible, and aligned with the supplied article evidence.
- Identify weaknesses, route-mixing errors, inappropriate DOE factors, and commercial-method overreach.
- Provide concrete revision instructions for the first agent.

Rules:
- Prioritize findings about scientific validity and experimental interpretability.
- Be explicit when protocol families are being inappropriately merged.
- Distinguish anchor-protocol critique from DOE critique.
- Recommend how the final V2 should structure conflicts, factor roles, and go/no-go criteria.
"""

DOE_SYNTHESIS_SYSTEM_PROMPT_V2 = """You are the first synthesis agent revising your initial output after expert critique.

Return JSON only and follow the schema exactly.

Your job:
- Build a scientifically defensible V2 synthesis for the requested target cell type.
- Use academic article extractions as the primary evidence layer.
- Use commercial/public method signals as a separate evidence layer.
- Use the review-agent critique to correct weaknesses in the initial version.
- Preserve the logic, exclusions, and conflicts behind the synthesis.

Critical method policy:
1. Before proposing any anchor protocol or DOE, cluster the articles into protocol families.
2. Identify the dominant family, or explicitly declare multiple branches if the evidence is heterogeneous.
3. Do not merge incompatible protocol families into one anchor unless you explicitly justify the merge.
4. For each factor, assign exactly one role:
   anchor_core, anchor_optional, doe_screen, defer_to_round2, commercial_anchor_only, or exclude.
5. A factor may enter DOE Round 1 only if it is explicit, controllable, and supported by repeat academic evidence, or by one academic source plus one explicit public commercial source.
6. Proprietary, under-described, kit-only, or closed-formulation factors must not enter DOE Round 1.
7. Commercial/public method signals may bias anchor protocol selection toward manufacturable, scalable, feeder-free, or clinically practical modules, but they must be tracked separately from academic evidence.
8. For every stage and factor, report supporting article IDs, support count, and evidence basis.
9. Report conflicts, exclusions, assumptions, and response to critique explicitly.
10. If evidence is heterogeneous, output branch-specific anchors and branch-specific DOE options instead of forcing one false consensus.

Anchor protocol logic:
- Prefer manufacturable, reproducible, and publicly repeated stage modules.
- Prefer stages and handoff windows that commercial/public programs repeatedly expose.
- Commercial/public signals may increase anchor priority even if they are not DOE-eligible.

DOE logic:
- Prefer explicit, interpretable, factor-level variables.
- Deprioritize proprietary or under-described commercial factors.
- Round 1 DOE should focus on academic-repeatable variables only.
"""

ARTICLE_EXTRACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "relevant": {"type": "boolean"},
        "article_title": {"type": "string"},
        "starting_cell_type": {"type": "string"},
        "final_cell_type": {"type": "string"},
        "protocol_scope": {"type": "string"},
        "stages": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "stage_label": {"type": "string"},
                    "start_day": {"type": ["number", "null"]},
                    "end_day": {"type": ["number", "null"]},
                    "time_range_text": {"type": "string"},
                    "cell_state": {"type": "string"},
                    "basal_medium": {"type": "string"},
                    "factors": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "name": {"type": "string"},
                                "concentration": {"type": "string"},
                            },
                            "required": ["name", "concentration"],
                        },
                    },
                    "markers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "name": {"type": "string"},
                                "expression": {"type": "string"},
                            },
                            "required": ["name", "expression"],
                        },
                    },
                    "evidence_sentences": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "stage_label",
                    "start_day",
                    "end_day",
                    "time_range_text",
                    "cell_state",
                    "basal_medium",
                    "factors",
                    "markers",
                    "evidence_sentences",
                ],
            },
        },
        "notes": {"type": "string"},
    },
    "required": [
        "relevant",
        "article_title",
        "starting_cell_type",
        "final_cell_type",
        "protocol_scope",
        "stages",
        "notes",
    ],
}

INITIAL_SYNTHESIS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "target_cell_type": {"type": "string"},
        "consensus_stage_map": {"type": "array", "items": {"type": "object"}},
        "recommended_anchor_protocol": {"type": "array", "items": {"type": "object"}},
        "doe": {"type": "object"},
        "logic_and_basis": {"type": "object"},
        "commercial_method_influence": {"type": "object"},
    },
    "required": [
        "target_cell_type",
        "consensus_stage_map",
        "recommended_anchor_protocol",
        "doe",
        "logic_and_basis",
        "commercial_method_influence",
    ],
}

REVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "overall_judgment": {"type": "string"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "severity": {"type": "string"},
                    "category": {"type": "string"},
                    "issue": {"type": "string"},
                    "why_it_matters": {"type": "string"},
                    "fix": {"type": "string"},
                },
                "required": ["severity", "category", "issue", "why_it_matters", "fix"],
            },
        },
        "anchor_protocol_critique": {"type": "array", "items": {"type": "string"}},
        "doe_critique": {"type": "array", "items": {"type": "string"}},
        "commercial_signal_critique": {"type": "array", "items": {"type": "string"}},
        "required_v2_changes": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "overall_judgment",
        "findings",
        "anchor_protocol_critique",
        "doe_critique",
        "commercial_signal_critique",
        "required_v2_changes",
    ],
}

DOE_SYNTHESIS_SCHEMA_V2 = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "target_cell_type": {"type": "string"},
        "protocol_families": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "family_id": {"type": "string"},
                    "family_name": {"type": "string"},
                    "article_ids": {"type": "array", "items": {"type": "string"}},
                    "dominant": {"type": "boolean"},
                    "why_grouped": {"type": "string"},
                },
                "required": ["family_id", "family_name", "article_ids", "dominant", "why_grouped"],
            },
        },
        "selected_strategy": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "mode": {"type": "string"},
                "family_id": {"type": "string"},
                "why_selected": {"type": "string"},
            },
            "required": ["mode", "family_id", "why_selected"],
        },
        "article_decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "article_id": {"type": "string"},
                    "title": {"type": "string"},
                    "decision": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["article_id", "title", "decision", "reason"],
            },
        },
        "consensus_stage_map": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "stage_name": {"type": "string"},
                    "time_range": {"type": "string"},
                    "cell_state_summary": {"type": "string"},
                    "basal_media": {"type": "array", "items": {"type": "string"}},
                    "factor_ranges": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "factor_name": {"type": "string"},
                                "concentration_range": {"type": "string"},
                                "role": {"type": "string"},
                                "support_count": {"type": "integer"},
                                "supporting_article_ids": {"type": "array", "items": {"type": "string"}},
                                "support_types": {"type": "array", "items": {"type": "string"}},
                                "rationale": {"type": "string"},
                            },
                            "required": [
                                "factor_name",
                                "concentration_range",
                                "role",
                                "support_count",
                                "supporting_article_ids",
                                "support_types",
                                "rationale",
                            ],
                        },
                    },
                },
                "required": ["stage_name", "time_range", "cell_state_summary", "basal_media", "factor_ranges"],
            },
        },
        "anchor_protocol_v2": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "stages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "stage_name": {"type": "string"},
                            "time_range": {"type": "string"},
                            "cell_state": {"type": "string"},
                            "basal_medium": {"type": "string"},
                            "factors": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "name": {"type": "string"},
                                        "concentration": {"type": "string"},
                                        "role": {"type": "string"},
                                        "support_count": {"type": "integer"},
                                        "supporting_article_ids": {"type": "array", "items": {"type": "string"}},
                                        "support_types": {"type": "array", "items": {"type": "string"}},
                                        "why_selected": {"type": "string"},
                                    },
                                    "required": [
                                        "name",
                                        "concentration",
                                        "role",
                                        "support_count",
                                        "supporting_article_ids",
                                        "support_types",
                                        "why_selected",
                                    ],
                                },
                            },
                            "go_no_go": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "positive_markers": {"type": "array", "items": {"type": "string"}},
                                    "negative_markers": {"type": "array", "items": {"type": "string"}},
                                    "decision_rule": {"type": "string"},
                                },
                                "required": ["positive_markers", "negative_markers", "decision_rule"],
                            },
                        },
                        "required": ["stage_name", "time_range", "cell_state", "basal_medium", "factors", "go_no_go"],
                    },
                }
            },
            "required": ["stages"],
        },
        "doe_v2": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "round_1_objective": {"type": "string"},
                "doe_entry_rule": {"type": "string"},
                "screening_factors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "string"},
                            "stage": {"type": "string"},
                            "role": {"type": "string"},
                            "levels": {"type": "array", "items": {"type": "string"}},
                            "support_count": {"type": "integer"},
                            "supporting_article_ids": {"type": "array", "items": {"type": "string"}},
                            "why_in_doe": {"type": "string"},
                            "why_not_anchor_only": {"type": "string"},
                        },
                        "required": [
                            "name",
                            "stage",
                            "role",
                            "levels",
                            "support_count",
                            "supporting_article_ids",
                            "why_in_doe",
                            "why_not_anchor_only",
                        ],
                    },
                },
                "deferred_factors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "string"},
                            "role": {"type": "string"},
                            "why_deferred": {"type": "string"},
                        },
                        "required": ["name", "role", "why_deferred"],
                    },
                },
                "fixed_conditions": {"type": "array", "items": {"type": "string"}},
                "response_variables": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["round_1_objective", "doe_entry_rule", "screening_factors", "deferred_factors", "fixed_conditions", "response_variables"],
        },
        "commercial_method_influence": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "anchor_bias_rules": {"type": "array", "items": {"type": "string"}},
                "doe_deprioritization_rules": {"type": "array", "items": {"type": "string"}},
                "signals_used": {"type": "array", "items": {"type": "string"}},
                "anchor_bias_only": {"type": "array", "items": {"type": "string"}},
                "doe_exclusions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["anchor_bias_rules", "doe_deprioritization_rules", "signals_used", "anchor_bias_only", "doe_exclusions"],
        },
        "logic_and_basis": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "selection_logic": {"type": "string"},
                "aggregation_logic": {"type": "string"},
                "conflicts": {"type": "array", "items": {"type": "string"}},
                "assumptions": {"type": "array", "items": {"type": "string"}},
                "limitations": {"type": "array", "items": {"type": "string"}},
                "self_check": {"type": "array", "items": {"type": "string"}},
                "response_to_review": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["selection_logic", "aggregation_logic", "conflicts", "assumptions", "limitations", "self_check", "response_to_review"],
        },
    },
    "required": [
        "target_cell_type",
        "protocol_families",
        "selected_strategy",
        "article_decisions",
        "consensus_stage_map",
        "anchor_protocol_v2",
        "doe_v2",
        "commercial_method_influence",
        "logic_and_basis",
    ],
}
