#!/usr/bin/env python3
"""Create an isolated survey run directory.

Usage:
    python3 scripts/init_run.py --topic "EHR Foundation Model ..."

The script creates outputs/runs/<timestamp>-<topic-slug>/ and a convenience
symlink outputs/latest. It never deletes existing runs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def ascii_slug(text: str, max_words: int = 8, max_len: int = 90) -> str:
    words = re.findall(r"[A-Za-z0-9]+", text.lower())
    stop = {
        "the", "and", "for", "with", "about", "survey", "review", "paper",
        "please", "using", "on", "of", "in", "to", "a", "an", "model", "models",
        "study", "studies", "general", "high", "quality",
    }
    filtered = [w for w in words if w not in stop and len(w) > 1]
    if not filtered:
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
        return f"topic-{digest}"
    slug = "-".join(filtered[:max_words])
    slug = re.sub(r"-+", "-", slug).strip("-")[:max_len].strip("-")
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:6]
    return f"{slug}-{digest}"


def make_dirs(run_dir: Path) -> None:
    subdirs = [
        "searches/raw_results",
        "web",
        "evidence",
        "extractions",
        "drafts",
        "figures",
        "tex/figures",
        "refs",
        "reports",
        "logs",
        "assets",
    ]
    for sub in subdirs:
        (run_dir / sub).mkdir(parents=True, exist_ok=False)


def write_placeholders(run_dir: Path, topic: str, manifest: dict) -> None:
    (run_dir / "prompt.txt").write_text(topic + "\n", encoding="utf-8")
    (run_dir / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (run_dir / "logs" / "paperclip_commands.md").write_text(
        "# Paperclip command log\n\nAppend every Paperclip command, timestamp, handle, and output file here.\n",
        encoding="utf-8",
    )
    (run_dir / "logs" / "codex_worklog.md").write_text(
        "# Codex worklog\n\nRecord major decisions, subagent use, failures, and recovery steps here.\n",
        encoding="utf-8",
    )
    (run_dir / "reports" / "protocol.md").write_text(
        "# Survey protocol\n\nTo be completed before drafting.\n",
        encoding="utf-8",
    )
    (run_dir / "reports" / "figure_audit.md").write_text(
        "# Figure audit\n\nStatus: pending\n\nThe overview figure has not yet been audited.\n",
        encoding="utf-8",
    )
    (run_dir / "reports" / "limitations.md").write_text(
        "# Limitations\n\nDocument corpus, search, and workflow limitations here.\n",
        encoding="utf-8",
    )
    (run_dir / "web" / "web_search_log.md").write_text(
        "# Web search log\n\nRecord web-search queries, rationale, sources, and what was integrated.\n",
        encoding="utf-8",
    )
    (run_dir / "web" / "web_query_plan_round1.md").write_text(
        "# Web query plan round 1\n\nList broad and targeted web-search queries here.\n",
        encoding="utf-8",
    )
    (run_dir / "web" / "web_query_plan_round2.md").write_text(
        "# Web query plan round 2\n\nRecord gap-driven web-search queries here.\n",
        encoding="utf-8",
    )
    (run_dir / "web" / "integrated_search_summary.md").write_text(
        "# Integrated search summary\n\nSummarize how Paperclip and web search were combined.\n",
        encoding="utf-8",
    )
    (run_dir / "figures" / "overview_figure_prompt.md").write_text(
        "# Overview figure prompt\n\nRendering route: pending\n\nDescribe the intended figure purpose, content, and Codex image_gen prompt here. Use deterministic rendering only if image_gen cannot be invoked, and record the fallback reason.\n",
        encoding="utf-8",
    )
    (run_dir / "figures" / "overview_figure_spec.md").write_text(
        "# Overview figure spec\n\nDistill the manuscript into a figure claim, layout archetype, node list, edge list, and omission list before drawing.\n",
        encoding="utf-8",
    )
    (run_dir / "reports" / "figure_selection.md").write_text(
        "# Figure selection\n\nStatus: pending\n\nRendering route: pending\n\nGenerate at least two candidates with Codex image_gen first, compare them, and record why the final figure was selected. If deterministic rendering was used, record why image_gen could not be invoked.\n",
        encoding="utf-8",
    )


def update_latest(outputs_dir: Path, run_dir: Path) -> None:
    latest = outputs_dir / "latest"
    try:
        if latest.is_symlink() or latest.exists():
            latest.unlink()
        latest.symlink_to(run_dir.resolve())
    except OSError:
        (outputs_dir / "LATEST_RUN.txt").write_text(str(run_dir.resolve()) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True, help="Exact user topic or prompt")
    parser.add_argument("--outputs", default="outputs", help="Output root directory")
    args = parser.parse_args()

    root = Path.cwd()
    outputs_dir = root / args.outputs
    runs_dir = outputs_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now().astimezone()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    slug = ascii_slug(args.topic)
    run_id = f"{timestamp}-{slug}"
    run_dir = runs_dir / run_id

    suffix = 2
    base_run_dir = run_dir
    while run_dir.exists():
        run_dir = Path(f"{base_run_dir}-{suffix}")
        suffix += 1

    make_dirs(run_dir)
    manifest = {
        "run_id": run_dir.name,
        "created_at_local": now.isoformat(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "topic": args.topic,
        "topic_slug": slug,
        "output_policy": "all survey outputs for this topic must remain under this run directory",
        "status": "initialized",
        "expected_outputs": [
            "drafts/survey_en.md",
            "drafts/survey_ja.md",
            "drafts/survey_en.linked.md",
            "drafts/survey_ja.linked.md",
            "figures/overview_figure_prompt.md",
            "figures/overview_figure_spec.md",
            "figures/overview_figure.<ext>",
            "reports/figure_selection.md",
            "tex/survey_en.tex",
            "tex/survey_ja.tex",
            "tex/references.bib",
            "tex/survey_en.pdf (if local LaTeX environment is available)",
            "tex/survey_ja.pdf (if local LuaLaTeX or upLaTeX+dvipdfmx environment is available)",
            "reports/figure_audit.md",
            "reports/claim_audit.md",
            "reports/validation_report.md",
            "evidence/evidence_cards.jsonl",
            "web/integrated_search_summary.md",
        ],
    }
    write_placeholders(run_dir, args.topic, manifest)
    update_latest(outputs_dir, run_dir)

    print(str(run_dir))
    print(f"RUN_DIR={run_dir}")


if __name__ == "__main__":
    main()
