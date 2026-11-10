<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Getting support

Thanks for using `pain001-loader-mt101`. Here's the fastest way to get
help, by need.

## Read first

- **[README.md](README.md)**: install, quick start, the full MT101 to
  pain.001 field-mapping table, assumptions and out-of-scope fields.
- **[`examples/`](examples/)**: two runnable scripts exercised in CI.
- **[DEVELOPMENT.md](DEVELOPMENT.md)**: building, testing and every CI
  gate, run locally.

## Questions & how-to

Open a [GitHub issue](https://github.com/sebastienrousseau/pain001-loader-mt101/issues/new) (the pain001 suite does not
use GitHub Discussions) with:

- Python version + OS
- `pain001-loader-mt101` version + `pain001` version
- A minimal MT101 payload that reproduces the issue (sensitive values
  redacted)
- The full error output

## Bugs

Open an [issue](https://github.com/sebastienrousseau/pain001-loader-mt101/issues/new)
with the same triage data plus expected vs. actual behaviour.

## Feature requests

Candidates that are not implemented:

- **FX legs** (`:33B:` instructed amount, `:36:` exchange rate, `:21F:`
  FX deal reference).
- **Instruction / regulatory fields** (`:23E:`, `:77B:`, `:25A:`).
- **Intermediary / sending institutions** (`:56a:`, `:51A:`).
- **Application-header agent fallback** (blocks 1/2 Sender / Receiver
  BIC when `:52a:` / `:57a:` are absent).

## Security

**Do not** open public issues for vulnerabilities. Follow the private
disclosure process in [SECURITY.md](SECURITY.md).

## Supported versions

| Version | Supported? |
| :--- | :--- |
| 0.0.85 (latest) | ✅ |

Requires Python 3.11+ and `pain001 >= 0.0.85`.
