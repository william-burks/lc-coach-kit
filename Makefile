# LC Coach Kit — convenience targets.
# `make install` once, then `make setup` / `make status` / `make review` etc.
# Targets use the venv python if present, else system python3 — no manual activation.

PY := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)
OPEN := $(shell command -v open >/dev/null 2>&1 && echo open || (command -v xdg-open >/dev/null 2>&1 && echo xdg-open || echo start))

.PHONY: help install setup status gap review log arm docs clean

help:
	@echo "LC Coach Kit"
	@echo "  make install                          create venv + install deps"
	@echo "  make setup                            configure name + language(s)"
	@echo "  make status                           what's due + flagged weak areas"
	@echo "  make review  [P=\"11 Container\"]        habit-aware code review (paste code)"
	@echo "  make log                              log a session report (paste report)"
	@echo "  make arm     P=\"11 Container\" [M=INTERVIEW]   build a session pack"
	@echo "  make gap                              aggregate trend analysis"
	@echo "  make docs                             open the full system manual (MANUAL.html)"
	@echo "  make clean                            remove venv + runtime files"
	@echo ""
	@echo "First: set ANTHROPIC_API_KEY in your environment (review/log/gap need it)."

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	@echo "Done. Now: export ANTHROPIC_API_KEY=... && make setup"

setup:
	@$(PY) lc.py setup

status:
	@$(PY) lc.py status

gap:
	@$(PY) lc.py gap

review:
	@$(PY) lc.py review $(if $(P),--problem "$(P)")

log:
	@$(PY) lc.py log

arm:
	@test -n "$(P)" || (echo 'usage: make arm P="11 Container" [M=INTERVIEW]'; exit 1)
	@$(PY) lc.py arm "$(P)" $(if $(M),--mode $(M))

docs:
	@$(OPEN) MANUAL.html

clean:
	rm -rf .venv __pycache__ .session session-pack.md
	@echo "Removed venv + runtime files (kept your config.md and logs/)."
