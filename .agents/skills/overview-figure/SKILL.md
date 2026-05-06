---
name: overview-figure
description: Design a high-quality academic overview figure for a survey manuscript using content distillation, layout specification, Codex image_gen first, deterministic/vector fallback only when image_gen cannot be invoked, candidate selection, and figure audit.
---

# Overview Figure Skill

Use this skill after the survey manuscript is substantively complete.

## Objective

Create a single overview figure that improves reader orientation in the survey paper.

The default failure mode is a low-information-quality **box farm**: many equally sized rectangles, long bullet lists, weak hierarchy, and generic arrows. Avoid that pattern.

For conceptual survey figures that are mostly boxes, arrows, and short labels, the preferred workflow is:

1. distill the manuscript into a figure spec;
2. choose a layout archetype;
3. construct at least two candidates with Codex `image_gen`;
4. audit the candidates;
5. select one candidate and integrate it into Markdown and TeX.

## Inputs

- English survey draft.
- Taxonomy and comparative table.
- Candidate/evidence summaries when they clarify which concepts are central.
- Figure purpose: taxonomy map, timeline, landscape diagram, workflow, or other academically justified summary.

## Phase 1: Figure claim and content distillation

Before generating or drawing any figure, create `figures/overview_figure_spec.md`.

The spec must include:

- one-sentence figure claim: what the figure should make clear;
- one-sentence reader takeaway;
- chosen layout archetype;
- dominant panel;
- secondary panels;
- node list with concise labels;
- edge list with arrow semantics;
- representative examples per node;
- content deliberately omitted from the figure because it belongs in prose or a table;
- caption draft.

### Hard content limits

- maximum 8 major nodes;
- maximum 12 arrows;
- maximum 35 words inside any major node;
- maximum 3 example items per node;
- arrow labels should usually be 0--2 words;
- no full sentences inside nodes unless absolutely necessary;
- no long lists of paper titles;
- no design that merely mirrors the manuscript section outline.

## Phase 2: Choose a layout archetype

Choose the layout that best matches the figure claim. Typical options:

- **centered taxonomy**: one dominant central panel, small context panels at the sides;
- **pipeline with cross-cutting constraints**: main flow plus top/bottom ribbons for design/evaluation/risks;
- **timeline + taxonomy hybrid**: temporal strip plus grouped model families;
- **two-axis landscape**: model families arranged against task/data axes.

Do not use a pure left-to-right six-box sequence unless the field is genuinely a sequential pipeline.

## Phase 3: Rendering route

Use Codex `image_gen` as the first rendering route after the content has been distilled and the layout is explicit. The generation prompt must describe a journal-style vector schematic with the exact panel hierarchy, labels, arrows, and style constraints from `figures/overview_figure_spec.md`.

If `image_gen` succeeds, select one of the generated images, save it as `figures/overview_figure.<png|jpg|jpeg|webp>`, and do not run the deterministic/code-based renderer. After candidate selection, use `scripts/insert_overview_figure.py` to insert that accepted image into the Markdown drafts, then regenerate linked Markdown and TeX.

Do not choose the deterministic route merely because the figure is text-heavy. First attempt `image_gen`, then revise through `image_gen` if the first output needs correction. Use the deterministic vector/slide route only when `image_gen` is unavailable, blocked, or cannot be invoked in the current Codex environment.

Record `Rendering route: image_gen` in `figures/overview_figure_prompt.md` or `reports/figure_selection.md`. If falling back, explicitly write the fallback reason in `logs/codex_worklog.md` or `reports/figure_selection.md`.

### Fallback deterministic helper route

When `image_gen` cannot be invoked and the figure is a structured schematic, create `figures/overview_figure_spec.json` using `templates/overview_figure_spec.schema.json`, then render a candidate with:

```bash
python3 scripts/render_overview_figure.py \
  --run <RUN_DIR> \
  --spec <RUN_DIR>/figures/overview_figure_spec.json \
  --output overview_figure_candidate_a \
  --fallback-reason "<why image_gen could not be invoked>"
```

This writes both:

```text
figures/overview_figure_candidate_a.png
figures/overview_figure_candidate_a.svg
```

After selection, copy the accepted fallback candidate to `figures/overview_figure.png` or use `scripts/insert_overview_figure.py` with the selected image.

## Phase 4: Candidate generation

Generate at least two candidates and save them as, for example:

```text
figures/overview_figure_candidate_a.<ext>
figures/overview_figure_candidate_b.<ext>
```

Each candidate should follow these style constraints:

- white background;
- restrained academic palette;
- no decorative icons;
- no gradient-heavy infographic style;
- one dominant panel and two to four secondary panels;
- concise labels;
- strong alignment and whitespace;
- readable at manuscript scale.

## Output requirements

- The figure text should be in English.
- The figure should be academically styled: clean layout, readable labels, restrained visual language, no decorative clutter.
- It should convey real structure from the manuscript rather than generic icons.
- Save the generation brief to `figures/overview_figure_prompt.md`.
- Save the distilled figure spec to `figures/overview_figure_spec.md`.
- Save candidate figures under `figures/overview_figure_candidate_*.<ext>`.
- Save the accepted image as `figures/overview_figure.<ext>`.
- Save the selection rationale to `reports/figure_selection.md`.
- Ensure the manuscript refers to Figure 1 explicitly.

## Figure-design checklist

- What is the figure's exact communicative purpose?
- Which concepts, groups, or phases must be shown?
- What should be omitted to avoid clutter?
- Will the figure still make sense to a reader who has not yet read the full survey?
- Are labels short, accurate, and readable?
- Does the figure match the taxonomy used in the text?
- Is one panel visually dominant?
- Is the figure understandable within 10--15 seconds?
- Is the figure saying something more useful than a table of section headings?
- Has the equal-size bullet-box-farm failure mode been avoided?

## Audit integration

After generation, send the figure and its description to `survey_figure_auditor`.
Only adopt the figure if the auditor accepts it or accepts it after revision.

If both candidates are weak, redesign the spec instead of merely tweaking colors.
