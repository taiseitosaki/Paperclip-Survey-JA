#!/usr/bin/env python3
"""Compile generated survey TeX files to PDF when LaTeX is available.

The workflow should still be usable on machines without a TeX distribution, so
missing compilers are treated as skips. If a compiler is available and a build
is attempted, build failures are reported with a non-zero exit status.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple


DOCS = [("survey_en", "en"), ("survey_ja", "ja")]
BUILD_EXTS = [
    ".aux",
    ".bbl",
    ".blg",
    ".dvi",
    ".fdb_latexmk",
    ".fls",
    ".log",
    ".out",
    ".xdv",
]


def engine_candidates(lang: str) -> List[str]:
    if lang == "ja":
        candidates: List[str] = []
        if shutil.which("lualatex"):
            candidates.append("lualatex")
        if shutil.which("uplatex") and shutil.which("dvipdfmx"):
            candidates.append("uplatex")
        return candidates
    return [engine for engine in ["pdflatex", "xelatex", "lualatex"] if shutil.which(engine)]


def latexmk_command(engine: str, tex_name: str) -> List[str]:
    cmd = [
        "latexmk",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "-g",
        "-bibtex",
    ]
    if engine == "lualatex":
        cmd.append("-lualatex")
    elif engine == "xelatex":
        cmd.append("-xelatex")
    else:
        cmd.append("-pdf")
    cmd.append(tex_name)
    return cmd


def latex_environment(tex_dir: Path) -> dict:
    env = os.environ.copy()
    cache_dir = tex_dir / ".latex-cache"
    for subdir in ["texmf-var", "texmf-config", "texmf-cache"]:
        (cache_dir / subdir).mkdir(parents=True, exist_ok=True)
    env["TEXMFVAR"] = str((cache_dir / "texmf-var").resolve())
    env["TEXMFCONFIG"] = str((cache_dir / "texmf-config").resolve())
    env["TEXMFCACHE"] = str((cache_dir / "texmf-cache").resolve())
    return env


def run_and_log(cmd: List[str], cwd: Path, log_path: Path, env: dict) -> int:
    with log_path.open("a", encoding="utf-8") as log:
        log.write("$ " + " ".join(cmd) + "\n")
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        log.write(proc.stdout)
        if proc.stdout and not proc.stdout.endswith("\n"):
            log.write("\n")
        log.write(f"[exit {proc.returncode}]\n\n")
    return proc.returncode


def clean_intermediates(tex_dir: Path, stems: List[str]) -> None:
    for stem in stems:
        for ext in BUILD_EXTS:
            path = tex_dir / f"{stem}{ext}"
            if path.exists():
                path.unlink()


def compile_with_engine(tex_dir: Path, stem: str, engine: str, log_path: Path) -> bool:
    tex_name = f"{stem}.tex"
    env = latex_environment(tex_dir)
    if shutil.which("latexmk"):
        return run_and_log(latexmk_command(engine, tex_name), tex_dir, log_path, env) == 0

    latex_cmd = [engine, "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", tex_name]
    if run_and_log(latex_cmd, tex_dir, log_path, env) != 0:
        return False

    aux_path = tex_dir / f"{stem}.aux"
    bib_path = tex_dir / "references.bib"
    if aux_path.exists() and bib_path.exists() and shutil.which("bibtex"):
        run_and_log(["bibtex", stem], tex_dir, log_path, env)

    return (
        run_and_log(latex_cmd, tex_dir, log_path, env) == 0
        and run_and_log(latex_cmd, tex_dir, log_path, env) == 0
    )


def write_uplatex_source(tex_dir: Path, stem: str) -> str:
    source = tex_dir / f"{stem}.tex"
    fallback_stem = f"{stem}.uplatex"
    fallback = tex_dir / f"{fallback_stem}.tex"
    lines: List[str] = []
    for line in source.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("% Compile with LuaLaTeX"):
            lines.append("% Local fallback compile with upLaTeX + dvipdfmx.")
        elif re.match(r"\\documentclass(?:\[[^\]]*\])?\{ltjsarticle\}", stripped):
            lines.append(r"\documentclass[uplatex,dvipdfmx,ja=standard,11pt,a4paper]{bxjsarticle}")
        elif stripped == r"\usepackage{luatexja}":
            continue
        elif stripped.startswith(r"\usepackage") and "luatexja-preset" in stripped:
            lines.append(r"\usepackage[haranoaji]{pxchfon}")
        elif stripped == r"\usepackage{hyperref}":
            lines.append(r"\usepackage[dvipdfmx]{hyperref}")
            lines.append(r"\usepackage{pxjahyper}")
        else:
            lines.append(line)
    fallback.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return fallback_stem


def compile_ja_with_uplatex(tex_dir: Path, stem: str, log_path: Path) -> bool:
    env = latex_environment(tex_dir)
    fallback_stem = write_uplatex_source(tex_dir, stem)
    tex_name = f"{fallback_stem}.tex"
    latex_cmd = ["uplatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", tex_name]
    if run_and_log(latex_cmd, tex_dir, log_path, env) != 0:
        return False

    aux_path = tex_dir / f"{fallback_stem}.aux"
    bib_path = tex_dir / "references.bib"
    if aux_path.exists() and bib_path.exists() and shutil.which("bibtex"):
        run_and_log(["bibtex", fallback_stem], tex_dir, log_path, env)

    if run_and_log(latex_cmd, tex_dir, log_path, env) != 0:
        return False
    if run_and_log(latex_cmd, tex_dir, log_path, env) != 0:
        return False
    if run_and_log(["dvipdfmx", f"{fallback_stem}.dvi"], tex_dir, log_path, env) != 0:
        return False

    fallback_pdf = tex_dir / f"{fallback_stem}.pdf"
    if fallback_pdf.exists():
        target_pdf = tex_dir / f"{stem}.pdf"
        if target_pdf.exists():
            target_pdf.unlink()
        fallback_pdf.replace(target_pdf)
        return True
    return False


def compile_doc(run_dir: Path, stem: str, lang: str) -> Tuple[str, bool]:
    tex_dir = run_dir / "tex"
    tex_path = tex_dir / f"{stem}.tex"
    pdf_path = tex_dir / f"{stem}.pdf"
    log_dir = tex_dir / "build_logs"
    log_path = log_dir / f"{stem}.compile.log"

    if not tex_path.exists():
        return f"skip: {tex_path} does not exist", True

    candidates = engine_candidates(lang)
    if not candidates:
        detail = "LuaLaTeX or upLaTeX+dvipdfmx is required for Japanese" if lang == "ja" else "no supported LaTeX engine found"
        return f"skip: {stem}.pdf ({detail})", True

    log_dir.mkdir(parents=True, exist_ok=True)
    clean_intermediates(tex_dir, [stem, f"{stem}.uplatex"])
    log_path.write_text(f"# LaTeX build log for {stem}\n\n", encoding="utf-8")
    for engine in candidates:
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"## Attempt: {engine}\n\n")
        if engine == "uplatex":
            ok = compile_ja_with_uplatex(tex_dir, stem, log_path)
        else:
            ok = compile_with_engine(tex_dir, stem, engine, log_path)
        if ok and pdf_path.exists():
            return f"wrote {pdf_path}", True

    return f"fail: {stem}.pdf (see {log_path})", False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, help="Run directory")
    args = parser.parse_args()
    run_dir = Path(args.run)

    all_ok = True
    for stem, lang in DOCS:
        message, ok = compile_doc(run_dir, stem, lang)
        print(message)
        all_ok = all_ok and ok

    raise SystemExit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
