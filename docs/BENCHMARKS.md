<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Benchmarks

MT101 is a *request for transfer*, and unlike MT103 it genuinely
batches: sequence B repeats once per credit-transfer instruction, and
the loader returns one flat `pain.001` record per instruction. So there
is a real scaling axis here, and it is the one a corporate treasury
moves along — a payroll run or a supplier batch is hundreds or thousands
of instructions in a single message.

```sh
python benches/bench_parse_mt101.py           # full run
python benches/bench_parse_mt101.py --quick   # what CI runs
python benches/bench_parse_mt101.py --json    # machine-readable
```

## Measured

One run of `python benches/bench_parse_mt101.py` on 2026-10-21: Apple A18
Pro, CPython 3.12.15, on a shared machine under load (load average about
35), so the absolute numbers are noisy and slower than an idle machine
gives. The shape is the result.

| txns | ms | µs/txn | records | bytes |
| ---: | ---: | ---: | ---: | ---: |
| 10 | 0.20 | 20.19 | 10 | 1,550 |
| 100 | 1.51 | 15.08 | 100 | 14,600 |
| 1,000 | 14.61 | 14.61 | 1,000 | 145,100 |
| 5,000 | 89.34 | 17.87 | 5,000 | 725,100 |

**Growth exponent 1.06: linear.**

A parser that has gone quadratic — because some lookup rescans the
instructions already parsed — looks perfectly healthy on a fixture of ten
and falls over on payroll day. The exponent is what catches that.

## Why the record count is printed

A loader that silently stopped after the first instruction would show a
*falling* µs/txn as the input grew, which reads as batching and is the
opposite: dividing by instructions never parsed. Watching the record
count track the instruction count is what rules that out.

This is not hypothetical. The sibling `pacs008-loader-mt103` behaves
exactly that way, because an MT103 carries exactly one transfer — and the
two loaders are easy to assume are alike.

## Not a gate

`tests/test_benchmarks.py` asserts a scaling ratio and is the durable
check. This benchmark exists to show the numbers behind it. CI runs
`--quick` so a benchmark that has stopped compiling against the current
API fails the build rather than rotting into a file that reads as
verified and is not.
