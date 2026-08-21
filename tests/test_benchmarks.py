"""Performance benchmarks for the MT101 parser.

There are two different things here, and they guard different failures.

``test_parse_1000_transactions`` is the measurement: it records what
parsing a realistic multi-transaction message costs, so the number shows
up in the benchmark artifact and can be compared release over release.

``test_parsing_scales_linearly`` is the guard. An absolute wall-clock
threshold on a shared CI runner is a bad regression check -- it has to
be set loose enough to survive a noisy neighbour, and by then it only
catches catastrophes. Comparing the parser against *itself* at two sizes
is machine-independent: a runner that is twice as slow scales both
measurements equally, and the ratio does not move.

The failure this is really aimed at is an accidental quadratic --
something like a per-transaction scan over all previously seen fields,
which is easy to introduce in a parser that looks values up by tag and
invisible on the small fixtures the unit tests use.

Measured on this machine, parsing is linear: doubling the transaction
count costs 2.00x and 1.86x across 1000 -> 2000 -> 4000. So the 4x-size
ratio sits near 4; the threshold below is 8, which leaves room for noise
while still failing loudly on anything quadratic (which would be ~16).
"""

from __future__ import annotations

import time

import pytest

from pain001_loader_mt101 import parse_mt101

SEQUENCE_A = (
    ":20:MSGREF001\n"
    ":30:260712\n"
    ":50K:/DE89370400440532013000\n"
    "JOHN DOE\n"
    "123 MAIN STREET\n"
    "BERLIN\n"
    ":52A:DEUTDEFF\n"
)

#: Ratio ceiling for a 4x increase in transaction count. Linear is ~4,
#: quadratic is ~16.
MAX_SCALING_RATIO = 8.0


def build_message(transactions: int) -> str:
    """Build an MT101 with ``transactions`` sequence-B blocks."""
    blocks = "".join(
        f":21:TXN-{i:06d}\n"
        f":32B:EUR12345,67\n"
        f":57A:CHASUS33\n"
        f":59:/GB29NWBK60161331926819\n"
        "ACME TRADING LTD\n"
        "1 CORPORATE AVENUE\n"
        "LONDON\n"
        f":70:INVOICE {i:06d}\n"
        ":71A:SHA\n"
        for i in range(transactions)
    )
    return SEQUENCE_A + blocks


def _best_of(text: str, rounds: int = 5) -> float:
    """Fastest parse of ``text`` in seconds.

    The minimum rather than the mean: it is the measurement least
    disturbed by an unrelated process getting the CPU.
    """
    parse_mt101(text)  # warm any lazily-built state
    timings = []
    for _ in range(rounds):
        started = time.perf_counter()
        parse_mt101(text)
        timings.append(time.perf_counter() - started)
    return min(timings)


@pytest.mark.benchmark
def test_parse_1000_transactions(benchmark) -> None:
    """Benchmark a 1000-transaction message end to end."""
    text = build_message(1000)
    rows = benchmark(parse_mt101, text)
    # A benchmark that silently parsed nothing would still look fast.
    assert len(rows) == 1000
    assert rows[0]["payment_id"] == "TXN-000000"
    assert rows[-1]["payment_id"] == "TXN-000999"


@pytest.mark.benchmark
def test_parsing_scales_linearly() -> None:
    """Parsing 4x the transactions must not cost ~16x the time."""
    small = _best_of(build_message(1000))
    large = _best_of(build_message(4000))

    ratio = large / small
    assert ratio < MAX_SCALING_RATIO, (
        f"parsing 4000 transactions took {ratio:.1f}x parsing 1000 "
        f"({large * 1000:.1f}ms vs {small * 1000:.1f}ms); linear is ~4x "
        f"and quadratic is ~16x, so this looks like the parser gained a "
        f"per-transaction scan over previously parsed fields"
    )


#: Ceiling on the cost of the wire format relative to a bare field list,
#: and of a field-rich transaction relative to a minimal one. Both
#: measured at 1.10x.
MAX_SHAPE_OVERHEAD = 3.0

BLOCK4_HEADER = "{1:F01BANKDEFFAXXX0000000000}{2:I101BANKDEFFXXXXN}{4:\n"
BLOCK4_TRAILER = "\n-}"


def wrap_block4(body: str) -> str:
    """Wrap a bare field list in the SWIFT block structure."""
    return BLOCK4_HEADER + body + BLOCK4_TRAILER


def build_rich_message(transactions: int) -> str:
    """Build an MT101 whose transactions carry every optional field."""
    blocks = "".join(
        f":21:TXN-{i:06d}\n"
        f":32B:EUR12345,67\n"
        f":57A:CHASUS33\n"
        f":59:/GB29NWBK60161331926819\n"
        "ACME TRADING LTD\n"
        "1 CORPORATE AVENUE\n"
        "LONDON\n"
        "EC1A 1BB\n"
        f":70:INVOICE {i} LONG REMITTANCE INFORMATION LINE\n"
        ":71A:SHA\n"
        ":36:1,0\n"
        for i in range(transactions)
    )
    return SEQUENCE_A + blocks


class TestMessageShapes:
    """Shapes the flat-list benchmark does not cover.

    ``test_parse_1000_transactions`` measures a bare field list with a
    uniform transaction. Two other shapes are what real traffic looks
    like, and both exercise code the flat case never reaches.
    """

    @pytest.mark.benchmark
    def test_parse_block4_wire_format(self, benchmark) -> None:
        """Benchmark the wrapped form banks actually send.

        A bare field list is the convenient shape for a fixture; the
        wire carries it inside ``{1:...}{2:...}{4: ... -}``, which means
        ``_unwrap_block4`` runs. Nothing benchmarked that path before.
        """
        text = wrap_block4(build_message(1000))

        rows = benchmark(parse_mt101, text)

        assert len(rows) == 1000
        assert rows[0]["payment_id"] == "TXN-000000"

    @pytest.mark.benchmark
    def test_the_wire_format_is_not_expensive_to_unwrap(self) -> None:
        """Unwrapping must cost about nothing.

        Measured at 1.10x a bare list. The failure this guards is
        unwrapping doing work proportional to the message more than
        once -- a scan per field rather than a scan per message.
        """
        flat = build_message(500)
        wrapped = wrap_block4(flat)

        ratio = _best_of(wrapped) / _best_of(flat)
        assert ratio < MAX_SHAPE_OVERHEAD, (
            f"the block-4 wire format cost {ratio:.1f}x a bare field list; "
            f"unwrapping should be a single scan"
        )

    @pytest.mark.benchmark
    def test_optional_fields_do_not_cost_disproportionately(self) -> None:
        """Field-rich transactions must not scale badly in field count.

        ``_lookup`` searches tag by tag, so the risk is it becoming
        quadratic in the number of fields present. Measured, a
        transaction carrying every optional field costs 1.10x a minimal
        one.
        """
        lean = build_message(500)
        rich = build_rich_message(500)

        ratio = _best_of(rich) / _best_of(lean)
        assert ratio < MAX_SHAPE_OVERHEAD, (
            f"transactions with every optional field cost {ratio:.1f}x "
            f"minimal ones; this suggests per-field work that rescans "
            f"the transaction"
        )
