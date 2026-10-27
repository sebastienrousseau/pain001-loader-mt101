# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
This package's version follows the [`pain001`](https://github.com/sebastienrousseau/pain001)
suite; the `0.0.1` release targets the `0.0.53` line of `pain001`.

## [Unreleased]

### Security

- `requirements/audit.txt` pinned filelock 4.1.0 for Python 3.10
  (GHSA-9vhv-jxww-xfm5, GHSA-567q-5qvw-pf92, GHSA-v4x8-3wr5-3wq8), which
  pip-audit on 3.12 skipped because of its marker. `audit.in` now floors
  `filelock >= 4.2.1`, and with the 3.10 entries gone the tree pins
  4.2.4.

### Removed

- Python 3.10 support. The floor is 3.11 (`requires-python = ">=3.11"`),
  the pain001 suite's decision for 0.0.75: 3.10 reaches end of life in
  October 2026, and current hypothesis releases need 3.11, which broke
  Dependabot's resolver for siblings on a 3.10 floor. CI tests 3.11 to
  3.14; ruff and mypy target 3.11; the 3.10 classifier, the `tomli`
  backport and the 3.10 branch in `scripts/check_suite_consistency.py`
  are gone, and `make pip-compile` compiles for 3.11 (only the packages
  for 3.10 leave). pip keeps 3.10 users on pain001-loader-mt101 0.0.74.

## [0.0.74] - 2026-10-21

Released in lockstep with `pain001` 0.0.74, the family's convergence
release (this package skips 0.0.73, which `pain001-mcp` published
alone). Two parser fixes change what `parse_mt101` accepts; everything
else is supply chain, CI and documentation.

### Security

- **An unterminated block-4 opener no longer costs quadratic time**
  (CWE-1333). `parse_mt101` found the `{4:...-}` envelope with a lazy
  regular expression, so each `{4:` without a closing `-}` made the
  search scan to the end of the text again: 120 KB of `{4:` took about
  110 seconds before the input was rejected. The envelope is now found
  in one pass, with the same result on every input. Every release up to
  0.0.72 is affected.

### Fixed

- `:30:` dates that do not exist are rejected with a `ValueError` naming
  `:30:`. `000000` used to come back as `2000-00-00` and `260230` as
  `2026-02-30`.
- `:32B:` amounts outside the SWIFT form are rejected with a
  `ValueError` naming `:32B:`. **Behaviour change:** an amount with a
  dot (`EUR1.234`, `EUR1000.50`) used to be read as a decimal point and
  is now refused, because SWIFT amounts never carry one; `1,2,3` and a
  bare `,` now raise the documented error instead of float's own; an
  amount over 15 characters (SWIFT `15d`), which could become an
  infinite amount, is refused.
- `scripts/check_suite_consistency.py` compares the tree with this
  package's own release on PyPI instead of the core's.
- `examples/01_minimal_parse.py` no longer prints names, IBANs and BICs
  (CodeQL `py/clear-text-logging-sensitive-data`); it lists the party
  keys with their values redacted.
- `CITATION.cff` states the licence as CFF 1.2.0 requires (`Apache-2.0`
  and `MIT`, either at the user's option); the SPDX expression it held
  did not validate.

### Changed

- `pain001 >= 0.0.74, < 1`, in `pyproject.toml` and every
  `requirements/*.in`.
- Every CI install is hash-pinned from `requirements/*.txt` (OpenSSF
  Scorecard Pinned-Dependencies), and the release build runs with
  `--no-isolation` from the pinned build tree. `certifi` is floored at
  2026.10.19 (GHSA-6q48-6c7w-9gw2) in the tooling trees that resolve it.
- New CI gates: `pip-audit` over every requirements file, complexity
  ceilings against `complexity-baseline.json` (empty: `parse_mt101` and
  `_parse_transaction` were split under the 60-line ceiling, with no
  change in output), Atheris fuzzing (`fuzz/`) and Hypothesis fuzzing in
  the test suite, mypy `--strict` over `scripts/`, and
  `scripts/verify_versions.py` ("Version sources agree"), which fails
  when any restatement of the version, or the `pain001` floor, differs
  from `pyproject.toml`.
- The README follows the family template, with a demo
  (`.github/demo.gif`, rendered by `make demo`), and its License section
  now states the dual `Apache-2.0 OR MIT` grant instead of Apache-2.0
  alone. New `docs/COMPARISON.md` and `docs/POLICIES.md`;
  `docs/benchmarks.md` is now `docs/BENCHMARKS.md` with a fresh run.
- Every page of the documentation site links the author from its
  copyright line.
- Since 0.0.72 on `main`: the sequence-B override test uses a mod-97
  valid IBAN and real BICs, every SPDX header states `Apache-2.0 OR MIT`,
  `make format` and `make lint` run ruff as CI does, and seven GitHub
  Actions were updated.

## [0.0.72] - 2026-09-28

Aligns the `pain001` suite on `0.0.72`, the core's coordinated release:
ISO 20022 schemas and Schematron validation rules, SLSA level 3 provenance
attestations, and dependency updates. Nothing in this package changed.

### Changed

- Version aligned to `0.0.72` across all `pain001` packages.
- The README and the documentation index link
  [What is pain.001?](https://pain001.com/pain-001/), an explainer of the
  target message's structure and versions.

## [0.0.71] - 2026-09-26

Aligns the `pain001` suite on `0.0.71`, the core's coordinated release:
request-local CEL policy rules, review-only correction suggestions,
explicit SFTP upload delivery, and release artifact inspection.
Nothing in this package changed.

### Changed

- Version aligned to `0.0.71` across all five `pain001` packages.
- `SECURITY.md`'s supported-version table follows the bump.

## [0.0.70] - 2026-09-13

Aligns the `pain001` suite on `0.0.70`: the core's rail rules now read the
CSV pipeline's column names, and its optional dependencies load on use
rather than on import. Nothing in this package changed.

### Changed

- Version aligned to `0.0.70` across all five `pain001` packages.
- `SECURITY.md`'s supported-version table follows the bump.

## [0.0.69] - 2026-09-12

Aligns the `pain001` suite on `0.0.69`, the core's third example-corpus
release: the tier 2 and 3 market packs, the CSV pipeline extension and
the pain.001 twin foundation (lossless ISO JSON twins with their
schemas). Nothing in this package changed.

### Changed

- Version aligned to `0.0.69` across all five `pain001` packages.
- `SECURITY.md`'s supported-version table follows the bump.

## [0.0.68] - 2026-09-12

Aligns the `pain001` suite on `0.0.68`, the core's second example-corpus
release: the tier-1 market packs (UK, SEPA core, US, CH, SE), coverage
files named by recipe and focus, and the tooling to apply a bank's own
guideline privately. Nothing in this package changed.

### Changed

- Version aligned to `0.0.68` across all five `pain001` packages.
- `SECURITY.md`'s supported-version table follows the bump.

## [0.0.67] - 2026-09-12

Aligns the `pain001` suite on `0.0.67`, the core's first example-corpus
release: validated pain.001 example files per country and rail with
their provenance, and the schema coverage sets. Nothing in this package
changed.

### Changed

- Version aligned to `0.0.67` across all five `pain001` packages.
- `SECURITY.md`'s supported-version table follows the bump.

## [0.0.66] - 2026-09-12

Aligns the `pain001` suite on `0.0.66`, the core release that adds
cross-record duplicate detection, the `/api/v1/ui` dashboard, GPG
flags and OpenTelemetry spans. Nothing in this package changed.

### Changed

- Version aligned to `0.0.66` across all five `pain001` packages.
- `SECURITY.md`'s supported-version table follows the bump.

## [0.0.65] - 2026-08-29

Aligns the `pain001` suite on one version number, and adds the gates this
repository was missing.

### Added

- `benches/bench_parse_mt101.py`. MT101 genuinely batches — sequence B
  repeats once per instruction — so unlike the MT103 loader there is a
  real scaling axis, and it is the one a payroll run moves along. Cost
  is linear across ten to five thousand instructions (exponent 1.03,
  roughly 6-8 µs each).
- The benchmark prints the **record count** beside the timings. A loader
  that silently stopped after the first instruction would show a falling
  µs/txn as the input grew — batching to read, dividing by work never
  done in fact. The sibling `pain001-loader-mt103` behaves exactly that
  way because an MT103 carries one transfer, and the two are easy to
  assume alike.
- `docs/benchmarks.md`, `CONTRIBUTING.md`.
- `scripts/check_suite_consistency.py` and a scheduled `Suite
  Consistency` workflow comparing this tree, and every published member,
  against PyPI.
- `tests/test_suite_conformance.py`, the shared suite conformance gate.

### Changed

- Version aligned to `0.0.65` across all five `pain001` packages, which
  had drifted to `0.0.62`, `0.0.64`, `0.0.63`, `0.0.62` and `0.0.63`.
- `SECURITY.md`'s supported-version table follows the bump.

## [0.0.62] - 2026-08-21

### Added

- **Benchmarks for the block-4 wire format and field-dense
  transactions.** The 0.0.61 set measured one shape: a bare field list
  with a uniform transaction. Banks send that list wrapped in
  `{1:...}{2:...}{4: ... -}`, which is the only thing that exercises
  `_unwrap_block4` — previously unbenchmarked. Measured at 1.10x a bare
  list.

  `_lookup` searches tag by tag, so the risk is it going quadratic in
  the number of fields present, which uniform fixtures cannot show. A
  transaction carrying every optional field costs 1.10x a minimal one.

- **`ruff format --check` in CI**, which `pain001-loader-xlsx` already
  enforced and this repo did not. Four files had drifted out of format
  with nothing configured to notice — the same shape of gap as a
  lockfile nobody installs from.

## [0.0.61] - 2026-08-20

Suite release with `pain001` 0.0.61. No change in this package.

The core's 0.0.61 is a performance release — libxml2 XSD validation and
a fix for quadratic CSV diagnostics — and neither touches the MT101
parser, which does its own parsing and does not go through either path.
The version moves because every member of the suite ships the same
number.

## [0.0.60] - 2026-08-20

Version-alignment release. No public API change and no change to the
MT101 -> pain.001 mapping.

### Changed

- **Joined the suite's single version line**, `0.0.2` -> `0.0.60`.
  Every package in the `pain001` suite now ships the same version
  number, so there is no compatibility table to consult. This package
  had been numbered independently and reached `0.0.2` against a `0.0.60`
  core; both were defensible under the previous policy, but a user could
  not tell that apart from drift. Versions advance in `0.0.1` steps from
  here and stay on the `0.0.x` line — `0.1.0` follows `0.0.999`.

  `0.0.3` through `0.0.59` were never released for this package and
  never will be.

### Added

- **Benchmarks and a scaling guard** (`tests/test_benchmarks.py`), run
  in CI with results kept as an artifact. The guard compares the parser
  against itself at 1000 and 4000 transactions rather than using a
  wall-clock threshold, so it is independent of runner speed; it was
  checked against the failure it exists for by injecting a
  per-transaction rescan, which moves the ratio to 11.3x against a
  ceiling of 8.

## [0.0.2] - 2026-07-18

### Changed

- Require `pain001 >= 0.0.55, < 1` (was `>= 0.0.53, < 1`) to propagate a
  security fix released in the `pain001` core library. No API or mapping
  changes in this loader.

## [0.0.1] - 2026-07-12

### Added

First release of `pain001-loader-mt101`, a SWIFT MT101 → ISO 20022
pain.001 converter and the second deliverable of the MT→MX converter
project (after
[`pacs008-loader-mt103`](https://github.com/sebastienrousseau/pacs008-loader-mt103)).
Companion to the
[`pain001`](https://github.com/sebastienrousseau/pain001) core library.

Public API: a single function `parse_mt101(text)` that returns a
`list[dict]` — one record per sequence-B transaction — whose keys are
exactly the flat-record fields `pain001` validates against the
`pain.001.001.09` JSON schema, so the records feed straight into
pain.001 generation.

#### Mapped MT101 fields

- `:20:` Sender's Reference → `id` + `payment_information_id`
- `:30:` Requested Execution Date → `requested_execution_date` + `date`
  (SWIFT sliding year window; `YYMMDD` → `YYYY-MM-DD`)
- `:21:` Transaction Reference (seq B) → `payment_id`
- `:32B:` Currency + Amount (seq B) → `currency` + `payment_amount`
  (SWIFT comma-decimal handled; no value date, unlike MT103 `:32A:`)
- `:50a:` Ordering Customer → `debtor_name`, `debtor_account_IBAN`,
  `initiator_name`
- `:52a:` Account Servicing Institution → `debtor_agent_BIC`
- `:57a:` Account With Institution (seq B) → `creditor_agent_BIC`
- `:59a:` Beneficiary (seq B) → `creditor_name`, `creditor_account_IBAN`
- `:70:` Remittance Information (seq B) → `remittance_information`
- `:71A:` Details of Charges (seq B) → `charge_bearer`
  (`OUR`→`DEBT`, `BEN`→`CRED`, `SHA`→`SHAR`)
- Message-level: `nb_of_txs` = count of sequence-B blocks, `ctrl_sum` =
  total of all amounts
- Synthesised defaults: `payment_method` = `TRF`, `batch_booking` =
  `False`, `service_level_code` = `SEPA`, `charge_bearer` fallback =
  `SLEV`, `remittance_information` fallback = `NOTPROVIDED`

#### Quality gates

- 100% line + branch coverage enforced via `--cov-fail-under=100`.
- 100% docstring coverage enforced via `interrogate`.
- Type-checked with `mypy --strict`; linted with `ruff`; formatted
  with `black`.
- Parsed records are verified schema-valid against the real `pain001`
  `SchemaValidator("pain.001.001.09")` in the test suite.

[0.0.2]: https://github.com/sebastienrousseau/pain001-loader-mt101/releases/tag/v0.0.2
[0.0.1]: https://github.com/sebastienrousseau/pain001-loader-mt101/releases/tag/v0.0.1
