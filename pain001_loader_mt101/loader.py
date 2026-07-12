# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""SWIFT MT101 -> ISO 20022 pain.001 flat-record loader.

SWIFT MT101 (*Request for Transfer*) is the legacy message an account
owner sends to instruct one or more credit transfers from its account,
and that ISO 20022 ``pain.001`` (Customer Credit Transfer Initiation)
replaces under the CBPR+ / SWIFT MX migration. This loader bridges that
gap: pass an MT101 text payload and get back the flat records that the
:mod:`pain001` library validates against the ``pain.001.001.09`` JSON
schema and turns into pain.001 XML.

Unlike an MT103 (a single transfer), an MT101 carries a general
**sequence A** plus one *or more* repeating **sequence B** transaction
blocks, so :func:`parse_mt101` returns *one record per transaction*.
Sequence-A ordering-customer / account-servicing-institution fields
apply to every transaction unless a sequence-B block overrides them.

The MT101 grammar handled here is the mandatory + common-denominator
subset needed to populate a schema-valid pain.001 record:

* ``:20:``  Sender's Reference (seq A)      -> ``id`` + ``payment_information_id``
* ``:30:``  Requested Execution Date (seq A, ``YYMMDD``) -> ``date`` and
  ``requested_execution_date`` (``YYYY-MM-DD``)
* ``:21:``  Transaction Reference (seq B)    -> ``payment_id``
* ``:32B:`` Currency + Amount (seq B)        -> ``currency`` + ``payment_amount``
  (SWIFT comma-decimal; note :32B: has *no* value date, unlike MT103 :32A:)
* ``:50a:`` (H/G/F/K, seq A or B) Ordering Customer -> ``debtor_name`` /
  ``debtor_account_IBAN`` (and ``initiator_name``)
* ``:52a:`` (A/C/D, seq A or B) Account Servicing Institution -> ``debtor_agent_BIC``
* ``:57a:`` (A/C/D, seq B) Account With Institution -> ``creditor_agent_BIC``
* ``:59a:`` (—/A/F, seq B) Beneficiary -> ``creditor_name`` / ``creditor_account_IBAN``
* ``:70:``  Remittance Information (seq B, optional) -> ``remittance_information``
* ``:71A:`` Details of Charges (seq B) -> ``charge_bearer``
  (``OUR`` -> ``DEBT``, ``BEN`` -> ``CRED``, ``SHA`` -> ``SHAR``)

The pain.001 schema requires several fields that MT101 does not carry;
these are synthesised (documented so callers can override):

* ``payment_method`` is always ``"TRF"`` (an MT101 requests credit
  transfers).
* ``batch_booking`` defaults to ``False``.
* ``service_level_code`` defaults to ``"SEPA"`` (the schema enum admits
  only ``SEPA`` / ``URNS``); override for non-SEPA payments.
* ``charge_bearer`` defaults to ``"SLEV"`` when ``:71A:`` is absent or
  carries an unrecognised code (the schema requires a charge bearer).
* ``remittance_information`` defaults to ``"NOTPROVIDED"`` when ``:70:``
  is absent (the schema requires a non-empty value).
* ``nb_of_txs`` is the count of sequence-B blocks and ``ctrl_sum`` is the
  sum of every transaction amount; both are repeated on every record, as
  in a pain.001 group header.
* ``date`` (message creation date) reuses ``:30:`` because MT101 has no
  separate creation timestamp.
* ``initiator_name`` reuses the ordering-customer name.

Out of scope (deliberately -- this is the correct core mapping, not every
optional MT101 field):

* ``:23E:`` instruction codes and ``:25:`` / ``:28D:`` authorisation /
  sequence-number fields.
* ``:33B:`` instructed currency/amount, ``:36:`` exchange rate and
  ``:21F:`` FX deal reference (FX legs).
* ``:56a:`` intermediary and ``:51A:`` sending institutions.
* ``:77B:`` regulatory reporting and ``:25A:`` charges account.
* The SWIFT application header (blocks 1/2); this loader reads block 4
  only (it will unwrap a ``{4:...-}`` envelope if present).

For a record to be schema-valid the ordering customer must supply a name
and an IBAN account (``:50a:``), the account-servicing and account-with
institutions must supply BICs (``:52a:`` / ``:57a:``) and the beneficiary
account must be an IBAN (``:59a:``); a well-formed MT101 carries all of
these. When such an optional source is absent the corresponding key is
omitted rather than guessed -- the loader never crashes on unexpected
input. Only ``:20:``, ``:30:`` and, per transaction, ``:21:``, ``:32B:``
and a named beneficiary are treated as hard requirements that raise
:class:`ValueError`.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

__all__ = ["parse_mt101"]


# --- Mapping tables ---------------------------------------------------------

# MT101 field 71A "Details of Charges" -> pain.001 ChargeBearerType1Code.
_CHARGE_BEARER = {
    "OUR": "DEBT",  # all charges borne by the debtor
    "BEN": "CRED",  # all charges borne by the creditor
    "SHA": "SHAR",  # charges shared
}

# pain.001 requires a charge bearer; when :71A: is absent or unrecognised
# fall back to "following service level".
_DEFAULT_CHARGE_BEARER = "SLEV"

# pain.001 requires a service level from a two-value enum; SEPA is the
# common case. Documented so callers can override for URNS payments.
_DEFAULT_SERVICE_LEVEL = "SEPA"

# pain.001 requires non-empty remittance information; MT101 :70: is
# optional, so supply the ISO 20022 "not provided" sentinel.
_DEFAULT_REMITTANCE = "NOTPROVIDED"

# Sequence-B / sequence-A party tag families, in preference order.
_ORDERING_TAGS = ("50H", "50G", "50F", "50K", "50A", "50")
_SERVICING_TAGS = ("52A", "52C", "52D")
_ACCOUNT_WITH_TAGS = ("57A", "57C", "57D")
_BENEFICIARY_TAGS = ("59", "59A", "59F")


# --- Regex helpers ----------------------------------------------------------

# A field starts with :tag: at the beginning of a line. MT101 tags are two
# digits plus an optional single option letter (20, 21, 21R, 30, 32B, 50H).
_FIELD_HEAD_RE = re.compile(r"^:(\d{2}[A-Z]?):", re.MULTILINE)

# :32B:EUR1234,56  ->  CCY (3 alpha) | amount (comma-decimal). No value date.
_F32B_RE = re.compile(r"^(?P<ccy>[A-Z]{3})(?P<amt>[\d.,]+)$")

# :30: requested execution date is exactly six digits (YYMMDD).
_DATE_RE = re.compile(r"^\d{6}$")

# A BIC is 8 or 11 chars; this mirrors the pain.001 schema BIC pattern so any
# line we accept as a BIC also passes downstream validation.
_BIC_RE = re.compile(r"^[A-Z0-9]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?$")

# Structured (option F) sub-field line, e.g. "1/JOHN DOE" -> number, text.
_STRUCTURED_RE = re.compile(r"^(?P<num>\d)/(?P<text>.*)$")

# The block-4 envelope of a raw SWIFT message: {4:\n...\n-}.
_BLOCK4_RE = re.compile(r"\{4:(?P<body>.*?)-\}", re.DOTALL)


# --- Tokeniser --------------------------------------------------------------


def _unwrap_block4(text: str) -> str:
    """Return the block-4 body if the payload is a raw ``{4:...-}`` envelope.

    A bare tag list (the common representation) is returned unchanged.
    """
    match = _BLOCK4_RE.search(text)
    return match.group("body") if match else text


def _iter_fields(text: str) -> Iterator[tuple[str, str]]:
    """Yield ``(tag, value)`` pairs from an MT101 payload, in order.

    Values may span multiple lines: everything after a ``:tag:`` head up to
    (but not including) the next ``:tag:`` head is the value, with the tag
    stripped and surrounding whitespace normalised. Duplicate tags (the
    repeating sequence-B ``:21:`` in particular) are preserved in order.
    """
    body = _unwrap_block4(text)
    matches = list(_FIELD_HEAD_RE.finditer(body))
    for index, match in enumerate(matches):
        tag = match.group(1)
        value_start = match.end()
        value_end = (
            matches[index + 1].start() if index + 1 < len(matches) else len(body)
        )
        value = body[value_start:value_end].strip()
        yield tag, value


def _split_sequences(
    fields: list[tuple[str, str]],
) -> tuple[dict[str, str], list[dict[str, str]]]:
    """Split ordered fields into sequence A and repeating sequence-B blocks.

    Every field before the first ``:21:`` belongs to the general sequence A.
    Each ``:21:`` starts a new sequence-B transaction block; fields up to the
    next ``:21:`` belong to that block. Within each scope the first
    occurrence of a tag wins.
    """
    seq_a: dict[str, str] = {}
    blocks: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for tag, value in fields:
        if tag == "21":
            current = {"21": value}
            blocks.append(current)
        elif current is None:
            seq_a.setdefault(tag, value)
        else:
            current.setdefault(tag, value)
    return seq_a, blocks


# --- Field parsers ----------------------------------------------------------


def _content_lines(value: str) -> list[str]:
    """Split a party field into its free-text content lines.

    Blank lines and account lines (``/account`` or ``//account``) are dropped
    -- an account line identifies the account, not the party name. A trailing
    block trailer (``-}``) is stripped defensively.
    """
    lines: list[str] = []
    for raw in value.splitlines():
        stripped = raw.strip().rstrip("}").rstrip("-").strip()
        if stripped and not stripped.startswith("/"):
            lines.append(stripped)
    return lines


def _party_name(value: str) -> str | None:
    """Extract the party name from a 50a / 59a field (options A, F, K, none).

    * Option F (structured): the name is the ``1/`` sub-field.
    * Option K / plain 59 (name + address): the name is the first line after
      the optional account line.
    * Option A (account + BIC): there is no free-text name, so the BIC line
      is returned as a best-effort identifier.

    Returns ``None`` when the field carries only an account number.
    """
    lines = _content_lines(value)
    if not lines:
        return None
    for line in lines:
        match = _STRUCTURED_RE.match(line)
        if match and match.group("num") == "1":
            return match.group("text").strip() or None
    return lines[0]


def _party_account(value: str) -> str | None:
    """Extract the account identifier from a party field's ``/account`` line.

    Returns the account with leading slashes stripped, or ``None`` when the
    field carries no account line.
    """
    for raw in value.splitlines():
        stripped = raw.strip()
        if stripped.startswith("/"):
            return stripped.lstrip("/").strip()
    return None


def _party_bic(value: str) -> str | None:
    """Extract a BIC from an institution field (options A and C/D).

    Returns the first content line that matches the BIC shape, or ``None``
    (option D typically carries a name and address, not a BIC).
    """
    for line in _content_lines(value):
        if _BIC_RE.match(line):
            return line
    return None


def _parse_amount(raw: str) -> float:
    """Convert a SWIFT amount to a float.

    SWIFT uses a comma as the decimal separator and never a thousands
    separator, so ``1234,56`` -> ``1234.56`` and a trailing comma
    (``1234,``) means a whole amount.
    """
    return float(raw.replace(",", "."))


def _parse_date(yymmdd: str) -> str:
    """Format a 6-char ``YYMMDD`` date as an ISO ``YYYY-MM-DD`` date.

    Years use the SWIFT sliding window: 00-79 -> 20YY, 80-99 -> 19YY.
    """
    if not _DATE_RE.match(yymmdd):
        raise ValueError(f"Malformed :30: requested execution date {yymmdd!r}")
    year = int(yymmdd[0:2])
    century = 2000 if year < 80 else 1900
    return f"{century + year:04d}-{yymmdd[2:4]}-{yymmdd[4:6]}"


def _parse_f32b(value: str) -> tuple[str, float]:
    """Parse ``:32B:`` into (currency, amount)."""
    match = _F32B_RE.match(value.replace("\n", "").strip())
    if not match:
        raise ValueError(f"Malformed :32B: currency/amount {value!r}")
    return match.group("ccy"), _parse_amount(match.group("amt"))


def _lookup(sources: list[dict[str, str]], tags: tuple[str, ...]) -> str | None:
    """Return the first field value found scanning ``sources`` then ``tags``.

    A sequence-B block is passed before sequence A so a per-transaction
    override wins over the general value.
    """
    for source in sources:
        for tag in tags:
            if tag in source:
                return source[tag]
    return None


# --- Transaction parser -----------------------------------------------------


def _parse_transaction(block: dict[str, str], seq_a: dict[str, str]) -> dict[str, Any]:
    """Parse one sequence-B block (with sequence-A fallbacks) into a record.

    Raises:
        ValueError: If the transaction lacks ``:21:``, ``:32B:`` or a named
            beneficiary.
    """
    txn_ref = block.get("21", "").strip()
    if not txn_ref:
        raise ValueError("MT101 transaction missing required :21: reference")

    if "32B" not in block:
        raise ValueError(
            f"MT101 transaction :21:{txn_ref} missing required :32B: amount"
        )
    currency, amount = _parse_f32b(block["32B"])

    ordering = _lookup([block, seq_a], _ORDERING_TAGS)
    if ordering is not None:
        debtor_name = _party_name(ordering)
        debtor_account = _party_account(ordering)
    else:
        debtor_name = None
        debtor_account = None

    servicing = _lookup([block, seq_a], _SERVICING_TAGS)
    debtor_agent = _party_bic(servicing) if servicing is not None else None

    account_with = _lookup([block], _ACCOUNT_WITH_TAGS)
    creditor_agent = _party_bic(account_with) if account_with is not None else None

    beneficiary = _lookup([block], _BENEFICIARY_TAGS)
    if beneficiary is None:
        raise ValueError(
            f"MT101 transaction :21:{txn_ref} missing required "
            "beneficiary :59:/:59A:/:59F:"
        )
    creditor_name = _party_name(beneficiary)
    if not creditor_name:
        raise ValueError(f"MT101 transaction :21:{txn_ref} beneficiary carries no name")
    creditor_account = _party_account(beneficiary)

    charge_code = block.get("71A", "").strip().upper()
    charge_bearer = _CHARGE_BEARER.get(charge_code, _DEFAULT_CHARGE_BEARER)

    remittance = " ".join(block.get("70", "").split()) or _DEFAULT_REMITTANCE

    return {
        "payment_id": txn_ref,
        "payment_amount": amount,
        "currency": currency,
        "charge_bearer": charge_bearer,
        "creditor_name": creditor_name,
        "remittance_information": remittance[:140],
        "initiator_name": debtor_name,
        "debtor_name": debtor_name,
        "debtor_account_IBAN": debtor_account,
        "debtor_agent_BIC": debtor_agent,
        "creditor_agent_BIC": creditor_agent,
        "creditor_account_IBAN": creditor_account,
    }


# Record keys that are extracted from MT101 when present and omitted (never
# guessed) when their source field is absent.
_OPTIONAL_KEYS = (
    "initiator_name",
    "debtor_name",
    "debtor_account_IBAN",
    "debtor_agent_BIC",
    "creditor_agent_BIC",
    "creditor_account_IBAN",
)


# --- Top-level parser -------------------------------------------------------


def parse_mt101(text: str) -> list[dict[str, Any]]:
    """Parse an MT101 payload into pain.001 flat records.

    An MT101 carries one *or more* credit-transfer instructions (repeating
    sequence B), so the returned list holds one record per transaction. Each
    record's keys are the fields the :mod:`pain001` library validates against
    the ``pain.001.001.09`` schema. ``nb_of_txs`` and ``ctrl_sum`` describe
    the whole message and are repeated on every record.

    Args:
        text: The MT101 payload as a string. A raw ``{4:...-}`` block-4
            envelope, trailing whitespace and CRLF/LF differences are
            tolerated.

    Returns:
        A list of parsed flat records, one per sequence-B transaction. Keys
        whose source MT101 field is absent are omitted rather than guessed.

    Raises:
        ValueError: If a mandatory field is missing or malformed. The
            mandatory fields are ``:20:`` (sender's reference), ``:30:``
            (requested execution date), at least one transaction, and per
            transaction ``:21:`` (reference), ``:32B:`` (currency/amount) and
            a named beneficiary (``:59:`` / ``:59A:`` / ``:59F:``). The error
            message names the offending field.
    """
    seq_a, blocks = _split_sequences(list(_iter_fields(text)))

    msg_ref = seq_a.get("20", "").strip()
    if not msg_ref:
        raise ValueError("MT101 payload missing required :20: sender's reference")

    exec_raw = seq_a.get("30", "").strip()
    if not exec_raw:
        raise ValueError("MT101 payload missing required :30: requested execution date")
    exec_date = _parse_date(exec_raw)

    if not blocks:
        raise ValueError("MT101 payload has no transaction (missing sequence B / :21:)")

    transactions = [_parse_transaction(block, seq_a) for block in blocks]
    nb_of_txs = len(transactions)
    ctrl_sum = round(sum(txn["payment_amount"] for txn in transactions), 2)

    records: list[dict[str, Any]] = []
    for txn in transactions:
        record: dict[str, Any] = {
            "id": msg_ref,
            "date": exec_date,
            "nb_of_txs": nb_of_txs,
            "ctrl_sum": ctrl_sum,
            "payment_information_id": msg_ref,
            "payment_method": "TRF",
            "batch_booking": False,
            "service_level_code": _DEFAULT_SERVICE_LEVEL,
            "requested_execution_date": exec_date,
            "charge_bearer": txn["charge_bearer"],
            "payment_id": txn["payment_id"],
            "payment_amount": txn["payment_amount"],
            "currency": txn["currency"],
            "creditor_name": txn["creditor_name"],
            "remittance_information": txn["remittance_information"],
        }
        for key in _OPTIONAL_KEYS:
            value = txn[key]
            if value:
                record[key] = value
        records.append(record)

    return records
