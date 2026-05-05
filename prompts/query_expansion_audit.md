# Query expansion audit prompt

Given the current topic, query plans, candidate list, evidence cards, and draft, audit the search strategy.

Return structured output with:

1. Missing umbrella terms.
2. Missing synonyms or alternate spellings.
3. Missing predecessor concepts or historical terminology.
4. Missing named methods, models, datasets, benchmarks, venues, or author clusters.
5. Missing evaluation/failure-mode/deployment terms.
6. Papers mentioned in reviews or abstracts that should be directly looked up.
7. 10-25 new search queries, each with rationale and expected contribution.
8. A judgment: continue searching or stop, with reason.

Do not optimize for fewer papers. Optimize for not missing important papers.
