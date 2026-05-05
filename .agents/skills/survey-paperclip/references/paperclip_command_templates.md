# Paperclip command templates for survey workflows

Record every command and result handle in `logs/paperclip_commands.md`.

## Broad search

```bash
paperclip searches \
  "<umbrella concept> <domain>" \
  "<exact user phrase>" \
  "<synonym phrase>" \
  "<historical predecessor terms>" \
  "<benchmark evaluation critique terms>"
```

## Lookup named landmark papers

```bash
paperclip lookup "<paper title or DOI or PMID or arXiv ID>"
```

## Refine within a result set without destroying it

```bash
paperclip grep -i "<important term>|<synonym>|<model name>" --from <search_handle>
paperclip scan --from <search_handle> "<term1>" "<term2>" "<term3>"
```

## Filter, but do not over-filter

```bash
paperclip filter --from <search_handle> "Keep core, adjacent, and context papers for a survey of <topic>. Exclude only clearly out-of-scope papers. Do not exclude preprints solely because they are preprints."
```

## Evidence extraction

```bash
paperclip map --from <filtered_handle> "For each paper, return one JSON evidence card. Focus on the mapped paper itself. Include contribution, technical details, data/task, objective, evaluation, novelty, limitations, publication_status, supported_claims, and evidence_scope."
```

## Synthesis

```bash
paperclip reduce --from <map_handle> --strategy summarize "Synthesize taxonomy, historical development, consensus findings, disagreements, gaps, and papers needing deeper reading."
```

## Manual recovery for failed maps

```bash
paperclip cat /papers/<id>/meta.json
paperclip ls /papers/<id>/sections/
paperclip head -120 /papers/<id>/content.lines
paperclip grep -i "method|model|dataset|objective|result|limitation|evaluation" /papers/<id>/content.lines
```
