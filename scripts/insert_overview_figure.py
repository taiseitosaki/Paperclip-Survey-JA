#!/usr/bin/env python3
"""Copy an overview figure into a run directory and insert a Markdown image block.

This helper is optional. It does not replace the need to mention the figure in the
main text and to record a figure audit.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def insert_block(text: str, image_rel: str, caption: str, lang: str) -> str:
    if image_rel in text:
        return text
    block = f"![{caption}]({image_rel})\n\n"
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
    parser.add_argument("--image", required=True)
    parser.add_argument("--caption", default="Figure 1. Overview of the surveyed field.")
    args = parser.parse_args()

    run_dir = Path(args.run)
    src = Path(args.image)
    if not src.exists():
        raise SystemExit(f"image not found: {src}")
    if src.suffix.lower() not in SUPPORTED_EXTS:
        raise SystemExit(f"unsupported image extension: {src.suffix}")

    dst = run_dir / "figures" / f"overview_figure{src.suffix.lower()}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    image_rel = "../figures/" + dst.name

    for stem, lang in [("survey_en.md", "en"), ("survey_ja.md", "ja")]:
        path = run_dir / "drafts" / stem
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        new_text = insert_block(text, image_rel, args.caption, lang)
        path.write_text(new_text, encoding="utf-8")
        print(f"updated {path}")

    print(f"copied {src} -> {dst}")


if __name__ == "__main__":
    main()
