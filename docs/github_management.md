# GitHub management notes

Track the workflow definition, not generated survey artifacts.

## Files that should normally be tracked

- `AGENTS.md`
- `.agents/skills/**`
- `.codex/agents/**`
- `prompts/**`
- `scripts/**`
- `templates/**`
- `README.md`
- `Makefile`
- `requirements.txt`

## Files that should normally not be tracked

- `outputs/**` run directories
- generated Markdown / TeX / BibTeX survey outputs
- generated survey PDFs
- generated overview figures and figure candidates
- local zip packages
- local patch/diff files
- LaTeX build artifacts

The repository `.gitignore` ignores the entire `outputs/` tree, including `outputs/.gitkeep`, so generated run directories do not appear as untracked files.

## If generated outputs were already committed

Run this once after applying the updated `.gitignore`:

```bash
git rm -r --cached outputs || true
git add .gitignore
git commit -m "Ignore generated survey outputs"
```

If zip or patch files were already committed unintentionally:

```bash
git rm --cached '*.zip' '*.patch' '*.diff' || true
git commit -m "Stop tracking local packaged artifacts"
```

## Applying a patch release

From the repository root:

```bash
git apply paperclip_survey_ja_v4_figure_quality.patch
git status
git add .
git commit -m "Improve overview figure workflow and ignore generated artifacts"
```

## Release packaging

Use GitHub Releases or external storage for packaged zip artifacts. Do not commit generated zip archives into the main branch unless there is a specific release-management reason.
