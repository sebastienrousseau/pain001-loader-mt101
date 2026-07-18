<!-- SPDX-License-Identifier: Apache-2.0 -->

# Getting support

Thanks for using `pain001-loader-mt101`. Here's the fastest way to get
help, by need.

## Read first

- **[README.md](README.md)** — install, quick start, the full MT101 →
  pain.001 field-mapping table, assumptions and out-of-scope fields.
- **[`examples/`](examples/)** — two runnable scripts exercised in CI.

## Questions & how-to

Open a [GitHub Discussion](https://github.com/sebastienrousseau/pain001-loader-mt101/discussions)
with:

- Python version + OS
- `pain001-loader-mt101` version + `pain001` version
- A minimal MT101 payload that reproduces the issue (sensitive values
  redacted)
- The full error output

## Bugs

Open an [issue](https://github.com/sebastienrousseau/pain001-loader-mt101/issues/new)
with the same triage data plus expected vs. actual behaviour.

## Feature requests

Likely categories, all out of scope for v0.0.2:

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
| 0.0.2 (latest) | ✅ |

Requires Python 3.10+ and `pain001 >= 0.0.55`.
