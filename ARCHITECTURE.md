<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# pain001-loader-mt101 Architecture

A map of the codebase for new contributors and maintainers.

## The pipeline

```
SWIFT MT101 text (with or without the {4:...-} block-4 envelope)
        |
        v
pain001_loader_mt101.parse_mt101(text)        one dict per Sequence B transaction
        |  keys are the pain001 flat-record vocabulary
        v
pain001  (SchemaValidator, scheme rulebooks, official XSD, XML generation)
        |
        v
ISO 20022 pain.001 XML
```

The loader does one thing: it parses the mandatory and common-denominator
MT101 grammar and returns flat records whose keys are exactly the ones
`pain001` validates against the `pain.001.001.09` JSON Schema. It does not
generate XML and it does not validate; the core does both, so a converted
message goes through the same three checks as any other input.

## Module map

| Area | Module | Responsibility |
| :--- | :--- | :--- |
| **Public API** | `pain001_loader_mt101/__init__.py` | Exports `parse_mt101` and `__version__` |
| **Parser** | `pain001_loader_mt101/loader.py` | Block-4 unwrapping, field iteration, Sequence A/B splitting, party and amount parsing, record assembly |
| **Tests** | `tests/` | Grammar, field mapping, strictness, examples run end to end, the suite conformance file |
| **Examples** | `examples/` | Runnable scripts, executed by the tests |
| **Benchmarks** | `benches/` | Parse throughput and its scaling |
| **Suite** | `scripts/check_suite_consistency.py`, `tests/test_suite_conformance.py` | The shared checks every suite member carries |

## Key design decisions

- **Records, not XML.** Conversion without validation is how malformed
  files reach banks. The loader hands records to the core and the core
  proves them clean.
- **Strict where it counts.** Malformed input raises `ValueError` with a
  precise message rather than emitting a half-converted batch: a missing
  `:20:` or `:30:`, no Sequence B, a transaction without `:21:` or `:32B:`.
- **Sequence B overrides Sequence A,** as the standard says; party tags set
  per transaction win over the message-level defaults.
- **Deliberately out of scope:** instruction codes, FX and intermediary
  routing (`:23E:`, `:33B:`, `:36:`, `:56a:` and the rest). They need human
  judgement, and the loader says so instead of guessing.
- **Zero third-party dependencies** beyond `pain001` itself.

## Extension points

- **A new tag:** add its parser in `loader.py`, map it to a record key from
  the core's vocabulary, and add a fixture message plus a test that the
  records still pass `SchemaValidator("pain.001.001.09")`.
- **A new message edition:** the record keys are edition-independent; the
  edition is chosen at generation time in the core.

## Where to look first

- Runnable examples: [`examples/`](examples/)
- Roadmap: [`ROADMAP.md`](ROADMAP.md)
- Release process: [`RELEASING.md`](RELEASING.md)
- Parent library: [`pain001`](https://github.com/sebastienrousseau/pain001)
