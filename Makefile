.PHONY: init link tex pdf validate finalize latest tree figure fallback-render-figure render-figure

TOPIC ?= Example survey topic
RUN ?= $(shell readlink outputs/latest 2>/dev/null || cat outputs/LATEST_RUN.txt 2>/dev/null)
IMAGE ?=
CAPTION ?= Figure 1. Overview of the surveyed field.
SPEC ?= $(RUN)/figures/overview_figure_spec.json
FIGURE_OUTPUT ?= overview_figure_candidate_a
FALLBACK_REASON ?= image_gen could not be invoked in the current Codex environment

init:
	python3 scripts/init_run.py --topic "$(TOPIC)"

link:
	python3 scripts/link_markdown_refs.py --run "$(RUN)"

figure:
	python3 scripts/insert_overview_figure.py --run "$(RUN)" --image "$(IMAGE)" --caption "$(CAPTION)"

fallback-render-figure:
	python3 scripts/render_overview_figure.py --run "$(RUN)" --spec "$(SPEC)" --output "$(FIGURE_OUTPUT)" --fallback-reason "$(FALLBACK_REASON)"

render-figure: fallback-render-figure

tex:
	python3 scripts/render_tex_bib.py --run "$(RUN)"

pdf: tex
	python3 scripts/compile_latex.py --run "$(RUN)"

validate:
	python3 scripts/validate_outputs.py --run "$(RUN)"

finalize: link tex pdf validate

latest:
	@echo "$(RUN)"

tree:
	find "$(RUN)" -maxdepth 3 -type f | sort
