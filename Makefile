.PHONY: init link tex validate latest tree figure

TOPIC ?= Example survey topic
RUN ?= $(shell readlink outputs/latest 2>/dev/null || cat outputs/LATEST_RUN.txt 2>/dev/null)
IMAGE ?=
CAPTION ?= Figure 1. Overview of the surveyed field.

init:
	python3 scripts/init_run.py --topic "$(TOPIC)"

link:
	python3 scripts/link_markdown_refs.py --run "$(RUN)"

figure:
	python3 scripts/insert_overview_figure.py --run "$(RUN)" --image "$(IMAGE)" --caption "$(CAPTION)"

tex:
	python3 scripts/render_tex_bib.py --run "$(RUN)"

validate:
	python3 scripts/validate_outputs.py --run "$(RUN)"

latest:
	@echo "$(RUN)"

tree:
	find "$(RUN)" -maxdepth 3 -type f | sort
