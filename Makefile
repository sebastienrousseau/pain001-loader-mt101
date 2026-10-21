# SPDX-License-Identifier: Apache-2.0 OR MIT
# Convenience targets for pain001-loader-mt101.
#
# Every target runs what CI runs, from the same hash-pinned requirements.
# `make install` builds that environment in .venv.

PY ?= .venv/bin/python
BIN := $(dir $(PY))
PKG := pain001_loader_mt101

.PHONY: help install test cov lint format typecheck docstrings examples complexity audit verify-versions pip-compile fuzz demo check clean docs mutate

help: ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Create/refresh .venv from the hash-pinned test and lint trees.
	python3 -m venv .venv
	$(PY) -m pip install --require-hashes -r requirements/test.txt
	$(PY) -m pip install --require-hashes -r requirements/lint.txt
	$(PY) -m pip install --no-deps -e .

test: ## Run the test suite with the 100% coverage gate.
	$(PY) -m pytest

cov: test ## Alias for the coverage-gated test run.

# Same paths CI lints, so a green `make lint` means a green lint job.
LINT_PATHS := $(PKG) tests examples benches scripts fuzz

lint: ## Ruff lint and format check (what CI runs).
	$(PY) -m ruff check $(LINT_PATHS)
	$(PY) -m ruff format --check $(LINT_PATHS)

format: ## Format with ruff (the formatter CI enforces) and fix imports.
	$(PY) -m ruff format $(LINT_PATHS)
	$(PY) -m ruff check --fix $(LINT_PATHS)

typecheck: ## Strict mypy over the package and scripts.
	$(PY) -m mypy $(PKG) scripts

docstrings: ## 100% docstring coverage gate.
	$(PY) -m interrogate -c pyproject.toml $(PKG)

examples: ## Run every example end-to-end.
	@for e in examples/*.py; do echo "--- $$e ---"; $(PY) "$$e" || exit 1; done

complexity: ## Complexity ceilings against complexity-baseline.json.
	$(PY) scripts/check_complexity.py
	$(BIN)complexipy $(PKG) scripts benches examples fuzz --max-complexity-allowed 15 --quiet

audit: ## pip-audit every hash-pinned requirements file (needs requirements/audit.txt).
	@for f in requirements/*.txt; do \
		echo "--- $$f"; \
		pip-audit --progress-spinner off --require-hashes --disable-pip -r "$$f" || exit 1; \
	done

verify-versions: ## Every restatement of the version agrees with pyproject.toml.
	$(PY) scripts/verify_versions.py

pip-compile: ## Regenerate hash-pinned requirements/*.txt from requirements/*.in (needs uv).
	@command -v uv >/dev/null || { echo "uv is required: https://docs.astral.sh/uv/"; exit 1; }
	@for f in requirements/*.in; do \
		[ "$$f" = requirements/fuzz.in ] && continue; \
		echo "compiling $$f"; \
		uv pip compile --quiet --generate-hashes --universal \
			--python-version 3.10 "$$f" -o "$${f%.in}.txt"; \
	done
	@echo "compiling requirements/fuzz.in (Linux x86_64, Atheris wheels only)"
	@uv pip compile --quiet --generate-hashes --python-platform x86_64-manylinux_2_17 \
		--python-version 3.12 requirements/fuzz.in -o requirements/fuzz.txt

fuzz: ## Atheris for FUZZ_SECONDS (default 60); Linux x86_64, needs requirements/fuzz.txt.
	$(PY) fuzz/fuzz_parse_mt101.py fuzz/corpus -max_total_time=$(or $(FUZZ_SECONDS),60)

demo: ## Re-render .github/demo.gif from .github/demo.tape (needs vhs).
	vhs .github/demo.tape

check: lint typecheck complexity verify-versions test docstrings examples ## Run every gate CI runs on a pull request.

clean: ## Remove caches and build artefacts.
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

# Mutation score floor for the parser: 90.4% (312 of 345) on 2026-09-18.
# The floor sits under it so one flaky mutant cannot block a release.
# Raise it when the score rises; never lower it to make a red run green.
MUTATION_FLOOR ?= 88

docs: ## Build the Sphinx documentation (warnings are errors; needs requirements/docs.txt)
	$(PY) -m sphinx -W --keep-going -b html docs docs/_build/html

mutate: ## Mutation testing (mutmut 3, config in pyproject; needs requirements/mutation.txt)
	rm -rf mutants
	$(PY) -m mutmut run
	$(PY) -m mutmut export-cicd-stats
	$(PY) scripts/mutation_gate.py --floor $(MUTATION_FLOOR)
