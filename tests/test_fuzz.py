# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Property-based fuzzing of ``parse_mt101``: the contract on any input.

The loader takes whatever a treasury system or an agent hands it. On any
text it must either return a list of records whose money and dates are
well formed, or raise ``ValueError`` naming what was wrong. Anything else
(another exception, an amount that is not a finite positive number, a
date that does not exist) is a defect, because the record goes on to
become a payment. ``fuzz/fuzz_parse_mt101.py`` holds Atheris to the same
contract in CI.
"""

from __future__ import annotations

import datetime
import math
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from pain001_loader_mt101 import parse_mt101

FUZZ = settings(max_examples=400, deadline=None)
CORPUS = Path(__file__).resolve().parent.parent / "fuzz" / "corpus"

TAGS = ["20", "21R", "30", "50H", "52A", "21", "32B", "57A", "59", "70", "71A"]
YYMMDD = st.text("0123456789", min_size=6, max_size=6)
AMOUNTS = st.text("0123456789,.", min_size=1, max_size=20)
F32B = st.builds(
    lambda ccy, amt: f"{ccy}{amt}", st.sampled_from(["EUR", "USD"]), AMOUNTS
)
VALUES = st.one_of(
    st.text(max_size=40),
    F32B,
    YYMMDD,
    st.sampled_from(["/DE89370400440532013000\nACME", "DEUTDEFF", "OUR", ""]),
)
HEADER = st.builds(
    lambda ref, date: [("20", ref), ("30", date)],
    st.text("ABC123", min_size=1, max_size=10),
    YYMMDD,
)
TRANSACTION = st.builds(
    lambda ref, amount, extra: [("21", ref), ("32B", amount), *extra],
    st.text("ABC123", min_size=1, max_size=10),
    F32B,
    st.lists(st.tuples(st.sampled_from(TAGS), VALUES), max_size=4),
)
FIELDS = st.builds(
    lambda head, body: head + [field for txn in body for field in txn],
    HEADER,
    st.lists(TRANSACTION, min_size=1, max_size=4),
)


def _payload(fields: list[tuple[str, str]]) -> str:
    return "".join(f":{tag}:{value}\n" for tag, value in fields)


def _check_record(record: dict[str, Any]) -> None:
    amount = record["payment_amount"]
    assert isinstance(amount, float) and math.isfinite(amount), amount
    assert amount >= 0, amount
    assert math.isfinite(record["ctrl_sum"]), record["ctrl_sum"]
    for key in ("date", "requested_execution_date"):
        datetime.date.fromisoformat(record[key])


def _check(text: str) -> None:
    try:
        records = parse_mt101(text)
    except ValueError:
        return
    assert records, "a successful parse returns at least one record"
    for record in records:
        _check_record(record)


@FUZZ
@given(text=st.text(max_size=400))
def test_arbitrary_text(text: str) -> None:
    _check(text)


@FUZZ
@given(fields=FIELDS)
def test_mt101_shaped_fields(fields: list[tuple[str, str]]) -> None:
    _check(_payload(fields))


@pytest.mark.parametrize("seed", sorted(p.name for p in CORPUS.iterdir()), ids=str)
def test_the_fuzz_corpus_replays(seed: str) -> None:
    """Every seed and fixed-bug input in fuzz/corpus, on every run."""
    _check((CORPUS / seed).read_text(encoding="utf-8"))
