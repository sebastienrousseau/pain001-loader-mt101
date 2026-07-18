# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
This package's version follows the [`pain001`](https://github.com/sebastienrousseau/pain001)
suite; the `0.0.1` release targets the `0.0.53` line of `pain001`.

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
