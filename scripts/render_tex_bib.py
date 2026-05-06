#!/usr/bin/env python3
"""Render Overleaf-ready TeX and BibTeX from survey Markdown and evidence cards.

This intentionally implements a conservative Markdown-to-LaTeX converter rather
than relying on pandoc, so the starter works on a fresh macOS environment.
Complex Markdown tables are wrapped in verbatim blocks to preserve compilation.
If Markdown images are present, they are converted into LaTeX figure environments
and copied into `tex/figures/`.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

CID_RE = re.compile(r"C\d{3,4}")
REF_HEADING_RE = re.compile(r"^#{1,6}\s*(references|reference list|参考文献|文献)\s*$", re.I)
IMAGE_RE = re.compile(r"^!\[(.*?)\]\(([^)]+)\)\s*$")
FIG_CAPTION_RE = re.compile(r"^\*?(Figure\s+\d+\.?|図\s*\d+\.?)(.*)\*?$", re.I)
OVERVIEW_MD_RE = re.compile(r"!\[[^\]]*\]\([^)]*overview_figure[^)]*\)", re.I)
OVERVIEW_EXTS = [".png", ".jpg", ".jpeg", ".webp"]

LATEX_SPECIALS = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}


def escape_latex_raw(text: str) -> str:
    return "".join(LATEX_SPECIALS.get(ch, ch) for ch in text)


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


def normalize_authors(authors) -> str:
    if not authors:
        return "Unknown Author"
    if isinstance(authors, list):
        return " and ".join(str(a) for a in authors)
    s = str(authors).strip()
    s = re.sub(r"\s+", " ", s)
    et_al = re.match(r"^(?P<lead>.+?)\s+et\s+al\.?$", s, flags=re.I)
    if et_al:
        lead = et_al.group("lead").strip(" ,;")
        return f"{lead} and others" if lead else "others"
    if ";" in s:
        return " and ".join(part.strip() for part in s.split(";") if part.strip())
    if "," in s:
        parts = [part.strip() for part in s.split(",") if part.strip()]
        out: List[str] = []
        has_et_al = False
        for part in parts:
            part = re.sub(r"^(and|&)\s+", "", part, flags=re.I).strip()
            if re.search(r"\bet\s+al\.?$", part, re.I):
                has_et_al = True
                part = re.sub(r"\bet\s+al\.?$", "", part, flags=re.I).strip()
            if part:
                out.append(part)
        if has_et_al:
            out.append("others")
        # Convert natural-language comma lists such as
        # "Huang, Altosaar, and Ranganath" into BibTeX-safe author lists.
        if len(out) > 1 and all(len(part.split()) <= 4 for part in out):
            return " and ".join(out)
    if " and " in s:
        return s
    return s


def bib_escape(value: str, *, url_field: bool = False) -> str:
    value = str(value).replace("\n", " ").strip()
    value = re.sub(r"\s+", " ", value)
    if url_field:
        return value.replace("{", "\\{").replace("}", "\\}")
    for char, replacement in {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }.items():
        value = value.replace(char, replacement)
    return value


def first_nonempty(*values) -> str:
    for v in values:
        if v:
            return str(v)
    return ""


def make_bib(cards: Dict[str, dict]) -> str:
    entries: List[str] = []
    for cid in sorted(cards):
        c = cards[cid]
        title = first_nonempty(c.get("title"), "Untitled")
        authors = normalize_authors(c.get("authors") or c.get("author"))
        year = first_nonempty(c.get("year"), c.get("date"), "n.d.")
        year_match = re.search(r"\d{4}", year)
        year = year_match.group(0) if year_match else "n.d."
        journal = first_nonempty(c.get("journal"), c.get("venue"), c.get("source"), c.get("source_type"))
        doi = first_nonempty(c.get("doi"))
        url = first_nonempty(c.get("url"))
        arxiv = first_nonempty(c.get("arxiv"), c.get("arxiv_id"))
        pmid = first_nonempty(c.get("pmid"))
        pmcid = first_nonempty(c.get("pmcid"), c.get("pmc"))
        note_parts = []
        pub_status = first_nonempty(c.get("publication_status"), c.get("source_type"))
        if pub_status:
            note_parts.append(pub_status)
        if pmid:
            note_parts.append(f"PMID: {pmid}")
        if pmcid:
            note_parts.append(f"PMCID: {pmcid}")
        note = "; ".join(note_parts)
        fields = {
            "author": authors,
            "title": title,
            "year": year,
        }
        if journal:
            fields["journal"] = journal
        if doi:
            fields["doi"] = doi
        if url:
            fields["url"] = url
        if arxiv:
            fields["eprint"] = arxiv.replace("arXiv:", "")
            fields["archivePrefix"] = "arXiv"
        if note:
            fields["note"] = note
        body = ",\n".join(f"  {k} = {{{bib_escape(v, url_field=(k == 'url'))}}}" for k, v in fields.items() if v)
        entries.append(f"@article{{{cid},\n{body}\n}}")
    return "\n\n".join(entries).rstrip() + "\n"


def find_overview_figure(run_dir: Path) -> Optional[Path]:
    fig_dir = run_dir / "figures"
    for ext in OVERVIEW_EXTS:
        path = fig_dir / f"overview_figure{ext}"
        if path.exists():
            return path
    return None


def choose_markdown_source(run_dir: Path, stem: str, overview_figure: Optional[Path]) -> Optional[Path]:
    linked = run_dir / "drafts" / f"{stem}.linked.md"
    raw = run_dir / "drafts" / f"{stem}.md"
    existing = [p for p in [linked, raw] if p.exists()]
    if not existing:
        return None
    if overview_figure is None:
        return linked if linked.exists() else raw

    with_figure = [p for p in existing if OVERVIEW_MD_RE.search(p.read_text(encoding="utf-8"))]
    if with_figure:
        return with_figure[0]
    raise SystemExit(
        f"Accepted overview figure exists at {overview_figure}, but neither {raw} nor {linked} "
        "contains an overview_figure image block. Run scripts/insert_overview_figure.py first."
    )


def split_title_and_body(md: str) -> Tuple[str, List[str]]:
    lines = md.splitlines()
    title = "Survey Paper"
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            body_start = i + 1
            break
    return title, lines[body_start:]


def strip_references(lines: List[str]) -> List[str]:
    out: List[str] = []
    for line in lines:
        if REF_HEADING_RE.match(line.strip()):
            break
        out.append(line)
    return out


def escape_latex_text(text: str) -> str:
    placeholders: Dict[str, str] = {}

    def protect(pattern: str, text: str) -> str:
        def repl(m: re.Match) -> str:
            key = f"@@PH{len(placeholders)}@@"
            placeholders[key] = m.group(0)
            return key
        return re.sub(pattern, repl, text)

    text = protect(r"\\cite\{[^}]+\}", text)
    text = protect(r"\\url\{[^}]+\}", text)
    text = protect(r"\\textbf\{[^}]+\}", text)
    text = protect(r"\\texttt\{[^}]+\}", text)

    escaped = escape_latex_raw(text)
    for key, value in placeholders.items():
        escaped = escaped.replace(key, value)
    return escaped


def convert_citations(text: str) -> str:
    text = re.sub(r"\[\[(C\d{3,4})\]\]\(#ref-\1\)", lambda m: rf"\cite{{{m.group(1)}}}", text)
    text = re.sub(r"(?<!\[)\[(C\d{3,4})\]", lambda m: rf"\cite{{{m.group(1)}}}", text)
    return text


def convert_inline_markup(text: str) -> str:
    text = re.sub(r"https?://[^\s)]+", lambda m: rf"\url{{{m.group(0)}}}", text)
    text = re.sub(r"\*\*([^*]+)\*\*", lambda m: rf"\textbf{{{escape_latex_raw(m.group(1))}}}", text)
    text = re.sub(r"`([^`]+)`", lambda m: rf"\texttt{{{escape_latex_raw(m.group(1))}}}", text)
    return text


def md_table_block(lines: List[str], start: int) -> Tuple[str, int]:
    block: List[str] = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|"):
        block.append(lines[i])
        i += 1
    rows: List[List[str]] = []
    for line in block:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        text = "\n".join(block)
        return "\\begin{verbatim}\n" + text + "\n\\end{verbatim}", i

    ncols = max(len(row) for row in rows)
    if ncols == 3:
        colspec = (
            r">{\raggedright\arraybackslash}p{0.22\linewidth}"
            r">{\raggedright\arraybackslash}p{0.32\linewidth}"
            r">{\raggedright\arraybackslash}p{0.38\linewidth}"
        )
    else:
        width = 0.92 / max(1, ncols)
        colspec = "".join(r">{\raggedright\arraybackslash}p{" + f"{width:.2f}" + r"\linewidth}" for _ in range(ncols))

    def cell_tex(cell: str) -> str:
        return escape_latex_text(convert_inline_markup(convert_citations(cell)))

    tex: List[str] = [r"\begin{footnotesize}", rf"\begin{{longtable}}{{{colspec}}}", r"\toprule"]
    header = rows[0] + [""] * (ncols - len(rows[0]))
    tex.append(" & ".join(cell_tex(cell) for cell in header) + r" \\")
    tex.append(r"\midrule")
    tex.append(r"\endfirsthead")
    tex.append(r"\toprule")
    tex.append(" & ".join(cell_tex(cell) for cell in header) + r" \\")
    tex.append(r"\midrule")
    tex.append(r"\endhead")
    for row in rows[1:]:
        padded = row + [""] * (ncols - len(row))
        tex.append(" & ".join(cell_tex(cell) for cell in padded) + r" \\")
    tex.append(r"\bottomrule")
    tex.append(r"\end{longtable}")
    tex.append(r"\end{footnotesize}")
    return "\n".join(tex), i


def sanitize_filename(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
    return name or "figure.png"


def latex_from_image(src_md_path: Path, image_ref: str, caption: str, tex_dir: Path, figure_index: int) -> str:
    source_path = (src_md_path.parent / image_ref).resolve() if not Path(image_ref).is_absolute() else Path(image_ref)
    if not source_path.exists():
        tex_path = image_ref.replace("\\", "/")
    else:
        tex_fig_dir = tex_dir / "figures"
        tex_fig_dir.mkdir(parents=True, exist_ok=True)
        name = sanitize_filename(source_path.name)
        target_path = tex_fig_dir / name
        shutil.copy2(source_path, target_path)
        tex_path = ("figures/" + name).replace("\\", "/")
    cap_text = re.sub(r"^(Figure\s+\d+\.?|図\s*\d+\.?)\s*", "", caption or "Overview figure", flags=re.I)
    cap = escape_latex_text(convert_inline_markup(convert_citations(cap_text)))
    label = "fig:overview" if figure_index == 1 else f"fig:{figure_index}"
    return (
        "\\begin{figure}[t]\n"
        "\\centering\n"
        f"\\includegraphics[width=\\linewidth]{{{tex_path}}}\n"
        f"\\caption{{{cap}}}\n"
        f"\\label{{{label}}}\n"
        "\\end{figure}"
    )


def markdown_to_latex(md: str, src_md_path: Path, tex_dir: Path) -> Tuple[str, str]:
    title, lines = split_title_and_body(md)
    lines = strip_references(lines)
    out: List[str] = []
    in_code = False
    in_abstract = False
    i = 0
    figure_index = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            out.append("\\end{verbatim}" if in_code else "\\begin{verbatim}")
            in_code = not in_code
            i += 1
            continue
        if in_code:
            out.append(line)
            i += 1
            continue

        if stripped.startswith("|"):
            table_tex, next_i = md_table_block(lines, i)
            out.append(table_tex)
            i = next_i
            continue

        img_match = IMAGE_RE.match(stripped)
        if img_match:
            alt_text, image_ref = img_match.groups()
            caption = alt_text.strip() or "Overview figure"
            caption_i = i + 1
            while caption_i < len(lines) and not lines[caption_i].strip():
                caption_i += 1
            if caption_i < len(lines):
                nxt = lines[caption_i].strip()
                if FIG_CAPTION_RE.match(nxt):
                    caption = nxt.strip("*").strip()
                    i = caption_i
            figure_index += 1
            out.append(latex_from_image(src_md_path, image_ref, caption, tex_dir, figure_index))
            i += 1
            continue

        if stripped == "":
            out.append("")
            i += 1
            continue

        if in_abstract and stripped.startswith("#"):
            out.append("\\end{abstract}")
            in_abstract = False

        if stripped.startswith("###### "):
            out.append(r"\paragraph{" + escape_latex_text(stripped[7:]) + "}")
        elif stripped.startswith("##### "):
            out.append(r"\paragraph{" + escape_latex_text(stripped[6:]) + "}")
        elif stripped.startswith("#### "):
            out.append(r"\subsubsection{" + escape_latex_text(stripped[5:]) + "}")
        elif stripped.startswith("### "):
            out.append(r"\subsection{" + escape_latex_text(stripped[4:]) + "}")
        elif stripped.startswith("## "):
            heading = stripped[3:].strip()
            if heading.lower() == "abstract" or heading == "概要":
                out.append("\\begin{abstract}")
                in_abstract = True
            else:
                out.append(r"\section{" + escape_latex_text(heading) + "}")
        elif stripped.startswith("# "):
            out.append(r"\section{" + escape_latex_text(stripped[2:]) + "}")
        elif re.match(r"^[-*]\s+", stripped):
            items: List[str] = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                item = re.sub(r"^[-*]\s+", "", lines[i].strip())
                item = escape_latex_text(convert_inline_markup(convert_citations(item)))
                items.append(r"\item " + item)
                i += 1
            out.append("\\begin{itemize}")
            out.extend(items)
            out.append("\\end{itemize}")
            continue
        elif re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                item = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                item = escape_latex_text(convert_inline_markup(convert_citations(item)))
                items.append(r"\item " + item)
                i += 1
            out.append("\\begin{enumerate}")
            out.extend(items)
            out.append("\\end{enumerate}")
            continue
        else:
            text = escape_latex_text(convert_inline_markup(convert_citations(line)))
            out.append(text)
        i += 1

    if in_abstract:
        out.append("\\end{abstract}")
    return title, "\n".join(out).strip() + "\n"


def tex_document(title: str, body: str, lang: str) -> str:
    if lang == "ja":
        preamble = r"""% Compile with LuaLaTeX on Overleaf.
\documentclass[11pt,a4paper]{ltjsarticle}
\usepackage{luatexja}
\usepackage[haranoaji]{luatexja-preset}
\usepackage{geometry}
\geometry{margin=25mm}
\usepackage{hyperref}
\usepackage{url}
\usepackage{graphicx}
\usepackage{longtable}
\usepackage{booktabs}
\usepackage{array}
\usepackage[numbers,sort&compress]{natbib}
\hypersetup{colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue}
"""
    else:
        preamble = r"""% Compile with pdfLaTeX, XeLaTeX, or LuaLaTeX on Overleaf.
\documentclass[11pt,a4paper]{article}
\usepackage[margin=1in]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{hyperref}
\usepackage{url}
\usepackage{graphicx}
\usepackage{longtable}
\usepackage{booktabs}
\usepackage{array}
\usepackage[numbers,sort&compress]{natbib}
\hypersetup{colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue}
"""
    title_tex = escape_latex_text(title)
    return (
        preamble
        + "\n"
        + f"\\title{{{title_tex}}}\n"
        + r"\author{Paperclip--Codex survey workflow}"
        + "\n"
        + r"\date{\today}"
        + "\n\n"
        + r"\begin{document}"
        + "\n"
        + r"\maketitle"
        + "\n\n"
        + body
        + "\n"
        + r"\bibliographystyle{plainnat}"
        + "\n"
        + r"\bibliography{references}"
        + "\n"
        + r"\end{document}"
        + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, help="Run directory")
    args = parser.parse_args()
    run_dir = Path(args.run)
    tex_dir = run_dir / "tex"
    tex_dir.mkdir(parents=True, exist_ok=True)
    (tex_dir / "figures").mkdir(parents=True, exist_ok=True)

    cards = load_cards(run_dir)
    (tex_dir / "references.bib").write_text(make_bib(cards), encoding="utf-8")
    overview_figure = find_overview_figure(run_dir)

    for stem, lang in [("survey_en", "en"), ("survey_ja", "ja")]:
        src = choose_markdown_source(run_dir, stem, overview_figure)
        if src is None:
            print(f"skip: {run_dir / 'drafts' / f'{stem}.md'} does not exist")
            continue
        title, body = markdown_to_latex(src.read_text(encoding="utf-8"), src, tex_dir)
        dst = tex_dir / f"{stem}.tex"
        dst.write_text(tex_document(title, body, lang), encoding="utf-8")
        print(f"wrote {dst}")
    print(f"wrote {tex_dir / 'references.bib'}")


if __name__ == "__main__":
    main()
