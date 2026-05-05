# Web-search integration prompt

Use Codex built-in web search to complement Paperclip.

Required outputs:

- `web/web_query_plan_round1.md` or `web/web_query_plan_round2.md`
- `web/web_search_log.md`
- `web/triangulated_candidates.csv`
- `web/integrated_search_summary.md`

Goals:

- discover broader terminology and adjacent keywords;
- identify missing landmark papers or review articles;
- confirm publication status and venue information;
- locate peer-reviewed versions of preprints;
- find candidate papers outside current Paperclip recall.
