#!/usr/bin/env python3
"""Create Markdown files with clickable citation links.

Input:
  <run>/drafts/survey_en.md
  <run>/drafts/survey_ja.md
  <run>/evidence/evidence_cards.jsonl   optional but recommended

Output:
  <run>/drafts/survey_en.linked.md
  <run>/drafts/survey_ja.linked.md

The script converts body citations like [C001] into [[C001]](#ref-C001), and
adds reference anchors like <a id="ref-C001"></a>[C001] in the References section.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List

CID_RE = re.compile(r"C\d{3,4}")
REF_HEADING_RE = re.compile(r"^#{1,6}\s*(references|reference list|参考文献|文献)\s*$", re.I)
REF_LINE_RE = re.compile(r"^(?P<prefix>\s*(?:[-*]\s*)?)(?:<a\s+id=\"ref-(?P<aid>C\d{3,4})\"\s*>\s*</a>\s*)?\[?(?P<cid>C\d{3,4})\]?\s*(?P<rest>.*)$")


def load_cards(run_dir: Path) -> Dict[str, dict]:
    path = run_dir / "evidence" / "evidence_cards.jsonl"
    cards: Dict[str, dict] = {}
    if not path.exists():
        return cards
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        cid = obj.get("card_id") or obj.get("citation_id") or obj.get("bib_key")
        if cid and CID_RE.fullmatch(str(cid)):
            cards[str(cid)] = obj
    return cards


def reference_from_card(cid: str, card: dict) -> str:
    authors = card.get("authors") or card.get("author") or "Unknown author"
    if isinstance(authors, list):
        authors = ", ".join(str(a) for a in authors[:8]) + (" et al." if len(authors) > 8 else "")
    year = card.get("year") or card.get("date") or "n.d."
    title = card.get("title") or "Untitled"
    venue = card.get("journal") or card.get("venue") or card.get("source") or card.get("source_type") or ""
    doi = card.get("doi") or ""
    pmcid = card.get("pmcid") or card.get("pmc") or ""
    pmid = card.get("pmid") or ""
    arxiv = card.get("arxiv") or card.get("arxiv_id") or ""
    extras = "; ".join(x for x in [venue, f"DOI: {doi}" if doi else "", f"PMCID: {pmcid}" if pmcid else "", f"PMID: {pmid}" if pmid else "", f"arXiv: {arxiv}" if arxiv else ""] if x)
    return f"- <a id=\"ref-{cid}\"></a>[{cid}] {authors} ({year}). {title}. {extras}".rstrip()


def find_refs_start(lines: List[str]) -> int | None:
    for i, line in enumerate(lines):
        if REF_HEADING_RE.match(line.strip()):
            return i
    return None


def cited_ids(text: str) -> List[str]:
    ids = sorted(set(CID_RE.findall(text)))
    return ids


def link_body_line(line: str) -> str:
    # Protect already-linked citations.
    placeholders: Dict[str, str] = {}

    def protect(m: re.Match) -> str:
        key = f"@@LINKED_CIT_{len(placeholders)}@@"
        placeholders[key] = m.group(0)
        return key

    line = re.sub(r"\[\[C\d{3,4}\]\]\(#ref-C\d{3,4}\)", protect, line)

    # Convert [C001] to [[C001]](#ref-C001). Avoid image/link syntax confusion as much as possible.
    line = re.sub(r"(?<!\[)\[(C\d{3,4})\](?!\]\(#ref-)", lambda m: f"[[{m.group(1)}]](#ref-{m.group(1)})", line)

    for key, value in placeholders.items():
        line = line.replace(key, value)
    # Improve readability for adjacent citations like [C001][C002].
    line = re.sub(r"(\]\(#ref-C\d{3,4}\))(\[\[C)", r"\1 \2", line)
    return line


def anchor_ref_line(line: str) -> str:
    m = REF_LINE_RE.match(line)
    if not m:
        return line
    cid = m.group("cid")
    rest = m.group("rest").lstrip()
    prefix = m.group("prefix") or "- "
    if not prefix.strip():
        prefix = "- "
    # Normalize duplicate anchor/label forms.
    return f"{prefix}<a id=\"ref-{cid}\"></a>[{cid}] {rest}".rstrip()


def ensure_references(lines: List[str], cards: Dict[str, dict]) -> List[str]:
    ids = cited_ids("\n".join(lines))
    if not ids:
        return lines

    ref_start = find_refs_start(lines)
    if ref_start is None:
        lines = lines + ["", "## References"]
        ref_start = len(lines) - 1

    ref_text = "\n".join(lines[ref_start + 1 :])
    present = set(CID_RE.findall(ref_text))
    missing = [cid for cid in ids if cid not in present]
    if missing:
        if lines and lines[-1].strip():
            lines.append("")
        for cid in missing:
            card = cards.get(cid, {})
            lines.append(reference_from_card(cid, card))
    return lines


def process(md: str, cards: Dict[str, dict]) -> str:
    lines = md.splitlines()
    lines = ensure_references(lines, cards)
    ref_start = find_refs_start(lines)

    out: List[str] = []
    for i, line in enumerate(lines):
        if ref_start is not None and i > ref_start:
            out.append(anchor_ref_line(line))
        else:
            out.append(link_body_line(line))
    return "\n".join(out).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, help="Run directory")
    args = parser.parse_args()
    run_dir = Path(args.run)
    cards = load_cards(run_dir)

    for stem in ["survey_en", "survey_ja"]:
        src = run_dir / "drafts" / f"{stem}.md"
        if not src.exists():
            print(f"skip: {src} does not exist")
            continue
        dst = run_dir / "drafts" / f"{stem}.linked.md"
        dst.write_text(process(src.read_text(encoding="utf-8"), cards), encoding="utf-8")
        print(f"wrote {dst}")


if __name__ == "__main__":
    main()
