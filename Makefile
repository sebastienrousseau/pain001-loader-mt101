# SPDX-License-Identifier: Apache-2.0 OR MIT
# Convenience targets for pain001-loader-mt101.

PY ?= .venv/bin/python
PKG := pain001_loader_mt101

.PHONY: help install test cov lint format typecheck docstrings examples check clean docs mutate

help: ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Create/refresh the dev environment.
	python -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"

test: ## Run the test suite with the 100% coverage gate.
	$(PY) -m pytest

cov: test ## Alias for the coverage-gated test run.

# Same paths CI lints, so a green `make lint` means a green lint job.
LINT_PATHS := $(PKG) tests examples benches scripts

lint: ## Ruff lint and format check (what CI runs).
	$(PY) -m ruff check $(LINT_PATHS)
	$(PY) -m ruff format --check $(LINT_PATHS)

format: ## Format with ruff (the formatter CI enforces) and fix imports.
	$(PY) -m ruff format $(LINT_PATHS)
	$(PY) -m ruff check --fix $(LINT_PATHS)

typecheck: ## Strict mypy.
	$(PY) -m mypy $(PKG)

docstrings: ## 100% docstring coverage gate.
	$(PY) -m interrogate -c pyproject.toml $(PKG)

examples: ## Run every example end-to-end.
	@for e in examples/*.py; do echo "--- $$e ---"; $(PY) "$$e"; done

check: test lint typecheck docstrings examples ## Run every gate.

clean: ## Remove caches and build artefacts.
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

# Mutation score floor for the parser: 90.4% (312 of 345) on 2026-09-18.
# The floor sits under it so one flaky mutant cannot block a release.
# Raise it when the score rises; never lower it to make a red run green.
MUTATION_FLOOR ?= 88

docs: ## Build the Sphinx documentation (warnings are errors)
	$(PY) -m sphinx -W --keep-going -b html docs docs/_build/html

mutate: ## Mutation testing (mutmut 3, config in pyproject)
	rm -rf mutants
	$(PY) -m mutmut run
	$(PY) -m mutmut export-cicd-stats
	$(PY) scripts/mutation_gate.py --floor $(MUTATION_FLOOR)

