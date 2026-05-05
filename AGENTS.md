# Project instructions: Paperclip + Codex survey writing

This project builds high-quality, auditable, domain-general survey papers from a user-supplied topic. The workflow must prefer evidence density, coverage, and technical synthesis over superficial cleanliness.

Paperclip is a major retrieval component, but it is not the only one. The Codex app's built-in web search must also be used and integrated. Treat the final survey as a triangulated product of:

1. Paperclip retrieval and full-text reading.
2. Codex built-in web search for discovery, triangulation, and metadata verification.
3. Structured evidence extraction.
4. Academic writing and post-translation language polishing.
5. Figure generation and figure audit.

## Non-negotiable output rule

Never write new survey outputs directly under `outputs/searches`, `outputs/evidence`, `outputs/drafts`, etc.

Every run must live under:

```text
outputs/runs/<YYYYMMDD-HHMMSS-topic-slug>/
```

Before doing any literature work, run:

```bash
python3 scripts/init_run.py --topic "<exact user topic or prompt>"
```

Use the printed run path for every subsequent file. `outputs/latest` may point to the current run, but it is only a convenience symlink.

## Language policy

- Work notes, search strategy, evidence extraction, and the first full manuscript draft must be in English.
- The English manuscript must be written using the `academic-writing` skill.
- Create the English survey first: `drafts/survey_en.md`.
- Only after the English version passes citation audit should you create the Japanese version.
- The Japanese manuscript must be created in two stages:
  1. faithful translation from the English manuscript;
  2. polishing into formal academic Japanese using the `academic-ja-polish` skill.
- The Japanese version must preserve all citation IDs, section structure, tables, figure references, and technical terminology where translating would reduce precision.
- Do not mix English prose into the Japanese version except for model names, datasets, paper titles, mathematical terms, figure file names, and standard technical vocabulary.

## Search and triangulation policy

Search must not rely on Paperclip alone.

For every run, perform both:

- Paperclip search and follow-up reading.
- Codex built-in web search for query expansion, missing-term discovery, publication-status verification, landmark discovery, and candidate triangulation.

The web search layer is especially important for:

- identifying broader umbrella terms and adjacent terminology;
- finding peer-reviewed versions of preprints;
- discovering papers that Paperclip coverage might miss;
- confirming venue, DOI, year, or later publication status;
- finding papers cited by reviews that should be directly located and read.

All web-search work must be logged under `web/` and integrated into the main candidate table. Do not treat web results as a replacement for evidence extraction; use them to improve recall and metadata fidelity.

## Citation and evidence policy

- Every citation-bearing claim must be supported by an evidence card in `evidence/evidence_cards.jsonl`.
- Citation IDs must use `C001`, `C002`, ... and map one-to-one to evidence cards.
- Markdown citations should be written as linked references in the final linked files, e.g. `[[C001]](#ref-C001)`.
- The reference list must contain matching anchors, e.g. `<a id="ref-C001"></a>[C001] ...`.
- Do not use a paper merely because another paper cites it. Locate it directly using Paperclip, web search, or another documented source and make an evidence card.
- Do not cite malformed `map` output. If Paperclip `map` fails or returns weak output, recover by reading metadata, abstract, sections, full text, figures, or external bibliographic records when available.
- Do not allow clean structure to mask shallow content.

## Inclusion and screening policy

- Do not exclude a relevant paper only because it is a preprint.
- For preprints, explicitly record `publication_status`, `venue_status`, and whether a later peer-reviewed version was found.
- Use tiers instead of premature exclusion:
  - `core`: central paper that should likely be cited and explained.
  - `adjacent`: relevant background or neighboring method; may be cited.
  - `context`: useful for framing or history.
  - `out_of_scope`: clearly not relevant; reason required.
- The default is to keep papers in `core`, `adjacent`, or `context` until coverage audit is complete.
- A paper can be excluded only with a concrete topical reason, not because it is inconvenient, recent, preprint, or methodologically imperfect.

## Coverage policy

A thin survey is unacceptable even if the structure is clean. Use these thresholds as warnings, not as arbitrary padding targets:

- If initial search returns >= 150 deduplicated candidates, create at least 50 evidence cards unless the coverage audit documents why fewer are genuinely relevant.
- If initial search returns 50-149 candidates, create at least 30 evidence cards unless justified.
- If initial search returns < 50 candidates, broaden queries and run at least one expansion round.
- If final cited papers are fewer than 20, the survey must be labeled as a rapid mini-review, not a full survey.
- In mature fields, explain why landmark papers, early methods, recent variants, evaluation papers, datasets/benchmarks, and critiques were included or not included.

## Subagent policy

For complex survey tasks, explicitly spawn or ask Codex to spawn focused subagents when available:

- `survey_query_strategist`: generates and critiques search terms.
- `survey_web_search_integrator`: runs and integrates Codex built-in web search with Paperclip results.
- `survey_coverage_auditor`: checks missing subfields, landmarks, and over-filtering.
- `survey_paper_reader`: reads batches of papers deeply and returns structured evidence.
- `survey_citation_auditor`: verifies that each claim is supported by cited evidence.
- `survey_figure_auditor`: reviews overview-figure quality, academic suitability, and textual fit.

Subagents should return structured outputs, not prose-only opinions.

## Drafting policy

- Do not draft before evidence cards and taxonomy exist.
- The English manuscript must be drafted with the `academic-writing` skill.
- For every cited paper, include enough technical detail to explain why it matters: contribution, architecture/method, data/task, evaluation, novelty, and limitation.
- Avoid list-like summaries. Synthesize across papers and explain conceptual relations.
- Include disagreements, negative results, evaluation weaknesses, and deployment limitations.
- Separate settled findings from emerging or weakly supported claims.
- The Japanese manuscript must be polished after translation with the `academic-ja-polish` skill.

## Overview-figure policy

An overview figure is mandatory once the English manuscript is substantively complete.

Requirements:

- The figure should be in English, even if the Japanese manuscript is also produced.
- It should communicate the field clearly in academic style. Typical contents include taxonomy, timeline, methodological landscape, data/task axes, or a survey workflow map, depending on what best fits the draft.
- The figure must be created from the survey content, not as generic decoration.
- Use the `overview-figure` skill and an image-generation tool if available.
- Store the prompt brief in `figures/overview_figure_prompt.md`.
- Store the accepted figure under `figures/overview_figure.<ext>`.
- The figure must be audited by `survey_figure_auditor`. The audit goes to `reports/figure_audit.md`.
- Only after the figure is accepted should it be inserted into `drafts/survey_en.md` and `drafts/survey_ja.md`, and then carried through to linked Markdown and TeX.
- The manuscript must mention the figure in the main text and explain what it shows.

## TeX policy

After both Markdown surveys and the figure are complete, run:

```bash
python3 scripts/link_markdown_refs.py --run <run-dir>
python3 scripts/render_tex_bib.py --run <run-dir>
python3 scripts/validate_outputs.py --run <run-dir>
```

The English and Japanese TeX files must be generated under `tex/` with a shared `references.bib`. If a figure is present, it must also be copied into `tex/figures/` and referenced from the TeX sources. The TeX files should compile on Overleaf with a standard bibliography workflow. For Japanese, prefer LuaLaTeX.
