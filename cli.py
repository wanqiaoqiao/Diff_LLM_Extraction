from __future__ import annotations

import argparse
from pathlib import Path

from .models import AnalysisConfig
from .pipeline import run_and_save


WORKFLOW_MODES = ["single-agent-v2", "multi-agent-review"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LLM-driven iPSC protocol DOE synthesis")
    parser.add_argument("--source", action="append", required=True, help="URL, PMCID, file path, or directory path. Repeatable.")
    parser.add_argument("--target-cell-type", required=True)
    parser.add_argument("--article-limit", type=int, default=10)
    parser.add_argument("--start-cell-type-hint", default="iPSC")
    parser.add_argument("--max-candidate-files", type=int, default=5000)
    parser.add_argument("--max-chars-per-article", type=int, default=22000)
    parser.add_argument("--openai-model", default="gpt-4.1-mini")
    parser.add_argument("--output-dir", default="./outputs")
    parser.add_argument("--stem", default=None)
    parser.add_argument("--workflow-mode", choices=WORKFLOW_MODES, default="single-agent-v2")
    parser.add_argument("--no-commercial-web-search", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = AnalysisConfig(
        sources=args.source,
        target_cell_type=args.target_cell_type,
        article_limit=args.article_limit,
        start_cell_type_hint=args.start_cell_type_hint,
        max_candidate_files=args.max_candidate_files,
        max_chars_per_article=args.max_chars_per_article,
        openai_model=args.openai_model,
        output_dir=Path(args.output_dir),
        include_commercial_web_search=not args.no_commercial_web_search,
        workflow_mode=args.workflow_mode,
    )
    json_path, txt_path = run_and_save(config, stem=args.stem)
    print(f"Saved JSON: {json_path}")
    print(f"Saved TXT: {txt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
