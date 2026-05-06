#!/usr/bin/env python3
"""Render a deterministic academic overview figure from a JSON spec.

This is a fallback route. The normal overview-figure workflow must try Codex
image_gen first and use its accepted image when that succeeds. Only run this
helper when image_gen is unavailable, blocked, or cannot be invoked in the
current environment. The script renders an editable SVG and a manuscript-ready
PNG under RUN_DIR/figures/.

Example:
    python3 scripts/render_overview_figure.py \
      --run outputs/runs/<run-id> \
      --spec outputs/runs/<run-id>/figures/overview_figure_spec.json \
      --output overview_figure_candidate_a \
      --fallback-reason "image_gen cannot be invoked in this environment"
"""
from __future__ import annotations

import argparse
import json
import math
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover - only hit when dependency is absent
    raise SystemExit(
        "Pillow is required for deterministic figure rendering. Install with: pip install -r requirements.txt"
    ) from exc

Color = Tuple[int, int, int]

ROLE_COLORS: Dict[str, Tuple[Color, Color]] = {
    "dominant": ((255, 246, 225), (83, 71, 42)),
    "context": ((236, 246, 255), (51, 69, 92)),
    "substrate": ((236, 248, 239), (49, 83, 65)),
    "design": ((243, 238, 252), (72, 59, 92)),
    "evaluation": ((255, 239, 238), (93, 60, 60)),
    "risk": ((243, 246, 250), (63, 73, 87)),
    "default": ((248, 249, 251), (64, 74, 88)),
}
TEXT = (22, 30, 45)
MUTED = (83, 96, 116)
ARROW = (58, 72, 92)
BACKGROUND = (255, 255, 255)
FINAL_FIGURE_EXTS = [".png", ".jpg", ".jpeg", ".webp"]

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Helvetica.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
]
BOLD_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
]


def load_font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    candidates = BOLD_FONT_CANDIDATES if bold else FONT_CANDIDATES
    for candidate in candidates:
        p = Path(candidate)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size=size)
            except OSError:
                pass
    return ImageFont.load_default()


@dataclass
class Panel:
    id: str
    title: str
    x: float
    y: float
    w: float
    h: float
    role: str
    items: List[str]
    subtitle: str = ""

    def rect(self, width: int, height: int) -> Tuple[int, int, int, int]:
        return (
            int(self.x * width),
            int(self.y * height),
            int((self.x + self.w) * width),
            int((self.y + self.h) * height),
        )

    def center(self, width: int, height: int) -> Tuple[float, float]:
        x0, y0, x1, y1 = self.rect(width, height)
        return ((x0 + x1) / 2, (y0 + y1) / 2)


def as_items(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        out = []
        for item in raw:
            if isinstance(item, dict):
                label = str(item.get("label") or item.get("text") or item)
            else:
                label = str(item)
            out.append(label)
        return out
    return [str(raw)]


def load_spec(path: Path) -> Dict[str, Any]:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON spec: {path}: {exc}") from exc
    if "panels" not in spec or not spec["panels"]:
        raise SystemExit("Spec must contain a non-empty `panels` list.")
    return spec


def build_panels(spec: Dict[str, Any]) -> Dict[str, Panel]:
    panels: Dict[str, Panel] = {}
    for index, raw in enumerate(spec.get("panels", []), 1):
        missing = [key for key in ["id", "title", "x", "y", "w", "h"] if key not in raw]
        if missing:
            raise SystemExit(f"Panel {index} is missing required fields: {', '.join(missing)}")
        panel = Panel(
            id=str(raw["id"]),
            title=str(raw["title"]),
            x=float(raw["x"]),
            y=float(raw["y"]),
            w=float(raw["w"]),
            h=float(raw["h"]),
            role=str(raw.get("role") or "default"),
            items=as_items(raw.get("items")),
            subtitle=str(raw.get("subtitle") or ""),
        )
        panels[panel.id] = panel
    return panels


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_to_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int, max_lines: int = 5) -> List[str]:
    if not text:
        return []
    words = text.split()
    if not words:
        return []
    lines: List[str] = []
    current: List[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        if text_size(draw, candidate, font)[0] <= width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
            if len(lines) >= max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(" ".join(current))
    if len(lines) == max_lines and len(" ".join(words)) > len(" ".join(lines)):
        lines[-1] = lines[-1].rstrip(".,;: ") + "…"
    return lines


def panel_edge_point(panel: Panel, target: Tuple[float, float], width: int, height: int) -> Tuple[float, float]:
    x0, y0, x1, y1 = panel.rect(width, height)
    cx, cy = panel.center(width, height)
    tx, ty = target
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    candidates: List[Tuple[float, float, float]] = []
    if dx != 0:
        for x in (x0, x1):
            t = (x - cx) / dx
            y = cy + t * dy
            if t > 0 and y0 <= y <= y1:
                candidates.append((t, x, y))
    if dy != 0:
        for y in (y0, y1):
            t = (y - cy) / dy
            x = cx + t * dx
            if t > 0 and x0 <= x <= x1:
                candidates.append((t, x, y))
    if candidates:
        _, x, y = min(candidates, key=lambda z: z[0])
        return x, y
    return cx, cy


def draw_arrow(draw: ImageDraw.ImageDraw, start: Tuple[float, float], end: Tuple[float, float], label: str, font: ImageFont.ImageFont) -> None:
    sx, sy = start
    ex, ey = end
    dx, dy = ex - sx, ey - sy
    length = max(math.hypot(dx, dy), 1.0)
    ux, uy = dx / length, dy / length
    # inset from panel borders
    sx += ux * 12
    sy += uy * 12
    ex -= ux * 12
    ey -= uy * 12
    draw.line((sx, sy, ex, ey), fill=ARROW, width=4)
    head = 18
    angle = math.atan2(ey - sy, ex - sx)
    p1 = (ex - head * math.cos(angle - math.pi / 7), ey - head * math.sin(angle - math.pi / 7))
    p2 = (ex - head * math.cos(angle + math.pi / 7), ey - head * math.sin(angle + math.pi / 7))
    draw.polygon([(ex, ey), p1, p2], fill=ARROW)
    if label:
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        tw, th = text_size(draw, label, font)
        pad = 8
        draw.rounded_rectangle((mx - tw / 2 - pad, my - th / 2 - pad, mx + tw / 2 + pad, my + th / 2 + pad), radius=10, fill=BACKGROUND)
        draw.text((mx - tw / 2, my - th / 2 - 1), label, fill=MUTED, font=font)


def draw_panel(draw: ImageDraw.ImageDraw, panel: Panel, width: int, height: int, fonts: Dict[str, ImageFont.ImageFont]) -> None:
    x0, y0, x1, y1 = panel.rect(width, height)
    fill, stroke = ROLE_COLORS.get(panel.role, ROLE_COLORS["default"])
    radius = 26 if panel.role == "dominant" else 20
    line_width = 5 if panel.role == "dominant" else 3
    draw.rounded_rectangle((x0, y0, x1, y1), radius=radius, fill=fill, outline=stroke, width=line_width)
    pad = 26
    cursor_y = y0 + pad
    title_font = fonts["panel_title_lg"] if panel.role == "dominant" else fonts["panel_title"]
    body_font = fonts["body_lg"] if panel.role == "dominant" else fonts["body"]
    for line in wrap_to_width(draw, panel.title, title_font, x1 - x0 - 2 * pad, max_lines=2):
        draw.text((x0 + pad, cursor_y), line, fill=TEXT, font=title_font)
        cursor_y += text_size(draw, line, title_font)[1] + 8
    if panel.subtitle:
        for line in wrap_to_width(draw, panel.subtitle, fonts["small"], x1 - x0 - 2 * pad, max_lines=2):
            draw.text((x0 + pad, cursor_y), line, fill=MUTED, font=fonts["small"])
            cursor_y += text_size(draw, line, fonts["small"])[1] + 6
    cursor_y += 8
    max_items = int(panel.h * height / 80)
    items = panel.items[: max(1, max_items)]
    if len(panel.items) > len(items):
        items[-1] = items[-1].rstrip(".,;: ") + " …"
    for item in items:
        bullet_x = x0 + pad
        first_line_y = cursor_y
        lines = wrap_to_width(draw, item, body_font, x1 - x0 - 2 * pad - 22, max_lines=3)
        if not lines:
            continue
        draw.ellipse((bullet_x, first_line_y + 10, bullet_x + 7, first_line_y + 17), fill=stroke)
        for line in lines:
            draw.text((x0 + pad + 20, cursor_y), line, fill=TEXT, font=body_font)
            cursor_y += text_size(draw, line, body_font)[1] + 5
        cursor_y += 7
        if cursor_y > y1 - pad:
            break


def render_png(spec: Dict[str, Any], out_path: Path) -> None:
    width = int(spec.get("width", 2200))
    height = int(spec.get("height", 1300))
    scale = int(spec.get("render_scale", 2))
    img = Image.new("RGB", (width * scale, height * scale), BACKGROUND)
    draw = ImageDraw.Draw(img)
    fonts = {
        "title": load_font(48 * scale, bold=True),
        "subtitle": load_font(28 * scale),
        "panel_title": load_font(28 * scale, bold=True),
        "panel_title_lg": load_font(32 * scale, bold=True),
        "body": load_font(22 * scale),
        "body_lg": load_font(23 * scale),
        "small": load_font(19 * scale),
        "arrow": load_font(18 * scale),
    }
    title = str(spec.get("title") or "Overview figure")
    subtitle = str(spec.get("subtitle") or "")
    title_w, title_h = text_size(draw, title, fonts["title"])
    draw.text(((width * scale - title_w) / 2, 38 * scale), title, fill=TEXT, font=fonts["title"])
    if subtitle:
        sub_w, sub_h = text_size(draw, subtitle, fonts["subtitle"])
        draw.text(((width * scale - sub_w) / 2, (38 + title_h / scale + 8) * scale), subtitle, fill=MUTED, font=fonts["subtitle"])

    panels = build_panels(spec)
    # Work in scaled normalized coordinates by scaling panel parameters.
    scaled_panels = {
        k: Panel(v.id, v.title, v.x, v.y, v.w, v.h, v.role, v.items, v.subtitle)
        for k, v in panels.items()
    }
    W, H = width * scale, height * scale
    # Draw arrows below panels but above background.
    for raw in spec.get("arrows", []):
        from_id = raw.get("from")
        to_id = raw.get("to")
        if from_id not in scaled_panels or to_id not in scaled_panels:
            continue
        a, b = scaled_panels[from_id], scaled_panels[to_id]
        b_center = b.center(W, H)
        a_center = a.center(W, H)
        start = panel_edge_point(a, b_center, W, H)
        end = panel_edge_point(b, a_center, W, H)
        draw_arrow(draw, start, end, str(raw.get("label") or ""), fonts["arrow"])

    for panel in scaled_panels.values():
        draw_panel(draw, panel, W, H, fonts)

    caption = spec.get("caption")
    if caption and spec.get("draw_caption", False):
        cap_font = fonts["small"]
        y = H - 58 * scale
        lines = wrap_to_width(draw, str(caption), cap_font, int(W * 0.86), max_lines=2)
        for line in lines:
            tw, th = text_size(draw, line, cap_font)
            draw.text(((W - tw) / 2, y), line, fill=MUTED, font=cap_font)
            y += th + 6

    if scale > 1:
        img = img.resize((width, height), Image.Resampling.LANCZOS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def svg_escape(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_svg(spec: Dict[str, Any], out_path: Path) -> None:
    width = int(spec.get("width", 2200))
    height = int(spec.get("height", 1300))
    panels = build_panels(spec)
    parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,4 L0,8 z" fill="#3a485c"/></marker></defs>',
    ]
    title = svg_escape(spec.get("title") or "Overview figure")
    subtitle = svg_escape(spec.get("subtitle") or "")
    parts.append(f'<text x="{width/2}" y="68" text-anchor="middle" font-family="Arial, sans-serif" font-weight="700" font-size="48" fill="#161e2d">{title}</text>')
    if subtitle:
        parts.append(f'<text x="{width/2}" y="106" text-anchor="middle" font-family="Arial, sans-serif" font-size="28" fill="#536074">{subtitle}</text>')
    for raw in spec.get("arrows", []):
        from_id, to_id = raw.get("from"), raw.get("to")
        if from_id not in panels or to_id not in panels:
            continue
        a, b = panels[from_id], panels[to_id]
        start = panel_edge_point(a, b.center(width, height), width, height)
        end = panel_edge_point(b, a.center(width, height), width, height)
        parts.append(f'<line x1="{start[0]:.1f}" y1="{start[1]:.1f}" x2="{end[0]:.1f}" y2="{end[1]:.1f}" stroke="#3a485c" stroke-width="3" marker-end="url(#arrow)"/>')
    for panel in panels.values():
        x0, y0, x1, y1 = panel.rect(width, height)
        fill, stroke = ROLE_COLORS.get(panel.role, ROLE_COLORS["default"])
        fill_hex = "#%02x%02x%02x" % fill
        stroke_hex = "#%02x%02x%02x" % stroke
        parts.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" rx="20" fill="{fill_hex}" stroke="{stroke_hex}" stroke-width="3"/>')
        parts.append(f'<text x="{x0+26}" y="{y0+42}" font-family="Arial, sans-serif" font-weight="700" font-size="26" fill="#161e2d">{svg_escape(panel.title)}</text>')
        yy = y0 + 82
        for item in panel.items[:5]:
            parts.append(f'<text x="{x0+36}" y="{yy}" font-family="Arial, sans-serif" font-size="20" fill="#161e2d">• {svg_escape(item)}</text>')
            yy += 30
    parts.append("</svg>")
    out_path.write_text("\n".join(parts), encoding="utf-8")


def accepted_overview_figure_exists(run_dir: Path) -> bool:
    fig_dir = run_dir / "figures"
    return any((fig_dir / f"overview_figure{ext}").exists() for ext in FINAL_FIGURE_EXTS)


def record_fallback_reason(run_dir: Path, reason: str) -> None:
    log_path = run_dir / "logs" / "codex_worklog.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"\n- {timestamp}: overview figure fallback renderer used. Reason: {reason}\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, help="Run directory")
    parser.add_argument("--spec", help="JSON figure spec. Defaults to RUN/figures/overview_figure_spec.json")
    parser.add_argument("--output", default="overview_figure_candidate_a", help="Base output name without extension")
    parser.add_argument(
        "--fallback-reason",
        required=True,
        help="Why Codex image_gen could not be used. Required because this renderer is fallback-only.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow fallback rendering even if figures/overview_figure.<ext> already exists.",
    )
    args = parser.parse_args()

    run_dir = Path(args.run)
    if accepted_overview_figure_exists(run_dir) and not args.force:
        raise SystemExit(
            "Accepted overview_figure.<ext> already exists. Use that image in Markdown/TeX; "
            "do not run the deterministic fallback unless you pass --force with a documented reason."
        )
    spec_path = Path(args.spec) if args.spec else run_dir / "figures" / "overview_figure_spec.json"
    spec = load_spec(spec_path)
    out_base = run_dir / "figures" / args.output
    render_png(spec, out_base.with_suffix(".png"))
    render_svg(spec, out_base.with_suffix(".svg"))
    record_fallback_reason(run_dir, args.fallback_reason)
    print(f"wrote {out_base.with_suffix('.png')}")
    print(f"wrote {out_base.with_suffix('.svg')}")


if __name__ == "__main__":
    main()
