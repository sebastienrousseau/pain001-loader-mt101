# pain001-loader-mt101: MT101 → pain.001 loader

**Convert legacy SWIFT MT101 requests for transfer into the flat records
that the [`pain001`][core] library validates and turns into ISO 20022
pain.001 XML.** A single `parse_mt101(text)` call returns a `list[dict]`
— one record per transaction — ready to feed straight into pain.001
generation.

> **Latest release: v0.0.1.** The second deliverable of the MT→MX
> converter project (after
> [`pacs008-loader-mt103`](https://github.com/sebastienrousseau/pacs008-loader-mt103)).
> SWIFT MT-MX coexistence ends in **November 2025**; this loader bridges
> the window where upstream systems still emit MT101 but downstream
> tooling expects pain.001.

## Contents

- [Overview](#overview)
- [Install](#install)
- [Quick Start](#quick-start)
- [Field Mapping](#field-mapping)
- [Assumptions and defaults](#assumptions-and-defaults)
- [Out of scope](#out-of-scope)
- [Examples](#examples)
- [Development](#development)
- [Security](#security)
- [License](#license)

## Overview

`pain001-loader-mt101` is a small, focused companion to the
[`pain001`][core] ISO 20022 Customer Credit Transfer Initiation library.
It does one thing well: parse the mandatory + common-denominator MT101
grammar and hand back flat records whose keys are exactly the ones
`pain001` validates against the `pain.001.001.09` JSON schema. Unlike an
MT103 (one transfer), an MT101 can carry **many** transactions
(repeating sequence B), so `parse_mt101` returns one record per
transaction. The correctness proof is that a realistic multi-transaction
MT101 maps to records that pass
`SchemaValidator("pain.001.001.09").validate_batch(...)` with zero
errors.

## Install

`pain001-loader-mt101` requires **Python 3.10+** and pulls in `pain001`
automatically.

```bash
pip install pain001-loader-mt101
```

## Quick Start

```python
from pain001_loader_mt101 import parse_mt101

mt101 = """:20:MSGREF2026070901
:21R:CUSTREF-A
:50H:/DE89370400440532013000
GLOBAL IMPORTS GMBH
100 HAFEN STRASSE
HAMBURG
:52A:DEUTDEFF
:30:260712
:21:TXN-REF-0001
:32B:EUR12345,67
:57A:CHASUS33
:59:/GB29NWBK60161331926819
ACME TRADING LTD
1 CORPORATE AVENUE
LONDON
:70:INVOICE 998877
:71A:SHA
:21:TXN-REF-0002
:32B:USD5000,00
:57A:BOFAUS3N
:59:/FR1420041010050500013M02606
LES FLEURS SARL
:70:CONTRACT 445566
:71A:OUR
"""

records = parse_mt101(mt101)
print(len(records))                       # 2
print(records[0]["payment_amount"])       # 12345.67
print(records[0]["charge_bearer"])        # SHAR
print(records[0]["nb_of_txs"])            # 2 (message-level)

# Validate against the real pain.001 schema:
from pain001.validation.schema_validator import SchemaValidator
total, valid, errors = SchemaValidator("pain.001.001.09").validate_batch(records)
assert valid == total and not errors
```

## Field Mapping

`parse_mt101(text: str) -> list[dict]` — one record per sequence-B
transaction. Sequence-A `:50a:` / `:52a:` apply to every transaction
unless a sequence-B block overrides them.

| MT101 field | Seq | Meaning | pain.001 key | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `:20:` | A | Sender's Reference | `id`, `payment_information_id` | Message-level |
| `:30:` | A | Requested Execution Date (`YYMMDD`) | `requested_execution_date`, `date` | `→ YYYY-MM-DD`; SWIFT sliding year window |
| `:21:` | B | Transaction Reference | `payment_id` | One per transaction |
| `:32B:` | B | Currency + Amount | `currency`, `payment_amount` | No value date; comma-decimal → float |
| `:50H/50G/50F/50K/50A:` | A/B | Ordering Customer | `debtor_name`, `debtor_account_IBAN`, `initiator_name` | Name from F (`1/`), K/H (name lines) or A (BIC); account from `/IBAN` line |
| `:52A/52C/52D:` | A/B | Account Servicing Institution | `debtor_agent_BIC` | BIC from A/C (or a BIC in D) |
| `:57A/57C/57D:` | B | Account With Institution | `creditor_agent_BIC` | BIC from A/C (or a BIC in D) |
| `:59/59A/59F:` | B | Beneficiary | `creditor_name`, `creditor_account_IBAN` | Name from plain 59, A (BIC) or F (`1/`) |
| `:70:` | B | Remittance Information | `remittance_information` | Whitespace-collapsed, capped at 140 chars |
| `:71A:` | B | Details of Charges | `charge_bearer` | `OUR`→`DEBT`, `BEN`→`CRED`, `SHA`→`SHAR` |
| — | — | (synthesised) | `nb_of_txs`, `ctrl_sum` | Count of, and total amount over, sequence-B blocks |
| — | — | (synthesised) | `payment_method`, `batch_booking`, `service_level_code` | `TRF`, `False`, `SEPA` |

## Assumptions and defaults

The pain.001 schema requires fields MT101 does not carry; these are
synthesised (override downstream as needed):

- **`payment_method = "TRF"`** — an MT101 requests credit transfers.
- **`batch_booking = False`**.
- **`service_level_code = "SEPA"`** — the schema enum admits only
  `SEPA` / `URNS`; override for non-SEPA payments.
- **`charge_bearer = "SLEV"`** when `:71A:` is absent or unrecognised —
  the schema requires a charge bearer.
- **`remittance_information = "NOTPROVIDED"`** when `:70:` is absent —
  the schema requires a non-empty value.
- **`nb_of_txs` / `ctrl_sum`** describe the whole message (count of and
  total over sequence-B blocks) and are repeated on every record, as in
  a pain.001 group header.
- **`date`** (message creation date) reuses `:30:` — MT101 has no
  separate creation timestamp. Two-digit years follow the SWIFT sliding
  window (00–79 → 20YY, 80–99 → 19YY).
- **`initiator_name`** reuses the ordering-customer name.
- **Absent optional fields are omitted, not guessed.** A schema-valid
  pain.001 record needs the ordering-customer name + IBAN (`:50a:`), the
  account-servicing and account-with BICs (`:52a:` / `:57a:`) and the
  beneficiary IBAN (`:59a:`); a well-formed MT101 carries all of these.
- **Hard requirements** — only `:20:`, `:30:`, at least one transaction,
  and per transaction `:21:`, `:32B:` and a named beneficiary
  (`:59:`/`:59A:`/`:59F:`) raise `ValueError`. Everything else is
  best-effort; the loader never crashes on unexpected input.

## Out of scope

This is the correct **core** MT101 → pain.001 mapping, not every
optional field. Deliberately excluded in v0.0.1:

- `:23E:` instruction codes, `:25:` / `:28D:` authorisation / sequence
  fields.
- `:33B:` instructed currency/amount, `:36:` exchange rate, `:21F:` FX
  deal reference (FX legs).
- `:56a:` intermediary and `:51A:` sending institutions.
- `:77B:` regulatory reporting and `:25A:` charges account.
- The SWIFT application header (blocks 1/2). This loader reads block 4
  only (it unwraps a `{4:...-}` envelope if present).

## Examples

Two runnable scripts live in `examples/`, exercised in CI:

- [`01_minimal_parse.py`](examples/01_minimal_parse.py) — parse and
  print the flat records.
- [`02_validate_against_pain001.py`](examples/02_validate_against_pain001.py)
  — parse, then validate against the real `pain.001.001.09` schema.

## Development

```bash
git clone https://github.com/sebastienrousseau/pain001-loader-mt101
cd pain001-loader-mt101
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                            # 100% line + branch coverage gate
interrogate pain001_loader_mt101  # 100% docstring gate
mypy pain001_loader_mt101         # strict
```

## Security

`pain001-loader-mt101` parses a flat text format with no XML envelope —
the XXE / billion-laughs surface lives upstream. Field regexes are
anchored and bounded, so catastrophic backtracking is not a concern.
See [`SECURITY.md`](SECURITY.md).

## License

Licensed under the [Apache License, Version 2.0][01]. Any contribution
submitted for inclusion shall be licensed as above, without additional
terms.

[01]: https://opensource.org/license/apache-2-0/
[core]: https://github.com/sebastienrousseau/pain001
