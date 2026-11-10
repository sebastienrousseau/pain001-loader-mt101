<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# AGENTS.md

`pain001-loader-mt101` turns legacy SWIFT MT101 Request for Transfer
messages into the flat records the `pain001` suite validates and turns
into ISO 20022 pain.001, one record per transaction, and nothing else.
These are the rules an automated change is most likely to break; humans
follow them too. Read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## Versioning

- The version is `0.0.x`, moves by `0.0.1`, and ships in lockstep with
  the other eight `pain001` suite repositories. Never bump it as a side
  effect of a change.
- It is restated in `pyproject.toml`, `pain001_loader_mt101/__init__.py`,
  `CITATION.cff` and the README's latest-release callout, with a
  `## [0.0.N]` heading in `CHANGELOG.md`. `scripts/verify_versions.py`
  and `tests/test_suite_conformance.py` check that they agree.
- Work for the next version happens on `feat/v<next-version>`, the only
  pull request into `main`.

## Commits

- Conventional commits with a body that says why.
- Every commit is signed off (`git commit -s`, see [DCO.txt](DCO.txt))
  and SSH-signed. Never rewrite pushed history.

## The gate

- `make check` runs every gate CI runs on a pull request: lint, strict
  mypy, complexity, version agreement, tests with **100% branch
  coverage**, docstring coverage and the examples. "It compiles" is not
  done.
- Complexity ceilings are held against `complexity-baseline.json`, which
  may only shrink.
- `requirements/*.txt` are hash-pinned; regenerate them with
  `make pip-compile`, never by hand.

## Data

- No real account numbers, personal data or bank-restricted material in
  the repository. Test inputs are synthetic; sample IBANs pass mod-97
  and BICs are structurally valid.

## Leave alone

- `tests/test_suite_conformance.py` is a byte-identical copy shared
  across the suite; change it upstream, not here.
