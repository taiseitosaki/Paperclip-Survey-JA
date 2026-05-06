#!/usr/bin/env python3
"""Validate a survey run and write reports/validation_report.md."""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional

CID_RE = re.compile(r"C\d{3,4}")
LINK_RE = re.compile(r"\[\[(C\d{3,4})\]\]\(#ref-\1\)")
ANCHOR_RE = re.compile(r"<a\s+id=\"ref-(C\d{3,4})\"\s*>\s*</a>", re.I)
CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
FIG_MD_RE = re.compile(r"!\[[^\]]*\]\(([^)]*overview_figure[^)]*)\)", re.I)
FIG_TEX_RE = re.compile(r"\\includegraphics\[[^\]]*\]\{([^}]*overview_figure[^}]*)\}", re.I)
FIG_REF_EN_RE = re.compile(r"\bFigure\s*1\b")
FIG_REF_JA_RE = re.compile(r"図\s*1")
IMAGE_GEN_ROUTE_RE = re.compile(r"(?im)^\s*(?:rendering\s+route|route|source)\s*:\s*image_gen\b")
FALLBACK_ROUTE_RE = re.compile(r"(?im)^\s*(?:rendering\s+route|route|source)\s*:\s*(?:fallback|deterministic|render_overview_figure)\b")


def load_cards(run_dir: Path) -> Dict[str, dict]:
    cards = {}
    path = run_dir / "evidence" / "evidence_cards.jsonl"
    if not path.exists():
        return cards
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            cards[f"INVALID_LINE_{n}"] = {"_invalid": line}
            continue
        cid = obj.get("card_id") or obj.get("citation_id") or obj.get("bib_key") or f"MISSING_ID_{n}"
        cards[str(cid)] = obj
    return cards


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def csv_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return sum(1 for _ in reader)
    except Exception:
        return max(0, len(path.read_text(encoding="utf-8").splitlines()) - 1)


def screening_preprint_exclusion_warnings(path: Path) -> List[str]:
    warnings = []
    if not path.exists():
        return warnings
    try:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 2):
                tier = (row.get("tier") or "").lower()
                reason = (row.get("reason") or "").lower()
                if tier == "out_of_scope" and "preprint" in reason:
                    warnings.append(f"screening_decisions.csv line {i}: preprint appears to be used as an exclusion reason")
    except Exception:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if "out_of_scope" in text and "preprint" in text:
            warnings.append("screening_decisions.csv may use preprint status as an exclusion reason")
    return warnings


def find_overview_figure(run_dir: Path) -> Optional[Path]:
    fig_dir = run_dir / "figures"
    if not fig_dir.exists():
        return None
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        p = fig_dir / f"overview_figure{ext}"
        if p.exists():
            return p
    return None


def find_figure_candidates(run_dir: Path) -> List[Path]:
    fig_dir = run_dir / "figures"
    if not fig_dir.exists():
        return []
    candidates: List[Path] = []
    for pattern in [
        "overview_figure_candidate_*.png",
        "overview_figure_candidate_*.jpg",
        "overview_figure_candidate_*.jpeg",
        "overview_figure_candidate_*.webp",
        "overview_figure_candidate_*.svg",
    ]:
        candidates.extend(fig_dir.glob(pattern))
    return sorted(set(candidates))


def find_deterministic_figure_artifacts(run_dir: Path) -> List[Path]:
    fig_dir = run_dir / "figures"
    if not fig_dir.exists():
        return []
    artifacts: List[Path] = []
    json_spec = fig_dir / "overview_figure_spec.json"
    if json_spec.exists():
        artifacts.append(json_spec)
    artifacts.extend(fig_dir.glob("overview_figure_candidate_*.svg"))
    return sorted(set(artifacts))


def latex_environment_available() -> bool:
    return any(shutil.which(cmd) for cmd in ["latexmk", "lualatex", "xelatex", "pdflatex", "uplatex"])


def english_pdf_environment_available() -> bool:
    return any(shutil.which(cmd) for cmd in ["pdflatex", "xelatex", "lualatex"])


def japanese_pdf_environment_available() -> bool:
    return bool(shutil.which("lualatex") or (shutil.which("uplatex") and shutil.which("dvipdfmx")))


def figure_rendering_route(*texts: str) -> str:
    combined = "\n".join(texts)
    if IMAGE_GEN_ROUTE_RE.search(combined):
        return "image_gen"
    if FALLBACK_ROUTE_RE.search(combined):
        return "fallback"
    return "unrecorded"


def figure_audit_decision(text: str) -> str:
    if not text.strip():
        return "missing"
    m = re.search(r"(?im)^\s*(decision|status)\s*:\s*(accept|accepted|revise|revision|reject|rejected)\b", text)
    if m:
        value = m.group(2).lower()
        if value.startswith("accept"):
            return "accept"
        if value.startswith("revis"):
            return "revise"
        if value.startswith("reject"):
            return "reject"
    lower = text.lower()
    if re.search(r"\breject(ed)?\b", lower):
        return "reject"
    if re.search(r"\brevis(e|ion|ed)\b", lower):
        return "revise"
    if re.search(r"\baccept(ed)?\b", lower):
        return "accept"
    return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    run_dir = Path(args.run)

    required = [
        "run_manifest.json",
        "prompt.txt",
        "drafts/survey_en.md",
        "drafts/survey_ja.md",
        "drafts/survey_en.linked.md",
        "drafts/survey_ja.linked.md",
        "figures/overview_figure_prompt.md",
        "figures/overview_figure_spec.md",
        "reports/figure_selection.md",
        "tex/survey_en.tex",
        "tex/survey_ja.tex",
        "tex/references.bib",
        "evidence/evidence_cards.jsonl",
        "reports/claim_audit.md",
        "reports/figure_audit.md",
        "web/web_query_plan_round1.md",
        "web/web_query_plan_round2.md",
        "web/integrated_search_summary.md",
    ]

    cards = load_cards(run_dir)
    valid_card_ids = {cid for cid, c in cards.items() if CID_RE.fullmatch(cid) and not c.get("_invalid")}
    invalid_cards = [cid for cid, c in cards.items() if c.get("_invalid") or not CID_RE.fullmatch(cid)]

    en = read_text(run_dir / "drafts" / "survey_en.md")
    ja = read_text(run_dir / "drafts" / "survey_ja.md")
    en_linked = read_text(run_dir / "drafts" / "survey_en.linked.md")
    ja_linked = read_text(run_dir / "drafts" / "survey_ja.linked.md")
    tex_en = read_text(run_dir / "tex" / "survey_en.tex")
    tex_ja = read_text(run_dir / "tex" / "survey_ja.tex")
    bib = read_text(run_dir / "tex" / "references.bib")
    pdf_en = run_dir / "tex" / "survey_en.pdf"
    pdf_ja = run_dir / "tex" / "survey_ja.pdf"
    web_summary = read_text(run_dir / "web" / "integrated_search_summary.md")
    figure_audit = read_text(run_dir / "reports" / "figure_audit.md")
    figure_spec = read_text(run_dir / "figures" / "overview_figure_spec.md")
    figure_prompt = read_text(run_dir / "figures" / "overview_figure_prompt.md")
    figure_selection = read_text(run_dir / "reports" / "figure_selection.md")

    cited_en = set(CID_RE.findall(en))
    cited_ja = set(CID_RE.findall(ja))
    cited_all = cited_en | cited_ja
    linked_ids = set(LINK_RE.findall(en_linked)) | set(LINK_RE.findall(ja_linked))
    anchors = set(ANCHOR_RE.findall(en_linked)) | set(ANCHOR_RE.findall(ja_linked))
    bib_ids = set(re.findall(r"@\w+\{(C\d{3,4}),", bib))

    candidate_count = csv_count(run_dir / "searches" / "deduped_candidates.csv")
    screening_count = csv_count(run_dir / "searches" / "screening_decisions.csv")
    evidence_count = len(valid_card_ids)
    citation_count = len(cited_all)
    web_candidate_count = csv_count(run_dir / "web" / "triangulated_candidates.csv")
    figure_path = find_overview_figure(run_dir)
    figure_candidates = find_figure_candidates(run_dir)
    deterministic_artifacts = find_deterministic_figure_artifacts(run_dir)
    audit_decision = figure_audit_decision(figure_audit)
    rendering_route = figure_rendering_route(figure_prompt, figure_selection)
    latex_available = latex_environment_available()
    en_pdf_available = english_pdf_environment_available()
    ja_pdf_available = japanese_pdf_environment_available()

    warnings: List[str] = []
    errors: List[str] = []

    for rel in required:
        if not (run_dir / rel).exists():
            errors.append(f"Missing required file: `{rel}`")

    if not figure_path:
        errors.append("Missing overview figure under `figures/overview_figure.<ext>`")

    if len(figure_candidates) < 2:
        warnings.append(f"Only {len(figure_candidates)} overview-figure candidate(s) found. Generate at least two candidates before final selection.")

    if not figure_spec.strip() or len([ln for ln in figure_spec.splitlines() if ln.strip()]) < 8:
        warnings.append("overview_figure_spec.md looks empty or too brief; figure content may not have been distilled before rendering.")

    if not figure_selection.strip() or "pending" in figure_selection.lower():
        warnings.append("figure_selection.md is missing, pending, or too brief; document why the accepted figure was selected.")

    if rendering_route == "unrecorded":
        warnings.append("Overview figure rendering route is not recorded. Add `Rendering route: image_gen` or a documented fallback route to overview_figure_prompt.md or figure_selection.md.")
    elif rendering_route == "image_gen" and deterministic_artifacts:
        warnings.append(
            "Figure route is recorded as image_gen, but deterministic fallback artifacts are present: "
            + ", ".join(str(p.relative_to(run_dir)) for p in deterministic_artifacts[:6])
        )

    if audit_decision != "accept":
        errors.append(f"Figure audit decision is `{audit_decision}`, not `accept`.")

    if invalid_cards:
        errors.append(f"Invalid evidence card IDs or JSON lines: {', '.join(invalid_cards[:10])}")

    missing_cards = sorted(cited_all - valid_card_ids)
    if missing_cards:
        errors.append(f"Citations without evidence cards: {', '.join(missing_cards)}")

    missing_links = sorted(cited_all - linked_ids)
    if missing_links:
        warnings.append(f"Citations not linked in linked Markdown: {', '.join(missing_links)}")

    missing_anchors = sorted(cited_all - anchors)
    if missing_anchors:
        warnings.append(f"Reference anchors missing in linked Markdown: {', '.join(missing_anchors)}")

    missing_bib = sorted(cited_all - bib_ids)
    if missing_bib:
        warnings.append(f"Citations missing from references.bib: {', '.join(missing_bib)}")

    if latex_available:
        if tex_en and en_pdf_available and not pdf_en.exists():
            errors.append("Local LaTeX tools are available, but `tex/survey_en.pdf` was not built. Run `python3 scripts/compile_latex.py --run <run-dir>`.")
        elif tex_en and not en_pdf_available:
            warnings.append("Local LaTeX tools are present, but no supported English PDF engine (pdfLaTeX, XeLaTeX, or LuaLaTeX) is available.")
        if tex_ja and ja_pdf_available and not pdf_ja.exists():
            errors.append("Local Japanese LaTeX tools are available, but `tex/survey_ja.pdf` was not built. Run `python3 scripts/compile_latex.py --run <run-dir>`.")
        elif tex_ja and not ja_pdf_available:
            warnings.append("Local LaTeX tools are present, but neither LuaLaTeX nor upLaTeX+dvipdfmx is available for Japanese PDF compilation.")
    else:
        warnings.append("No local LaTeX environment detected; PDF compilation was skipped.")

    if ja and len(CJK_RE.findall(ja)) < max(50, len(ja) // 20):
        warnings.append("Japanese survey appears to contain too little Japanese text; check for untranslated English sections.")

    if en and len(CJK_RE.findall(en)) > max(50, len(en) // 20):
        warnings.append("English survey appears to contain substantial Japanese text; check language separation.")

    if candidate_count >= 150 and evidence_count < 50:
        warnings.append(f"Evidence cards look thin: {candidate_count} deduplicated candidates but only {evidence_count} evidence cards. Justify in coverage audit or extract more papers.")
    elif 50 <= candidate_count < 150 and evidence_count < 30:
        warnings.append(f"Evidence cards look thin: {candidate_count} deduplicated candidates but only {evidence_count} evidence cards. Justify or extract more.")
    elif candidate_count and evidence_count < min(20, candidate_count):
        warnings.append(f"Evidence cards may be too few for a survey: {candidate_count} candidates, {evidence_count} evidence cards.")

    if citation_count < 20:
        warnings.append(f"Final cited-paper count is {citation_count}; unless the field is genuinely small, label as rapid mini-review or expand search/deep reading.")
    if evidence_count and citation_count / evidence_count < 0.45:
        warnings.append(f"Only {citation_count}/{evidence_count} evidence cards are cited. Check whether useful relevant papers were unnecessarily omitted from the synthesis.")

    warnings.extend(screening_preprint_exclusion_warnings(run_dir / "searches" / "screening_decisions.csv"))

    if not web_summary.strip() or len(web_summary.strip().splitlines()) < 3:
        warnings.append("Integrated web-search summary looks empty or too brief.")
    if web_candidate_count == 0:
        warnings.append("No rows found in web/triangulated_candidates.csv. Web search may not have been meaningfully integrated.")

    if figure_path:
        if not FIG_MD_RE.search(en) and not FIG_MD_RE.search(en_linked):
            errors.append("English Markdown draft does not contain the accepted overview-figure image block.")
        if not FIG_MD_RE.search(ja) and not FIG_MD_RE.search(ja_linked):
            errors.append("Japanese Markdown draft does not contain the accepted overview-figure image block.")
        if not FIG_TEX_RE.search(tex_en):
            errors.append("English TeX does not include the accepted overview figure.")
        if not FIG_TEX_RE.search(tex_ja):
            errors.append("Japanese TeX does not include the accepted overview figure.")
        if not FIG_REF_EN_RE.search(en):
            warnings.append("English draft may not explicitly reference Figure 1 in the prose.")
        if not FIG_REF_JA_RE.search(ja):
            warnings.append("Japanese draft may not explicitly reference 図1 in the prose.")

    if audit_decision != "accept":
        warnings.append("Figure audit does not clearly indicate acceptance.")

    report = []
    report.append("# Validation report")
    report.append("")
    report.append(f"Run: `{run_dir}`")
    report.append("")
    report.append("## Summary")
    report.append("")
    report.append(f"- Deduplicated candidates: {candidate_count if candidate_count else 'not available'}")
    report.append(f"- Screening rows: {screening_count if screening_count else 'not available'}")
    report.append(f"- Web-triangulated candidates: {web_candidate_count if web_candidate_count else 'not available'}")
    report.append(f"- Valid evidence cards: {evidence_count}")
    report.append(f"- Cited IDs across EN/JA drafts: {citation_count}")
    report.append(f"- Linked citation IDs: {len(linked_ids)}")
    report.append(f"- Reference anchors: {len(anchors)}")
    report.append(f"- BibTeX entries: {len(bib_ids)}")
    report.append(f"- Local LaTeX environment available: {'yes' if latex_available else 'no'}")
    report.append(f"- English PDF present: {'yes' if pdf_en.exists() else 'no'}")
    report.append(f"- Japanese PDF present: {'yes' if pdf_ja.exists() else 'no'}")
    report.append(f"- Overview figure present: {'yes' if figure_path else 'no'}")
    report.append(f"- Overview figure candidates: {len(figure_candidates)}")
    report.append(f"- Figure rendering route: {rendering_route}")
    report.append(f"- Figure audit decision: {audit_decision}")
    report.append("")
    report.append("## Errors")
    report.append("")
    if errors:
        report.extend(f"- {e}" for e in errors)
    else:
        report.append("- None detected.")
    report.append("")
    report.append("## Warnings")
    report.append("")
    if warnings:
        report.extend(f"- {w}" for w in warnings)
    else:
        report.append("- None detected.")
    report.append("")
    report.append("## Interpretation")
    report.append("")
    if errors:
        report.append("Status: **fail**. Fix errors before treating the survey as usable.")
    elif warnings:
        report.append("Status: **pass with warnings**. Review warnings before using the survey for serious research work.")
    else:
        report.append("Status: **pass**. This script checks structural quality; semantic correctness still requires claim audit.")
    report.append("")

    out = run_dir / "reports" / "validation_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(report), encoding="utf-8")
    print(f"wrote {out}")
    print("fail" if errors else "pass")


if __name__ == "__main__":
    main()
