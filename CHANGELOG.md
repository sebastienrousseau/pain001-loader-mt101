# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
This package's version follows the [`pain001`](https://github.com/sebastienrousseau/pain001)
suite; the `0.0.1` release targets the `0.0.53` line of `pain001`.

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
