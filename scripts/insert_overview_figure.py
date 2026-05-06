#!/usr/bin/env python3
"""Copy or reuse an accepted overview figure and insert a Markdown image block.

This helper finalizes the figure produced by the preferred Codex image_gen route
or by the deterministic fallback. It does not replace the need to mention the
figure in the main text and to record a figure audit.
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
from typing import Optional

SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
OVERVIEW_EXTS = [".png", ".jpg", ".jpeg", ".webp"]
OVERVIEW_IMAGE_RE = re.compile(r"(?im)^!\[[^\]]*\]\((?:[^)]*/)?overview_figure[^)]*\)[ \t]*(?:\n[ \t]*)*")


def find_overview_figure(run_dir: Path) -> Optional[Path]:
    fig_dir = run_dir / "figures"
    for ext in OVERVIEW_EXTS:
        path = fig_dir / f"overview_figure{ext}"
        if path.exists():
            return path
    return None


def resolve_image_arg(image: str, run_dir: Path) -> Optional[Path]:
    if not image.strip():
        return None
    raw = Path(image).expanduser()
    candidates = [raw]
    if not raw.is_absolute():
        candidates.append(run_dir / "figures" / raw)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise SystemExit(f"image not found: {image}")


def accepted_figure_path(run_dir: Path, image: str) -> Path:
    src = resolve_image_arg(image, run_dir)
    if src is None:
        existing = find_overview_figure(run_dir)
        if existing:
            return existing
        raise SystemExit(
            "No accepted overview figure found. Provide --image with the selected "
            "image_gen output, or save it as figures/overview_figure.<png|jpg|jpeg|webp>."
        )
    if src.suffix.lower() not in SUPPORTED_EXTS:
        raise SystemExit(f"unsupported image extension: {src.suffix}")

    dst = run_dir / "figures" / f"overview_figure{src.suffix.lower()}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() != dst.resolve():
        shutil.copy2(src, dst)
        print(f"copied {src} -> {dst}")
    else:
        print(f"using existing {dst}")
    return dst


def insert_block(text: str, image_rel: str, caption: str, lang: str) -> str:
    block = f"![{caption}]({image_rel})\n"
    if OVERVIEW_IMAGE_RE.search(text):
        return OVERVIEW_IMAGE_RE.sub(block + "\n", text, count=1)
    if image_rel in text:
        return text
    block += "\n"
    if lang == "ja":
        mention = "図1は、本サーベイで扱う主要な分類軸または構造を概観する。\n\n"
    else:
        mention = "Figure 1 provides a high-level overview of the surveyed field and its organizing structure.\n\n"
    for heading in ["## Introduction", "## はじめに", "## 背景"]:
        idx = text.find(heading)
        if idx != -1:
            return text[:idx] + block + mention + text[idx:]
    return text.rstrip() + "\n\n" + block + mention


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument(
        "--image",
        default="",
        help=(
            "Selected overview figure. If omitted, reuse figures/overview_figure.<png|jpg|jpeg|webp>. "
            "Pass the image_gen output here after candidate selection."
        ),
    )
    parser.add_argument("--caption", default="Figure 1. Overview of the surveyed field.")
    args = parser.parse_args()

    run_dir = Path(args.run)
    dst = accepted_figure_path(run_dir, args.image)
    image_rel = "../figures/" + dst.name

    for stem, lang in [("survey_en.md", "en"), ("survey_ja.md", "ja")]:
        path = run_dir / "drafts" / stem
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        new_text = insert_block(text, image_rel, args.caption, lang)
        path.write_text(new_text, encoding="utf-8")
        print(f"updated {path}")

    print(f"accepted overview figure: {dst}")


if __name__ == "__main__":
    main()
