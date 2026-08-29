#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Throughput of :func:`parse_mt101` as a payment batch grows.

MT101 is a *request for transfer*, and unlike MT103 it genuinely
batches: sequence B repeats, once per credit-transfer instruction, and
the loader returns one flat `pain.001` record per instruction. So there
is a real scaling axis here, and it is the one a corporate treasury
actually moves along -- a payroll run or a supplier batch is hundreds or
thousands of instructions inside a single message.

What this watches for is **shape, not speed**. A parser linear in
instructions stays usable as the batch grows; one that goes quadratic --
because some lookup rescans the instructions already parsed -- looks
perfectly healthy on a fixture of ten and falls over on payroll day. Read
``us/txn``: flat across sizes is what you want. The growth exponent says
the same thing in one number, where 1.0 is linear and 2.0 quadratic.

The record count is printed beside the timings deliberately. A loader
that silently stopped after the first instruction would show a falling
``us/txn`` as the input grew, which reads as batching and would be the
opposite -- dividing by instructions never parsed. Watching the record
count track the input is what rules that out. (Its sibling
`pain001-loader-mt103` genuinely behaves that way, because an MT103
carries exactly one transfer; the two loaders are easy to assume are
alike.)

Run::

    python benches/bench_parse_mt101.py
    python benches/bench_parse_mt101.py --json
    python benches/bench_parse_mt101.py --quick     # what CI runs

Timings are wall-clock on one machine and are not comparable between
machines, so nothing here asserts a threshold. `tests/test_benchmarks.py`
does assert a scaling ratio, which is the durable check; this exists to
show the numbers behind it. CI runs ``--quick`` to prove the benchmark
still executes against the current API.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pain001_loader_mt101 import parse_mt101  # noqa: E402

#: Sequence A: the message-level header, present once.
SEQUENCE_A = (
    ":20:MSGREF001\n"
    ":30:260712\n"
    ":50K:/DE89370400440532013000\n"
    "JOHN DOE\n"
    "123 MAIN STREET\n"
    "BERLIN\n"
    ":52A:DEUTDEFF\n"
)


def build(transactions: int) -> str:
    """An MT101 carrying ``transactions`` sequence-B instructions.

    References are distinct per instruction so nothing can be collapsed
    by a cache keyed on the reference, which would measure the cache
    rather than the parser.
    """
    blocks = "".join(
        f":21:TXN-{i:06d}\n"
        ":32B:EUR12345,67\n"
        ":57A:CHASUS33\n"
        ":59:/GB29NWBK60161331926819\n"
        "ACME TRADING LTD\n"
        "1 CORPORATE AVENUE\n"
        "LONDON\n"
        f":70:INVOICE {i:06d}\n"
        ":71A:SHA\n"
        for i in range(transactions)
    )
    return SEQUENCE_A + blocks


def _best(call, repeats: int) -> float:
    """Best-of timing after one untimed warm-up.

    The minimum is the least noisy estimator available; the mean follows
    whatever else the machine is doing.
    """
    call()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    return min(samples)


def run(quick: bool) -> dict:
    """Measure parse cost across batch sizes."""
    sizes = [10, 100] if quick else [10, 100, 1_000, 5_000]
    repeats = 2 if quick else 5
    rows, points = [], []
    for count in sizes:
        text = build(count)
        records = len(parse_mt101(text))
        seconds = _best(lambda t=text: parse_mt101(t), repeats)
        points.append((count, seconds))
        rows.append(
            {
                "transactions": count,
                "ms": seconds * 1e3,
                "us_per_txn": seconds * 1e6 / count,
                "records": records,
                "bytes": len(text),
            }
        )
    (n0, t0), (n1, t1) = points[0], points[-1]
    exponent = (
        math.log(t1 / t0) / math.log(n1 / n0)
        if n0 != n1 and t0 > 0 and t1 > 0
        else None
    )
    return {"rows": rows, "exponent": exponent}


def render(results: dict) -> None:
    """Print the table and the verdict."""
    print(f"  {'txns':>7}{'ms':>10}{'us/txn':>10}{'records':>10}{'bytes':>11}")
    for row in results["rows"]:
        print(
            f"  {row['transactions']:>7}{row['ms']:>10.2f}"
            f"{row['us_per_txn']:>10.2f}{row['records']:>10}"
            f"{row['bytes']:>11,}"
        )

    mismatched = [r for r in results["rows"] if r["records"] != r["transactions"]]
    if mismatched:
        print(
            "\n  WARNING: the record count does not match the instruction "
            "count. Instructions are\n  being dropped, and every us/txn "
            "figure above is divided by work never done."
        )
    else:
        print(
            "\n  Record count tracks the instruction count, so every "
            "instruction is being parsed\n  and us/txn means what it says."
        )

    exponent = results["exponent"]
    if exponent is not None:
        if exponent <= 1.25:
            verdict = "linear, as it should be"
        elif exponent < 1.75:
            verdict = "superlinear -- something is rescanning"
        else:
            verdict = "quadratic -- a lookup is rescanning what is parsed"
        print(f"  growth exponent {exponent:.2f} -- {verdict}.")


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--quick", action="store_true", help="small sizes, as CI runs")
    args = parser.parse_args()

    results = run(quick=args.quick)
    if args.json:
        json.dump(results, sys.stdout, indent=1)
        print()
    else:
        render(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
