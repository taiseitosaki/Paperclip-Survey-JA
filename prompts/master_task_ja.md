[$survey-paperclip](.agents/skills/survey-paperclip/SKILL.md) <ここに調査テーマを入力> に関する一般的で質の高いサーベイを作成してください。

重要条件:

1. 最初に `python3 scripts/init_run.py --topic "<ここに調査テーマを入力>"` を実行し、作成された `outputs/runs/<run-id>/` だけに出力してください。
2. 作業・文献探索・evidence extraction・英語ドラフトは英語で進めてください。
3. 英語版 `drafts/survey_en.md` の執筆には、必ず `[$academic-writing](.agents/skills/academic-writing/SKILL.md)` を活用してください。
4. Paperclip 検索に加えて、Codex built-in web search も必ず実施し、検索語拡張・候補統合・出版状況確認に使ってください。
5. 日本語版 `drafts/survey_ja.md` は英語版完成後に翻訳し、その後 `[$academic-ja-polish](.agents/skills/academic-ja-polish/SKILL.md)` を用いて academic な日本語文体へ洗練させてください。
6. `drafts/survey_en.linked.md` と `drafts/survey_ja.linked.md` では、`[C001]` をクリックしたら Reference list の該当箇所に飛べるようにしてください。
7. 英語版・日本語版ともに、Overleaf でコンパイル可能な `tex/survey_en.tex`, `tex/survey_ja.tex`, `tex/references.bib` を作成してください。ローカル LaTeX 環境が利用可能な場合は PDF までコンパイルし、`tex/survey_en.pdf` と `tex/survey_ja.pdf` も提供してください。
8. 関連論文を安易に削ぎ落とさないでください。preprint は除外理由にせず、出版・採択状況を確認できる場合は記録してください。
9. 検索クエリは入力語だけに依存せず、広義語、同義語、歴史的前身、モデル名、データセット名、ベンチマーク名、評価・批判・限界関連語を含めてください。
10. 初回検索後、見つかった論文のタイトル・abstract・review内の重要概念から query expansion を行い、少なくとも第2ラウンドの Paperclip + web search を実行してください。
11. 必要に応じて subagents を起動してください。特に query strategist, web search integrator, coverage auditor, paper reader, citation auditor, figure auditor の役割を使ってください。
12. 原稿完成後、`[$overview-figure](.agents/skills/overview-figure/SKILL.md)` を使って overview figure を作成してください。まず `figures/overview_figure_spec.md` に情報設計を落とし込み、その後 Codex `image_gen` を優先して少なくとも 2 つの figure candidate を作ってください。図内の言語は英語で構いません。
13. text-heavy な survey 図でも、spec と layout constraints を明示したうえでまず `image_gen` を呼んでください。`image_gen` が成功した場合は、選んだ画像を `figures/overview_figure.<png|jpg|jpeg|webp>` として保存し、`Rendering route: image_gen` を記録し、コードベースの deterministic renderer は実行しないでください。`image_gen` が現在の環境で呼べない場合に限り、vector / slide / deterministic renderer ベースの作図へフォールバックし、その理由を `logs/codex_worklog.md` または `reports/figure_selection.md` に残してください。単なる「節見出しを箱に詰めた box farm」型の図は避けてください。
14. figure auditor の採否を経て、採用された overview figure を本文の適切な位置に挿入し、本文中でも Figure 1 / 図1 として参照・説明してください。image_gen で作成された図がある場合は、その画像を Markdown に組み込み、linked Markdown と TeX を再生成してください。`reports/figure_selection.md` に採用理由も残してください。
15. 最終的に `python3 scripts/link_markdown_refs.py --run <RUN_DIR>`, `python3 scripts/render_tex_bib.py --run <RUN_DIR>`, `python3 scripts/compile_latex.py --run <RUN_DIR>`, `python3 scripts/validate_outputs.py --run <RUN_DIR>` を実行してください。

最終回答では、run directory と主要ファイル、PDF の有無またはコンパイルをスキップした理由を示し、coverage・citation・web integration・figure audit・validation 上の残存リスクを簡潔に報告してください。
