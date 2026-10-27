<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

<p align="center">
  <img src="https://cloudcdn.pro/pain001/v1/logos/pain001.svg" alt="pain001-loader-mt101 logo" width="128" />
</p>

<h1 align="center">pain001-loader-mt101</h1>

<p align="center">
  Turns SWIFT MT101 requests for transfer into the flat records pain001 validates and writes as ISO 20022 pain.001.
</p>

<p align="center">
  <a href="https://github.com/sebastienrousseau/pain001-loader-mt101/actions"><img src="https://img.shields.io/github/actions/workflow/status/sebastienrousseau/pain001-loader-mt101/ci.yml?style=for-the-badge&logo=github" alt="Build" height="28" /></a>
  <a href="https://pypi.org/project/pain001-loader-mt101/"><img src="https://img.shields.io/pypi/v/pain001-loader-mt101?style=for-the-badge&color=fc8d62&logo=python" alt="Registry" height="28" /></a>
  <a href="https://sebastienrousseau.com/pain001-loader-mt101/"><img src="https://img.shields.io/badge/docs-sphinx-blue?style=for-the-badge&labelColor=555555&logo=readthedocs" alt="Docs" height="28" /></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/sebastienrousseau/pain001-loader-mt101"><img src="https://img.shields.io/ossf-scorecard/github.com/sebastienrousseau/pain001-loader-mt101?style=for-the-badge&label=OpenSSF%20Scorecard&logo=openssf" alt="OpenSSF Scorecard" height="28" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0%20OR%20MIT-blue.svg?style=for-the-badge" alt="License: Apache-2.0 OR MIT" height="28" /></a>
  <a href="https://github.com/sebastienrousseau/pain001-loader-mt101/blob/main/docs/POLICIES.md"><img src="https://img.shields.io/badge/Python-3.11%2B-93450a.svg?style=for-the-badge&logo=python" alt="Python 3.11 or newer" height="28" /></a>
</p>

<p align="center">
  <img src=".github/demo.gif" alt="pain001-loader-mt101 demo: the MT101 text in examples/01_minimal_parse.py, the pain.001 records it prints with party data redacted, then a :30: date of 30 February rejected with a ValueError" width="100%" />
</p>

---

## Contents

**Getting started**

- [Install](#install) — `pip`, one runtime dependency
- [Requirements](#requirements) — toolchain floor, platforms
- [Quick Start](#quick-start) — one call from MT101 text to schema-valid pain.001 records

**The pain001-loader-mt101 ecosystem**

- [The pain001-loader-mt101 ecosystem](#the-pain001-loader-mt101-ecosystem) — the pain001 core, its MCP and LSP servers and its loaders

**Library reference**

- [Capabilities at a glance](#capabilities-at-a-glance) — the current surface by theme
- [Ecosystem comparison](#ecosystem-comparison) — short matrix; full table at [`docs/COMPARISON.md`](docs/COMPARISON.md)
- [Benchmarks](#benchmarks) — headline numbers; full table at [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md)
- [Features](#features) — module-level capability list
- [Configuration](#configuration) — core options
- [Examples](#examples) — runnable example index

**Operational**

- [When not to use pain001-loader-mt101](#when-not-to-use-pain001-loader-mt101) — limitations
- [Development](#development) — make targets, fuzzing, CI
- [Security](#security) — guarantees and compliance
- [Documentation](#documentation) — all reference docs
- [Stability guarantees](#stability-guarantees) — SemVer axis, output stability, minimum toolchain discipline
- [License](#license)

---

## Install

### As a Python library

```sh
pip install pain001-loader-mt101
```

> **Latest release: v0.0.74**: impossible `:30:` dates and `:32B:`
> amounts outside the SWIFT form are rejected, released in lockstep with
> the pain001 suite, for Python 3.10+.

The package pulls in [`pain001`][core] (0.0.74 or newer, below 1) and
nothing else. There is no command-line entry point: it is a library.

---

## Requirements

- Python 3.11 or newer, tested in CI on 3.11, 3.12, 3.13 and 3.14 on
  Linux ([toolchain policy](docs/POLICIES.md)).
- `pain001` 0.0.74 or newer on the 0.x line.
- Pure Python, so any platform CPython runs on; CI exercises Linux only.

---

## Quick Start

```python
from pain001.validation.schema_validator import SchemaValidator
from pain001_loader_mt101 import parse_mt101

mt101 = """:20:MSGREF2026070901
:30:260712
:50H:/DE89370400440532013000
GLOBAL IMPORTS GMBH
:52A:DEUTDEFF
:21:TXN-REF-0001
:32B:EUR12345,67
:57A:CHASUS33
:59:/GB29NWBK60161331926819
ACME TRADING LTD
:70:INVOICE 998877
:71A:SHA
"""

records = parse_mt101(mt101)
print(len(records))                  # 1
print(records[0]["payment_amount"])  # 12345.67
print(records[0]["charge_bearer"])   # SHAR

total, valid, errors = SchemaValidator("pain.001.001.09").validate_batch(records)
assert valid == total and not errors
```

`parse_mt101` returns one record per sequence-B transaction, with the keys
`pain001` validates against the `pain.001.001.09` schema, so the records go
straight into pain.001 generation.

---

## The pain001-loader-mt101 ecosystem

This package is one of the pain001 suite. The core, its MCP and LSP
servers and its two loaders release together at one version, core first.
New to the target format? [What is pain.001?](https://pain001.com/pain-001/)
explains it, and <https://pain001.com/mt101-migration/> sets out the
MT101 migration case.

| Component | Purpose | Use case |
| :--- | :--- | :--- |
| [`pain001`][core] | Generates and validates ISO 20022 payment files from tabular data | The core library these records feed |
| **`pain001-loader-mt101`** | SWIFT MT101 text to pain.001 flat records | A treasury or ERP system still emits MT101 |
| [`pain001-loader-xlsx`][xlsx] | Excel loader plugin for `.xlsx` / `.xlsm` | Payment batches kept in spreadsheets |
| [`pain001-mcp`][mcp] | MCP server exposing pain001 validation, generation and inspection | Agent workflows over payment files |
| [`pain001-lsp`][lsp] | Language server for pain001 input files | Editor support |

---

## Capabilities at a glance

| Area | Capability | Status |
| :--- | :--- | :--- |
| Parsing | Sequence A (`:20:`, `:30:`, `:50a:`, `:52a:`) and repeating sequence B (`:21:`, `:32B:`, `:50a:`, `:52a:`, `:57a:`, `:59a:`, `:70:`, `:71A:`) | Supported |
| Envelope | A raw `{4:...-}` block 4, CRLF or LF | Supported |
| Output | One pain.001 record per transaction; `nb_of_txs` and `ctrl_sum` on each | Supported |
| Validation | Missing `:20:`, `:30:`, `:21:`, `:32B:` or named beneficiary | Rejected with `ValueError` |
| Validation | `:30:` dates that do not exist, `:32B:` amounts outside the SWIFT form | Rejected since 0.0.74 |
| FX legs | `:33B:`, `:36:`, `:21F:` | Not mapped |
| Header blocks | SWIFT blocks 1 and 2 | Not read |

---

## Ecosystem comparison

`pain001` takes rows (CSV, SQLite, JSON, JSONL, Python records) and
`pain001-loader-xlsx` takes spreadsheets. This package is the path for
MT101 text. A search of likely names on PyPI found no other MT101 parser;
the nearest is `mt103`, which reads MT103 only.

| Project | Input | Records per input | Licence |
| :--- | :---: | :---: | :---: |
| **pain001-loader-mt101** | MT101 text | One per transaction | Apache-2.0 OR MIT |
| `pain001-loader-xlsx` | `.xlsx` / `.xlsm` | One per row | Apache-2.0 OR MIT |
| `mt103` 1.1.1 | MT103 text | One message | GPL-3.0-or-later |

See [`docs/COMPARISON.md`](docs/COMPARISON.md) for the evidence and complete matrix.

---

## Benchmarks

`benches/bench_parse_mt101.py` grows one message from 10 to 5,000
transactions and reports microseconds per transaction and a growth
exponent. The number to read is the shape: per-transaction cost should
stay flat. Nothing asserts a time; `tests/test_benchmarks.py` asserts the
scaling ratio, and CI runs the benchmark with `--quick`.

| Scenario | Result | Environment |
| :--- | ---: | :--- |
| One MT101, 1,000 transactions (145 KB) | 14.61 ms, 14.61 µs/txn | Apple A18 Pro, CPython 3.12.15, shared machine under load |
| One MT101, 5,000 transactions (725 KB) | 89.34 ms, 17.87 µs/txn | same run |
| Growth exponent, 10 to 5,000 transactions | 1.06 (linear) | same run |

See [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) for methodology and full results.

---

## Features

- **One function.** `parse_mt101(text)` returns `list[dict]`, one record
  per sequence-B transaction. Sequence-A `:50a:` and `:52a:` apply to
  every transaction unless a sequence-B block overrides them.
- **Field mapping.**

  | MT101 field | Seq | Meaning | pain.001 key |
  | :--- | :--- | :--- | :--- |
  | `:20:` | A | Sender's reference | `id`, `payment_information_id` |
  | `:30:` | A | Requested execution date (`YYMMDD`) | `requested_execution_date`, `date` |
  | `:21:` | B | Transaction reference | `payment_id` |
  | `:32B:` | B | Currency and amount | `currency`, `payment_amount` |
  | `:50H/G/F/K/A:` | A/B | Ordering customer | `debtor_name`, `debtor_account_IBAN`, `initiator_name` |
  | `:52A/C/D:` | A/B | Account servicing institution | `debtor_agent_BIC` |
  | `:57A/C/D:` | B | Account with institution | `creditor_agent_BIC` |
  | `:59/59A/59F:` | B | Beneficiary | `creditor_name`, `creditor_account_IBAN` |
  | `:70:` | B | Remittance information | `remittance_information` (140 characters at most) |
  | `:71A:` | B | Details of charges | `charge_bearer` (`OUR` to `DEBT`, `BEN` to `CRED`, `SHA` to `SHAR`) |

- **Synthesised fields**, documented so callers can override them:
  `payment_method="TRF"`, `batch_booking=False`,
  `service_level_code="SEPA"`, `charge_bearer="SLEV"` when `:71A:` is
  absent or unknown, `remittance_information="NOTPROVIDED"` when `:70:`
  is absent; `date` reuses `:30:` and `initiator_name` the ordering
  customer's name.
- **Absent optional fields are omitted, not guessed.**
- **Errors name the field.** Every `ValueError` names the MT101 field
  that is missing or malformed.

---

## Configuration

None. `parse_mt101` takes the text and nothing else; the synthesised
defaults above are fixed, and callers override them on the returned
records.

---

## Examples

- [`examples/01_minimal_parse.py`](examples/01_minimal_parse.py): parse a
  two-transaction MT101 and print each record, with names, IBANs and BICs
  redacted.
- [`examples/02_validate_against_pain001.py`](examples/02_validate_against_pain001.py):
  parse, then validate against the `pain.001.001.09` schema.

Both run in CI on every pull request.

---

## When not to use pain001-loader-mt101

- **Your batch is already rows or a spreadsheet.** Use the `pain001` core
  loaders or [`pain001-loader-xlsx`][xlsx].
- **You have MT103.** That is a single transfer going to pacs.008; see
  [`pacs008-loader-mt103`](https://github.com/sebastienrousseau/pacs008-loader-mt103).
- **You need FX legs, regulatory reporting or authorisation fields**
  (`:33B:`, `:36:`, `:21F:`, `:77B:`, `:25:`, `:28D:`, `:23E:`): they are
  not mapped.
- **You need the SWIFT header blocks.** Only block 4 is read.
- **Your payments are not SEPA.** `service_level_code` defaults to
  `SEPA`; set `URNS` on the records yourself.
- **Your MT101 arrives PGP-encrypted.** Decrypt it first; the loader
  takes plaintext.

---

## Development

```bash
git clone https://github.com/sebastienrousseau/pain001-loader-mt101
cd pain001-loader-mt101
make install   # .venv from the hash-pinned requirements/test.txt and lint.txt
make check
```

`make check` runs ruff, mypy in strict mode, the complexity ceilings, the
version-agreement check, pytest with a 100% line and branch coverage gate
(Hypothesis fuzzing included), interrogate at 100% docstring coverage and
the examples. CI also runs the dependency audit (`pip-audit` over every
`requirements/*.txt`), Atheris fuzzing of `parse_mt101` (two minutes per
change, thirty weekly, seeded from `fuzz/corpus/`), mutation testing of
the parser, CodeQL, OpenSSF Scorecard, the DCO check and a daily Suite
Consistency check against PyPI. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Security

The loader parses text: it reads no files, opens no sockets and parses no
XML. Input outside the grammar (including dates that do not exist and
amounts outside the SWIFT form) is rejected with a `ValueError` naming
the field. Cap the size of untrusted input before parsing it. The parser is fuzzed with Atheris in CI and
with Hypothesis in the test suite. Releases are published from a signed
tag through PyPI Trusted Publishing, with SLSA build provenance, sigstore
signatures and SPDX and CycloneDX SBOMs.

Report vulnerabilities according to [`SECURITY.md`](SECURITY.md).

---

## Documentation

[User manual](https://sebastienrousseau.com/pain001-loader-mt101/) ·
[API reference](docs/api.md) ·
[Developer guide](CONTRIBUTING.md) ·
[Family map](#the-pain001-loader-mt101-ecosystem) ·
[Changelog](CHANGELOG.md) · [Policies](docs/POLICIES.md) ·
[Architecture](ARCHITECTURE.md) · [Decisions](docs/adr/index.md)

---

## Stability guarantees

The project is pre-1.0 and versions advance in `0.0.1` steps, in lockstep
with the pain001 suite. The breaking axis is `parse_mt101`'s signature and
the records it produces for a given input: a change to that output is
breaking even when no signature moves, and the changelog calls it out
(0.0.74 rejecting impossible `:30:` dates and `:32B:` amounts with a dot).
The Python floor moves only as described in the
[toolchain policy](docs/POLICIES.md).

---

## License

This project is dual-licensed under either:

* Apache License, Version 2.0 ([`LICENSE-APACHE`](LICENSE-APACHE) or <https://www.apache.org/licenses/LICENSE-2.0>)
* MIT License ([`LICENSE-MIT`](LICENSE-MIT) or <https://opensource.org/licenses/MIT>)

at your option. Dependencies keep their own licences.

[core]: https://github.com/sebastienrousseau/pain001
[mcp]: https://github.com/sebastienrousseau/pain001-mcp
[lsp]: https://github.com/sebastienrousseau/pain001-lsp
[xlsx]: https://github.com/sebastienrousseau/pain001-loader-xlsx
