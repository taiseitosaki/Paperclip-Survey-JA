---
name: survey-paperclip
description: Create an auditable, high-coverage survey paper from a research topic using Paperclip, Codex built-in web search, iterative query expansion, evidence cards, academic English drafting, academic Japanese polishing, Markdown reference links, overview-figure creation, and Overleaf-ready TeX/BibTeX outputs.
---

# Survey Paperclip Skill v3

Use this skill when the user asks for a survey, scoping review, literature review, background review, technical survey, or research-map style paper.

The goal is not merely to produce a well-structured essay. The goal is to produce a dense, well-supported, auditable survey whose citations reflect the relevant literature found during search, and whose overview figure faithfully summarizes the manuscript.

## Mandatory first action

Create a run-specific output directory before any literature work:

```bash
python3 scripts/init_run.py --topic "<exact user topic or prompt>"
```

Use the printed `RUN_DIR`. All outputs must be under that directory.

Do not write into legacy flat directories such as `outputs/drafts/` or `outputs/evidence/`.

## Required final outputs

Under `RUN_DIR`, produce:

```text
run_manifest.json
prompt.txt
searches/query_plan_round1.csv
searches/query_plan_round2.csv
searches/deduped_candidates.csv
searches/screening_decisions.csv
searches/coverage_audit.md
web/web_query_plan_round1.md
web/web_query_plan_round2.md
web/web_search_log.md
web/triangulated_candidates.csv
web/integrated_search_summary.md
evidence/evidence_cards.jsonl
evidence/paper_reading_status.csv
extractions/comparative_table.csv
extractions/taxonomy.md
refs/references.md
refs/references.jsonl
drafts/survey_en.md
drafts/survey_ja.md
drafts/survey_en.linked.md
drafts/survey_ja.linked.md
figures/overview_figure_prompt.md
figures/overview_figure_spec.md
figures/overview_figure_candidate_a.<png|jpg|jpeg|webp|svg>
figures/overview_figure_candidate_b.<png|jpg|jpeg|webp|svg>
figures/overview_figure.<png|jpg|jpeg|webp>
tex/survey_en.tex
tex/survey_ja.tex
tex/references.bib
tex/survey_en.pdf  # if local LaTeX is available
tex/survey_ja.pdf  # if local LuaLaTeX or upLaTeX+dvipdfmx is available
reports/protocol.md
reports/methods.md
reports/claim_audit.md
reports/figure_audit.md
reports/figure_selection.md
reports/limitations.md
reports/validation_report.md
logs/paperclip_commands.md
logs/codex_worklog.md
```

## Workflow overview

1. Initialize a run directory.
2. Convert the user topic into review questions and scope.
3. Generate broad, synonym-rich search queries.
4. Run Paperclip searches and preserve all handles/logs.
5. Run Codex built-in web searches and log them.
6. Deduplicate and tier candidates; do not over-filter.
7. Run query expansion from discovered terms, landmarks, reviews, and draft gaps.
8. Deep-read core and adjacent papers into evidence cards.
9. Build taxonomy and comparative tables.
10. Draft the English survey using the `academic-writing` skill.
11. Audit coverage and citation support.
12. Translate the English survey into Japanese and then polish it with the `academic-ja-polish` skill.
13. Create a figure spec, generate at least two overview-figure candidates using the `overview-figure` skill, and audit them with `survey_figure_auditor`.
14. Select the accepted figure, record the selection rationale, insert it into the survey drafts, generate linked Markdown, TeX, BibTeX, and validation report.

## Step 1: Topic decomposition

Write `reports/protocol.md` with:

- original prompt;
- review type: narrative survey, scoping review, systematic review, or rapid review;
- 3-7 review questions;
- expected subfields;
- likely landmark papers or method names if known;
- inclusion tiers: core, adjacent, context, out_of_scope;
- known limitations of Paperclip coverage for the topic.

Do not assume the input field is biomedical. If the topic is outside Paperclip's strongest corpus, state that explicitly and compensate with stronger web-search recall.

## Step 2: Query strategy

Before searching, generate `searches/query_plan_round1.csv` with columns:

```text
query_id,query,query_type,rationale,expected_subfield,broadness,mandatory_terms,optional_terms
```

Also generate `web/web_query_plan_round1.md` that records the web-search plan. Include broad umbrella terms, exact user terms, synonyms, predecessor methods, model families, benchmarks, datasets, evaluation terms, limitations, critique terms, and adjacent terminology.

The query set must include:

- broad umbrella terms;
- exact user terms;
- synonyms and alternate spellings;
- predecessor methods and historical terminology;
- named model families, datasets, benchmarks, and tasks;
- critique/evaluation/deployment terms;
- review/meta-analysis/scoping-review terms;
- if applicable, standards/ontologies/common data models.

Use at least 12 queries for ordinary topics and at least 20 queries for broad or mature fields.

Use Paperclip commands such as:

```bash
paperclip searches \
  "<broad query 1>" \
  "<broad query 2>" \
  "<targeted query 3>" \
  ...
```

Also use `paperclip lookup` for named papers, authors, DOI/PMID/PMC/arXiv IDs, or landmark titles discovered during the process.

Append every Paperclip command and handle to `logs/paperclip_commands.md`.

## Step 3: Web-search integration

Use the Codex app's built-in web search as an integrated recall and verification layer.

Write to:

- `web/web_search_log.md`
- `web/triangulated_candidates.csv`
- `web/integrated_search_summary.md`

The web layer must be used to:

- discover broader and adjacent terminology;
- identify papers not surfaced by initial Paperclip search;
- find later peer-reviewed versions of preprints;
- confirm metadata such as venue, DOI, year, and publication status;
- identify key review papers and landmark references that should be directly located.

Do not let web search remain a side note. Merge web-only and Paperclip-only candidates into the main candidate pool and document discovery source.

## Step 4: Screening without premature exclusion

Create `searches/deduped_candidates.csv` and `searches/screening_decisions.csv`.

Screening decisions must use tiers:

```text
candidate_id,title,authors,year,source,doi,url,discovery_source,first_seen_query_ids,tier,reason,preprint_status,publication_status_checked,notes
```

Rules:

- Preprint status is not an exclusion reason.
- Malformed map output is not an exclusion reason; it is a signal to recover evidence by another read path.
- Keep potentially relevant papers in `core`, `adjacent`, or `context` until coverage audit.
- `out_of_scope` requires a concrete topical reason.
- Do not collapse the field to only 10-20 papers if many relevant candidates exist.

## Step 5: First evidence extraction

For `core` and high-value `adjacent` candidates, create evidence cards in `evidence/evidence_cards.jsonl` using `templates/evidence_card.schema.json`.

Each evidence card must explain:

- what the paper contributes;
- architecture/method/model/dataset/task details;
- why the contribution is novel or historically important;
- what limitation or caveat matters;
- what exact review claims the paper can support;
- publication status, including preprint and later venue information where found.

A thin one-sentence evidence card is not acceptable for a cited technical paper.

Suggested Paperclip map prompt:

```text
For each paper, return a JSON object for a survey evidence card. Focus on the mapped paper itself, not papers it cites. Include: title, authors, year, source, DOI/PMID/PMCID/arXiv ID, publication_status, later_peer_reviewed_version_if_any, topical_role, contribution, technical_details, architecture_or_method, data_or_corpus, objective_or_training_signal, evaluation_tasks, quantitative_results_if_supported, novelty, limitations, importance_for_survey, related_terms, candidate_tier, should_cite, and supported_claims. Do not infer beyond available text. If only abstract is available, mark evidence_scope='abstract-only'.
```

If Paperclip `map` returns weak or malformed entries, recover manually with:

```bash
paperclip cat /papers/<id>/meta.json
paperclip head -80 /papers/<id>/content.lines
paperclip ls /papers/<id>/sections/
paperclip grep -i "method|model|dataset|result|limitation|benchmark|evaluation" /papers/<id>/content.lines
```

Use `survey_paper_reader` subagents for batches of core papers when available.

## Step 6: Query expansion and coverage audit

After round 1 extraction, write `searches/coverage_audit.md`.

The coverage auditor must check for:

- missing synonyms;
- missing model names or method families;
- missing earlier foundational papers;
- missing recent variants;
- missing datasets/benchmarks;
- missing evaluation, critique, robustness, fairness, deployment, or failure-mode papers;
- suspicious dominance by one query, author group, venue, or year;
- papers found in reviews but not directly located.

Also use `survey_web_search_integrator` to check whether built-in web search reveals major terms or papers missing from the current candidate set.

Then generate `searches/query_plan_round2.csv` and `web/web_query_plan_round2.md`, and run another Paperclip + web-search round.

A third round is required if the round-2 new relevant-paper rate is high or if key concepts remain uncovered.

## Step 7: Synthesis before drafting

Create:

```text
extractions/taxonomy.md
extractions/comparative_table.csv
extractions/concept_matrix.csv
```

The taxonomy should identify conceptual groups, not merely paper titles. For each group, record representative papers and the technical distinction between groups.

## Step 8: English survey draft

Draft `drafts/survey_en.md` first, and explicitly use the `academic-writing` skill.

Requirements:

- Use citation IDs `[C001]`, `[C002]`, etc. in the unlinked draft.
- Include an Abstract, Introduction, Methods/Search Strategy, Taxonomy, Comparative Evidence, Main Findings, Limitations, Open Problems, Conclusion, and References.
- Explain cited papers technically. For each central technical paper, include contribution, method/architecture, data/task, novelty, and limitation.
- Do not cite a paper unless its evidence card supports the claim.
- Distinguish published papers, preprints, reviews, benchmarks, and opinion/framework papers.
- Avoid filler. Prefer dense technical synthesis.

## Step 9: Citation audit

Create `reports/claim_audit.md`.

For each citation-bearing paragraph, verify:

```text
claim_id,section,claim_summary,citations,evidence_card_ids,support_status,problem,fix
```

Support statuses:

- `supported`
- `overstated`
- `unsupported`
- `needs_more_evidence`
- `citation_mismatch`

Revise the English draft until no central claim is unsupported.

## Step 10: Japanese translation and polishing

Only after the English draft passes citation audit, translate it to `drafts/survey_ja.md`.

Rules:

- Preserve all citation IDs and reference list IDs exactly.
- Preserve section structure and tables.
- Translate prose into Japanese; keep precise technical terms in English when Japanese translation would be less standard.
- Do not add new claims during translation.
- If the English paragraph is weak, fix the English first and then translate.
- After translation, explicitly use the `academic-ja-polish` skill to revise the Japanese manuscript into formal, publication-appropriate academic Japanese.

## Step 11: Overview figure generation and audit

After the English manuscript is substantively complete, create an overview figure.

Use the `overview-figure` skill. First save the generation brief to `figures/overview_figure_prompt.md`, then save a distilled layout/content spec to `figures/overview_figure_spec.md`.

Requirements:

- The figure should be in English.
- The figure must be academically useful, not decorative.
- It should summarize the field structure or survey logic in a way that helps readers orient themselves.
- Suitable content includes taxonomy, timeline, methodological axes, data-task-architecture map, or a survey workflow.
- Do not simply convert each major manuscript section into one dense bullet box.
- Prefer a figure with one dominant organizing panel and smaller contextual/constraint panels.
- After the figure spec is explicit, use Codex `image_gen` first to create the overview-figure candidates.
- If `image_gen` succeeds, save the accepted image as `figures/overview_figure.<png|jpg|jpeg|webp>`, record `Rendering route: image_gen`, and do not run code-based figure creation.
- Use vector/slide construction or `scripts/render_overview_figure.py` only if `image_gen` is unavailable or cannot be invoked in the current environment, and record the fallback reason.
- Generate at least two candidate figures.
- Save the final choice and reasons for rejecting non-selected candidates to `reports/figure_selection.md`.

Then ask `survey_figure_auditor` to evaluate the figure. Save the audit as `reports/figure_audit.md`.

If the audit result is `revise`, improve the figure and audit again. If the result is `reject`, redesign the spec rather than merely tweaking colors.

After acceptance, insert the figure into `drafts/survey_en.md` and `drafts/survey_ja.md`, and make sure the main text explicitly mentions and explains the figure.

## Step 12: Finalization

After the figure is integrated, run:

```bash
python3 scripts/link_markdown_refs.py --run <RUN_DIR>
python3 scripts/render_tex_bib.py --run <RUN_DIR>
python3 scripts/compile_latex.py --run <RUN_DIR>
python3 scripts/validate_outputs.py --run <RUN_DIR>
```

If local LaTeX tools are available, `scripts/compile_latex.py` must build `tex/survey_en.pdf` and, when LuaLaTeX or upLaTeX+dvipdfmx is available, `tex/survey_ja.pdf`. The Japanese PDF must visibly render Japanese text; use explicit Japanese font embedding such as HaranoAji rather than treating a successful compiler exit as sufficient. If the tools are unavailable, report that PDF compilation was skipped rather than inventing PDFs.

The final answer should report:

- run directory;
- key output files;
- PDF files, or the reason PDF compilation was skipped;
- candidate count / evidence-card count / citation count;
- whether the figure was accepted;
- remaining coverage or validation risks.
