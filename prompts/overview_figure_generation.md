# Overview figure generation prompt

Create an academic overview figure only after the survey manuscript is substantively complete.

This must be a two-stage process.

## Stage 1: plan the figure

Before drawing, create `figures/overview_figure_spec.md` and fill in:

- figure claim: one sentence;
- reader takeaway: one sentence;
- layout archetype;
- dominant panel;
- secondary panels;
- node list;
- edge list;
- representative examples per node (max 3);
- content deliberately omitted from the figure;
- caption draft.

Hard limits:

- <= 8 major nodes;
- <= 12 arrows;
- <= 35 words in any node;
- <= 3 example items per node;
- no long arrow labels;
- no paper-title walls;
- no equal-size dense box farm.

## Stage 2: generate candidates

Generate at least two candidate figures.

Use Codex `image_gen` as the preferred rendering route after the figure is content-distilled and layout-constrained. The prompt should request a journal-style vector schematic, not a consumer infographic, and should include the exact layout, panel hierarchy, labels, arrow semantics, and style constraints from `figures/overview_figure_spec.md`.

If `image_gen` succeeds, use the selected image_gen output as `figures/overview_figure.<png|jpg|jpeg|webp>` and do not run any code-based figure renderer. Record `Rendering route: image_gen` in `figures/overview_figure_prompt.md` or `reports/figure_selection.md`.

Do not use the deterministic vector/slide route unless `image_gen` is unavailable, blocked, or cannot be invoked in the current environment. If falling back, record the reason in `logs/codex_worklog.md` or `reports/figure_selection.md`.

If falling back to the deterministic helper, create `figures/overview_figure_spec.json` using `templates/overview_figure_spec.schema.json`, then run:

```bash
python3 scripts/render_overview_figure.py \
  --run <RUN_DIR> \
  --spec <RUN_DIR>/figures/overview_figure_spec.json \
  --output overview_figure_candidate_a \
  --fallback-reason "<why image_gen could not be invoked>"
```

Stylistic requirements:

- journal-style vector schematic, not a consumer infographic;
- white background;
- restrained palette;
- strong visual hierarchy;
- one dominant panel and smaller context/constraint panels;
- no decorative icons;
- no dense bullet walls.

Save:

- `figures/overview_figure_prompt.md`
- `figures/overview_figure_spec.md`
- `figures/overview_figure_candidate_a.<ext>`
- `figures/overview_figure_candidate_b.<ext>`
- `figures/overview_figure.<ext>` (accepted final)
- `reports/figure_selection.md`

After selecting the accepted image, run `python3 scripts/insert_overview_figure.py --run <RUN_DIR> --image <selected-image-gen-output> --caption "Figure 1. ..."` so the image_gen figure is carried into the Markdown drafts. Then regenerate linked Markdown, TeX, and PDFs if local LaTeX tools are available.

Ensure the manuscript refers to Figure 1 / 図1 explicitly.
