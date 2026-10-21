<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Comparison

What this compares: the ways a payment batch reaches `pain001`, and the
Python packages on PyPI that parse SWIFT MT payment messages. Checked on
2026-10-21 against `pain001-loader-mt101` at this commit, the `pain001`
0.0.72 and `pain001-loader-xlsx` 0.0.72 READMEs, and PyPI's JSON API.

## Inputs to pain001

| | pain001 (core) | pain001-loader-xlsx | pain001-loader-mt101 |
| :--- | :--- | :--- | :--- |
| Input | CSV, SQLite, JSON, JSONL, Python records; optional Parquet | Excel `.xlsx` / `.xlsm`, first sheet | SWIFT MT101 text, bare or in a `{4:...-}` block |
| How it plugs in | Built in | `pain001.loaders` entry point | A function: `parse_mt101(text)` returns the records |
| Records per input | One per row | One per row | One per sequence-B transaction |
| Fields pain.001 needs and the input lacks | Supplied by the caller | Supplied by the caller | Synthesised and documented (`payment_method`, `service_level_code`, ...) |
| Licence | Apache-2.0 OR MIT | Apache-2.0 OR MIT | Apache-2.0 OR MIT |

## MT parsers on PyPI

No package on PyPI parses MT101 under the names checked: `mt101`,
`python-mt101`, `swift-mt`, `swiftmt`, `swift-mt-parser`, `swift-parser`,
`mt-parser`, `mt-message`, `mt-messages`, `swiftmessage` and
`swift-messages` all return 404 from `https://pypi.org/pypi/<name>/json`.
This is a search of likely names, not a proof that none exists.

| | pain001-loader-mt101 | mt103 1.1.1 |
| :--- | :--- | :--- |
| Message | MT101 (request for transfer, many transactions) | MT103 (single customer credit transfer) |
| Output | pain.001 flat records, validated by `pain001` | Parsed MT103 fields |
| Licence | Apache-2.0 OR MIT | GPL-3.0-or-later |

## When to pick which

Pick this package when the input is MT101 and the output is pain.001.
Use the `pain001` core's own loaders when the batch already exists as
rows, and `pain001-loader-xlsx` when it arrives as a spreadsheet. For an
MT103 going to pacs.008, the family's sibling is
[`pacs008-loader-mt103`](https://github.com/sebastienrousseau/pacs008-loader-mt103).

## Evidence

- `pain001`: the "Capabilities at a glance" table of its README
  (`Input | CSV, SQLite, JSON, JSONL, Python records; optional Parquet and
  plugins`).
- `pain001-loader-xlsx`: `[project.entry-points."pain001.loaders"]` in its
  `pyproject.toml`.
- `pain001-loader-mt101`: `pain001_loader_mt101/loader.py`; `pyproject.toml`
  declares no entry point.
- `mt103`: PyPI metadata for 1.1.1 (summary "Parse MT103 messages from the
  Swift payments network", licence `GPL-3.0-or-later`).
