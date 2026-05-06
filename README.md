# Paperclip + Codex Survey

Mac の Codex app で Paperclip (https://paperclip.gxl.ai/) と Codex 内蔵 web search を併用し、入力テーマから監査可能で中身の濃いサーベイ論文を作るためのプロジェクト雛形です。

## 推奨実行方法

Codex app でこのフォルダを開き、次のように依頼してください。

```text
[$survey-paperclip](.agents/skills/survey-paperclip/SKILL.md) <ここに調査テーマを入力> に関する一般的で質の高いサーベイを作成してください。
作業は英語で進め、英語版サーベイを academic-writing skill を使って完成させた後、日本語版を翻訳し、academic-ja-polish skill で学術日本語へ洗練させてください。
Paperclip 検索に加えて Codex built-in web search も行い、検索語拡張・候補統合・出版状況確認に使ってください。
最後に overview figure を作成してください。ただし、まず figure spec を作り、Codex image_gen を優先して少なくとも2候補を作成し、image_gen が呼べない場合のみ deterministic renderer にフォールバックしてください。figure auditor の採否と figure selection を経て本文に組み込んでください。
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
    overview_figure_spec.md
    overview_figure_spec.json  # fallback deterministic-renderer input
    overview_figure_candidate_a.png
    overview_figure_candidate_b.png
    overview_figure.png  # accepted final, or jpg/webp
  tex/
    survey_en.tex
    survey_ja.tex
    references.bib
    survey_en.pdf  # LaTeX環境がある場合
    survey_ja.pdf  # LuaLaTeXまたはupLaTeX+dvipdfmx環境がある場合
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
    figure_selection.md
    limitations.md
    validation_report.md
  logs/
    paperclip_commands.md
    codex_worklog.md
```

## 初期セットアップ

```bash
pip install -r requirements.txt
```

Overview figure は Codex `image_gen` を優先して作成します。`image_gen` が成功した場合は、選んだ画像を `figures/overview_figure.<png|jpg|jpeg|webp>` として保存し、`scripts/insert_overview_figure.py` で Markdown に組み込みます。この場合、コードベースの deterministic renderer は実行しません。`render_overview_figure.py` は、`image_gen` が呼べない場合の fallback として deterministic な PNG/SVG 生成のため Pillow を使います。

## 補助コマンド

```bash
# 最新runを確認
ls -la outputs/runs
readlink outputs/latest

# Markdown引用リンクを作成
python3 scripts/link_markdown_refs.py --run outputs/runs/<run-id>

# image_gen で選んだ overview figure を Markdown に挿入
python3 scripts/insert_overview_figure.py --run outputs/runs/<run-id> --image /path/to/figure.png --caption "Figure 1. Overview of ..."

# fallback: image_gen が呼べない場合のみ、JSON spec から deterministic な overview figure 候補を生成
python3 scripts/render_overview_figure.py --run outputs/runs/<run-id> --spec outputs/runs/<run-id>/figures/overview_figure_spec.json --output overview_figure_candidate_a --fallback-reason "image_gen could not be invoked in this environment"

# TeX/BibTeXを生成
python3 scripts/render_tex_bib.py --run outputs/runs/<run-id>

# LaTeX環境がある場合にPDFまでコンパイル
python3 scripts/compile_latex.py --run outputs/runs/<run-id>

# 日本語PDFはHaranoAji系フォントを明示して生成します。
# コンパイル成功だけでなく、日本語本文が実際に表示されることを確認してください。

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
outputs/runs/<run-id>/figures/overview_figure_spec.md
outputs/runs/<run-id>/figures/overview_figure_candidate_a.<png|jpg|webp|svg>
outputs/runs/<run-id>/figures/overview_figure_candidate_b.<png|jpg|webp|svg>
outputs/runs/<run-id>/figures/overview_figure.<png|jpg|webp>
outputs/runs/<run-id>/tex/survey_en.tex
outputs/runs/<run-id>/tex/survey_ja.tex
outputs/runs/<run-id>/tex/references.bib
outputs/runs/<run-id>/tex/survey_en.pdf  # LaTeX環境がある場合
outputs/runs/<run-id>/tex/survey_ja.pdf  # LuaLaTeXまたはupLaTeX+dvipdfmx環境がある場合
outputs/runs/<run-id>/reports/figure_audit.md
outputs/runs/<run-id>/reports/figure_selection.md
outputs/runs/<run-id>/reports/claim_audit.md
outputs/runs/<run-id>/reports/validation_report.md
outputs/runs/<run-id>/evidence/evidence_cards.jsonl
outputs/runs/<run-id>/web/integrated_search_summary.md
```

## 位置づけ

このスターターは「綺麗な見かけの文書」を作るためのものではなく、検索・網羅性・読み込み・引用根拠・図の妥当性まで含めて、AI agent による survey workflow を監査可能にするためのものです。Paperclip の coverage が強い分野ではそれを主軸に使い、そうでない分野では Codex built-in web search を補助ではなく重要な回収経路として使ってください。


## Git 管理方針

`outputs/` 配下の run output、ローカルで作成した zip / patch / diff、LaTeX build artifacts は `.gitignore` で除外します。テンプレート、スクリプト、skills、prompts だけを track。
