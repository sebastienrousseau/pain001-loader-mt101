<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# 0002. Strict errors over half-converted output

- **Status:** Accepted
- **Date:** 2026-09-18 (practised since the first release; written down today)
- **Deciders:** maintainer

## Context

Real MT101 traffic is uneven: missing `:20:` or `:30:`, a Sequence B
without `:21:` or `:32B:`, fields the loader does not map (`:23E:`,
`:33B:`, `:36:`, `:56a:`).

## Options considered

1. Best effort: convert what parses, skip the rest, warn. Produces a
   file for every input; produces a wrong file for some.
2. Strict: raise `ValueError` naming the missing or unsupported field;
   document the unmapped tags as out of scope.

## Decision

Option 2. A treasury system would rather stop than send a payment
batch with a silently dropped transaction; the unmapped tags need
human judgement the loader cannot supply.

## Consequences

Every error message names the tag and the sequence. The out-of-scope
list is documented in the README and the site's reference page, and
surfacing those tags under named keys is a roadmap candidate that
starts with the core's vocabulary, not here.
