<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# 0001. Records, not XML

- **Status:** Accepted
- **Date:** 2026-09-18 (practised since the first release; written down today)
- **Deciders:** maintainer

## Context

`parse_mt101` could have written `pain.001` XML directly, which is what
most MT-to-MX converters do. It returns flat records instead and leaves
generation and validation to the core.

## Options considered

1. Emit XML from the loader. One package does everything; but the
   mapping and the output both have to be trusted, and every fix to
   the core's XML would need a matching fix here.
2. Emit the core's flat records. The core proves them through its
   JSON Schema, the rail rulebook and the official XSD, the same three
   checks every other input gets; the loader is only a mapping.

## Decision

Option 2. Conversion without validation is how malformed files reach
banks; a loader that only maps keeps the proof where it already
exists.

## Consequences

The loader has no XML code and no schema of its own; its correctness
test is that a realistic multi-transaction message maps to records
that pass `SchemaValidator("pain.001.001.09")` with zero errors. A new
message edition needs no change here.
