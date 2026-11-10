<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Development

The single entry point for working on `pain001-loader-mt101`: toolchain,
how to reproduce every CI gate locally, where tests live, and how a
release happens. [CONTRIBUTING.md](CONTRIBUTING.md) covers the etiquette
(DCO, commit format, review); this file covers the mechanics.

## Toolchain

| Tool | Version | Where it is pinned |
| :--- | :--- | :--- |
| Python | 3.11 is the floor; CI tests 3.11 to 3.14 | `pyproject.toml` `requires-python`, the `ci.yml` matrix, [toolchain policy](docs/POLICIES.md) |
| Python packages | exact, with hashes | `requirements/*.txt`, compiled from `requirements/*.in` with `make pip-compile` (needs `uv`) |
| Node | any current LTS | only for `markdownlint-cli2` in `make docs-lint` and the docs-lint job |
| vhs | any | only for `make demo` |

```bash
git clone https://github.com/sebastienrousseau/pain001-loader-mt101
cd pain001-loader-mt101
make install          # .venv from requirements/test.txt and lint.txt
make check            # every gate a pull request runs, see below
pre-commit install    # optional: ruff, codespell, markdownlint on commit
```

`make install` installs the test and lint trees. The other gates need
their own hash-pinned file installed into `.venv` first, for example
`.venv/bin/python -m pip install --require-hashes -r requirements/docs.txt`.
Install them one file at a time: the files pin different versions of
some shared packages and conflict when installed together.

The [devcontainer](.devcontainer/devcontainer.json) runs
`make install && make check` when it is created, in a Codespace or a VS
Code container.

## Reproducing every CI gate

| Gate | Local command | CI workflow |
| :--- | :--- | :--- |
| Ruff lint and format | `make lint` | `ci.yml` (Lint & Type Check) |
| mypy `--strict` over the package and scripts | `make typecheck` | `ci.yml` (Lint & Type Check) |
| Complexity: cyclomatic 10, cognitive 15, Halstead 30, 60 lines per function, 500 per file, against `complexity-baseline.json` | `make complexity` | `ci.yml` (Complexity) |
| Version agreement across every restatement | `make verify-versions` | `versions.yml` |
| Tests, 100% line and branch coverage of the package and `scripts/` | `make test` | `ci.yml` (Test, Python 3.11 to 3.14) |
| 100% docstring coverage | `make docstrings` | `ci.yml` |
| Examples run end to end | `make examples` (also `tests/test_examples.py`) | `ci.yml` |
| Benchmark still runs | `.venv/bin/python benches/bench_parse_mt101.py --quick` | `ci.yml` |
| Dependency advisories over every `requirements/*.txt` | `make audit` (needs `requirements/audit.txt`) | `ci.yml` (Dependency audit) |
| Spelling and Markdown style | `make docs-lint` (needs `requirements/docs-lint.txt` and Node) | `docs-lint.yml` |
| Sphinx manual, warnings are errors | `make docs` (needs `requirements/docs.txt`) | `docs.yml` |
| Atheris fuzzing of `parse_mt101` | `make fuzz` (Linux x86_64, needs `requirements/fuzz.txt`) | `fuzz.yml` |
| Mutation score of the parser, floor 88% | `make mutate` (needs `requirements/mutation.txt`) | `mutation.yml` |
| DCO sign-off on every commit | `git log --format=%B` shows `Signed-off-by:` | `dco.yml` |
| CodeQL, OpenSSF Scorecard | none locally | `codeql.yml`, `scorecard.yml` |
| Nine-member suite publications agree | none locally; the core's `make ecosystem-check` | `suite-consistency.yml` (daily and after a release) |

`make check` runs lint, typecheck, complexity, verify-versions, test,
docstrings and examples, in that order, and is what a pull request must
pass before review.

### Why the coverage floor is 100%

The package is one parser of a few hundred lines, and the branches a
test suite tends to miss are the malformed-input ones, which is exactly
where a parser that feeds payment files has to be right. `scripts/` is
held to the same floor because those scripts decide whether a release
goes out. Coverage is measured with branches (`--cov-branch`); the scope
and the floor live in `pyproject.toml`'s pytest `addopts`, so `make test`
and CI cannot measure different things. The one `# pragma: no cover` is
the command-line guard of `scripts/release_notes.py`, which is vendored
byte-identical from the core; the other scripts' entry points are run by
their tests.

## Test layout

```text
tests/
  test_loader.py              the parser: grammar, field mapping, strictness
  test_fuzz.py                Hypothesis properties, and a replay of fuzz/corpus/
  test_benchmarks.py          pytest-benchmark timings and the scaling guard
  test_examples.py            every script in examples/ runs and prints its result
  test_readme_template.py     README heading order, badges, demo, no {{...}} left,
                              the Quick Start executed
  test_verify_versions.py     scripts/verify_versions.py, one drift at a time
  test_check_complexity.py    scripts/check_complexity.py and its baseline ratchet
  test_mutation_gate.py       scripts/mutation_gate.py
  test_release_notes.py       scripts/release_notes.py (vendored from pain001)
  test_suite_conformance.py   the family-wide rules; vendored byte-identical, do not edit
examples/                     numbered, runnable scripts
benches/                      throughput as a message grows
fuzz/                         the Atheris harness and its corpus; fixed-bug inputs
                              are named regression-*.mt101
```

A fixed bug gets a regression test in `tests/test_loader.py` and, when
the input came from fuzzing, a `regression-*.mt101` file in
`fuzz/corpus/`, which `tests/test_fuzz.py` replays on every run.

## Documentation

Sphinx with MyST under `docs/`, the only documentation root. `make docs`
builds `docs/_build/html` with warnings as errors; `docs.yml` deploys it
to GitHub Pages from `main`. Root Markdown files (`README.md`,
`ARCHITECTURE.md`, this file, `CHANGELOG.md`) are included into the
manual by thin chapter files under `docs/`, so each is edited in one
place. The API reference (`docs/api.md`) is generated from docstrings,
which `make docstrings` holds at 100%. Decisions that will be questioned
later get an ADR in [`docs/adr/`](docs/adr/index.md).

## Versioning and release

- The version is `0.0.x`, moves by `0.0.1`, and every member of the
  pain001 suite ships the same number. The maintainer decides when a
  release opens; a change never bumps it on the side.
- It is restated in `pyproject.toml`, `pain001_loader_mt101/__init__.py`,
  `CITATION.cff`, the `SECURITY.md` and `SUPPORT.md` support tables, the
  README's latest-release callout, `releases/v0.0.N.md` and a
  `## [0.0.N]` heading in `CHANGELOG.md`; `make verify-versions` checks
  the ones it can.
- Work for the next version happens on `feat/v<next-version>`, the only
  pull request into `main`.
- Releases are cut from a signed tag; `release.yml` builds, attests,
  signs and publishes to PyPI with trusted publishing.
  [RELEASING.md](RELEASING.md) is the checklist.
