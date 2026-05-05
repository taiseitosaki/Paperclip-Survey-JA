---
name: overview-figure
description: Design an academic overview figure for a survey manuscript, generate it with an image-generation tool when available, and prepare it for figure audit and manuscript insertion.
---

# Overview Figure Skill

Use this skill after the survey manuscript is substantively complete.

## Objective

Create a single overview figure that improves reader orientation in the survey paper.

## Inputs

- English survey draft.
- Taxonomy and comparative table.
- Figure purpose: taxonomy map, timeline, landscape diagram, workflow, or other academically justified summary.

## Output requirements

- The figure text should be in English.
- The figure should be academically styled: clean layout, readable labels, restrained visual language, no decorative clutter.
- It should convey real structure from the manuscript rather than generic icons.
- Save the generation brief to `figures/overview_figure_prompt.md`.
- Save the accepted image as `figures/overview_figure.<ext>`.
- Ensure the manuscript refers to Figure 1 explicitly.

## Figure-design checklist

- What is the figure's exact communicative purpose?
- Which concepts, groups, or phases must be shown?
- What should be omitted to avoid clutter?
- Will the figure still make sense to a reader who has not yet read the full survey?
- Are labels short, accurate, and readable?
- Does the figure match the taxonomy used in the text?

## Audit integration

After generation, send the figure and its description to `survey_figure_auditor`.
Only adopt the figure if the auditor accepts it or accepts it after revision.
