# SPDX-License-Identifier: Apache-2.0
# Convenience targets for pain001-loader-mt101.

PY ?= .venv/bin/python
PKG := pain001_loader_mt101

.PHONY: help install test cov lint format typecheck docstrings examples check clean

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

lint: ## Ruff lint.
	$(PY) -m ruff check $(PKG) tests examples

format: ## Format with black + ruff import sort.
	black $(PKG) tests examples
	$(PY) -m ruff check --fix $(PKG) tests examples

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
