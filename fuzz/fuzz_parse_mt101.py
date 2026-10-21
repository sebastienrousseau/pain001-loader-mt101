# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Coverage-guided fuzzing of ``parse_mt101`` with Atheris.

The contract, the same one ``tests/test_fuzz.py`` checks with Hypothesis:
on any text the loader returns records whose amounts are finite,
non-negative numbers and whose dates exist, or raises ``ValueError``. Any
other exception, or a malformed amount or date in a record, is a crash
that libFuzzer reports and minimises.

An input that starts with ``:`` or ``{`` is parsed as MT101 text as it
stands, so the files in ``fuzz/corpus/`` (real-shaped messages and the
inputs of fixed bugs) are seeds and regression cases at once. Any other
input is decoded into a sequence of MT101 fields.

Run (Linux x86_64, Python 3.12 to 3.14)::

    pip install --require-hashes -r requirements/fuzz.txt
    pip install --no-deps -e .
    python fuzz/fuzz_parse_mt101.py fuzz/corpus -max_total_time=60
"""

import datetime
import math
import sys

import atheris

with atheris.instrument_imports():
    from pain001_loader_mt101 import parse_mt101

TAGS = ["20", "21R", "30", "50H", "50K", "52A", "21", "32B", "57A", "59", "70", "71A"]


def _text(data: bytes) -> str:
    """The MT101 payload this input encodes."""
    if data[:1] in (b":", b"{"):
        return data.decode("utf-8", "replace")
    fdp = atheris.FuzzedDataProvider(data)
    fields = [
        f":{fdp.PickValueInList(TAGS)}:{fdp.ConsumeUnicodeNoSurrogates(48)}"
        for _ in range(fdp.ConsumeIntInRange(0, 16))
    ]
    return "\n".join(fields)


def test_one_input(data: bytes) -> None:
    """Parse one input and hold every record to the contract."""
    try:
        records = parse_mt101(_text(data))
    except ValueError:
        return
    for record in records:
        amount = record["payment_amount"]
        if not (math.isfinite(amount) and amount >= 0):
            raise AssertionError(f"amount out of range: {amount!r}")
        if not math.isfinite(record["ctrl_sum"]):
            raise AssertionError(f"ctrl_sum out of range: {record['ctrl_sum']!r}")
        try:
            datetime.date.fromisoformat(record["requested_execution_date"])
        except ValueError as exc:
            raise AssertionError(f"impossible date in output: {exc}") from exc


def main() -> None:
    """Hand the harness to libFuzzer."""
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
