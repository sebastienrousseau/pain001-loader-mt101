# pain001-loader-mt101 Roadmap

The loader ships with the pain001 suite, at the suite's version. Items
here are candidates; a release ships when the gates pass, not on a
calendar, and the maintainer decides what opens.

## Shipped

- `parse_mt101(text)`: the mandatory and common-denominator MT101 grammar
  to `pain.001.001.09` records, one per Sequence B transaction, with
  Sequence B overriding Sequence A and strict errors on malformed input.
- The same capability for AI agents as the `convert_mt101` tool in
  [`pain001-mcp`](https://github.com/sebastienrousseau/pain001-mcp).
- 100% line and branch coverage, docstring gate, benchmarks, examples run
  by the tests; CodeQL, Dependabot, DCO and Scorecard; releases attested,
  signed and shipped with SBOMs.
- Mutation testing (mutmut 3) of the parser on every pull request into
  `main`, every push to `main` and weekly
  (`.github/workflows/mutation.yml`); the build fails when the share of
  reached mutants the tests kill drops below 88%
  (`scripts/mutation_gate.py`).

## Candidates

- **Documented handling for the out-of-scope tags** (`:23E:` instruction
  codes, `:33B:`/`:36:` FX, `:56a:` intermediary): expose them on the
  record under clearly named keys so a caller can decide, rather than
  dropping them silently. Needs a decision on the core's vocabulary first.
- **A corpus scenario sourced from an MT101 message**, so the site's
  example corpus shows the conversion end to end with provenance.

## Out of scope

- Generating or validating XML: the core does both.
- MT103 and other MT categories: separate loaders.
