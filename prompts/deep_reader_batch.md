# Deep reader batch prompt

For each assigned paper, create one evidence card JSON object following `templates/evidence_card.schema.json`.

Rules:

- Focus on the assigned paper itself, not papers it cites.
- Extract enough technical detail for a survey: method, architecture, data/corpus, task, objective, evaluation, novelty, limitation, and relationship to other papers.
- Do not reduce technical papers to one-sentence summaries.
- Mark evidence_scope as full-text, abstract-only, metadata-only, figure-derived, or mixed.
- Preprint status is not an exclusion reason. Record publication_status.
- Return valid JSONL: exactly one JSON object per line.
