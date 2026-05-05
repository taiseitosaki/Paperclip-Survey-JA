# Japanese translation prompt

Translate `drafts/survey_en.md` to `drafts/survey_ja.md` only after the English draft passes citation audit.

Rules:

- Preserve citation IDs exactly: `[C001]` remains `[C001]`.
- Preserve headings, tables, figure references, and reference IDs.
- Translate prose into precise Japanese.
- Keep model names, dataset names, mathematical terms, and standard technical vocabulary in English when appropriate.
- Do not add new claims during translation.
- Do not omit caveats about preprints, weak evidence, or corpus limitations.
- After translation, run a second-pass academic Japanese polishing step.
