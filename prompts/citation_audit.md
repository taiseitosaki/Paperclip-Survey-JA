# Citation audit prompt

Audit the English draft against `evidence/evidence_cards.jsonl`.

For each citation-bearing paragraph, return a row with:

- claim_id
- section
- claim_summary
- citations
- evidence_card_ids
- support_status: supported | overstated | unsupported | needs_more_evidence | citation_mismatch
- problem
- fix

Check whether the cited evidence directly supports the exact surrounding claim. Do not merely check that the citation ID exists.

After the audit, revise the draft until no central claim is unsupported. If a claim is important but insufficiently supported, either add evidence by reading more papers or weaken the claim.
