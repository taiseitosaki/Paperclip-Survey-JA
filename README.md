# Paperclip + Codex Survey

Mac の Codex app で Paperclip (https://paperclip.gxl.ai/) と Codex 内蔵 web search を併用し、入力テーマから監査可能で中身の濃いサーベイ論文を作るためのプロジェクト雛形です。


## 推奨実行方法

Codex app でこのフォルダを開き、次のように依頼してください。

```text
[$survey-paperclip](.agents/skills/survey-paperclip/SKILL.md) <ここに調査テーマを入力> に関する一般的で質の高いサーベイを作成してください。
作業は英語で進め、英語版サーベイを academic-writing skill を使って完成させた後、日本語版を翻訳し、academic-ja-polish skill で学術日本語へ洗練させてください。
Paperclip 検索に加えて Codex built-in web search も行い、検索語拡張・候補統合・出版状況確認に使ってください。
最後に overview figure を作成し、figure auditor の採否を経て本文に組み込んでください。
```

Codex が最初に実行すべきコマンドは以下です。

```bash
python3 scripts/init_run.py --topic "<your topic>"
```

このコマンドは、例えば次のようなディレクトリを作ります。

```text
outputs/runs/<timestamp>-<topic>-1a2b3c/
```

以後の全出力はこの run directory に保存してください。

## Run directory structure

```text
outputs/runs/<timestamp>-<topic-slug>/
  run_manifest.json
  prompt.txt
  searches/
    query_plan_round1.csv
    query_plan_round2.csv
    raw_results/
    deduped_candidates.csv
    screening_decisions.csv
    coverage_audit.md
  web/
    web_query_plan_round1.md
    web_query_plan_round2.md
    web_search_log.md
    triangulated_candidates.csv
    integrated_search_summary.md
  evidence/
    evidence_cards.jsonl
    evidence_cards.schema.json
    paper_reading_status.csv
  extractions/
    comparative_table.csv
    taxonomy.md
    concept_matrix.csv
  drafts/
    survey_en.md
    survey_en.linked.md
    survey_ja.md
    survey_ja.linked.md
  figures/
    overview_figure_prompt.md
    overview_figure.png  # or jpg/webp
  tex/
    survey_en.tex
    survey_ja.tex
    references.bib
    figures/
      overview_figure.png  # copied automatically if present
  refs/
    references.md
    references.jsonl
  reports/
    protocol.md
    methods.md
    claim_audit.md
    figure_audit.md
    limitations.md
    validation_report.md
  logs/
    paperclip_commands.md
    codex_worklog.md
```

## 補助コマンド

```bash
# 最新runを確認
ls -la outputs/runs
readlink outputs/latest

# Markdown引用リンクを作成
python3 scripts/link_markdown_refs.py --run outputs/runs/<run-id>

# overview figure を Markdown に挿入する補助（任意）
python3 scripts/insert_overview_figure.py --run outputs/runs/<run-id> --image /path/to/figure.png --caption "Figure 1. Overview of ..."

# TeX/BibTeXを生成
python3 scripts/render_tex_bib.py --run outputs/runs/<run-id>

# 品質検査
python3 scripts/validate_outputs.py --run outputs/runs/<run-id>
```

## 出力物

最低限、次を作成してください。

```text
outputs/runs/<run-id>/drafts/survey_en.md
outputs/runs/<run-id>/drafts/survey_ja.md
outputs/runs/<run-id>/drafts/survey_en.linked.md
outputs/runs/<run-id>/drafts/survey_ja.linked.md
outputs/runs/<run-id>/figures/overview_figure_prompt.md
outputs/runs/<run-id>/figures/overview_figure.<png|jpg|webp>
outputs/runs/<run-id>/tex/survey_en.tex
outputs/runs/<run-id>/tex/survey_ja.tex
outputs/runs/<run-id>/tex/references.bib
outputs/runs/<run-id>/reports/figure_audit.md
outputs/runs/<run-id>/reports/claim_audit.md
outputs/runs/<run-id>/reports/validation_report.md
outputs/runs/<run-id>/evidence/evidence_cards.jsonl
outputs/runs/<run-id>/web/integrated_search_summary.md
```

## 位置づけ

このスターターは「綺麗な見かけの文書」を作るためのものではなく、検索・網羅性・読み込み・引用根拠・図の妥当性まで含めて、AI agent による survey workflow を監査可能にするためのものです。Paperclip の coverage が強い分野ではそれを主軸に使い、そうでない分野では Codex built-in web search を補助ではなく重要な回収経路として使ってください。
