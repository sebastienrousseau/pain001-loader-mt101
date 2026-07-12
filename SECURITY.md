<!-- SPDX-License-Identifier: Apache-2.0 -->

# Security Policy

## Supported versions

This package follows the [`pain001`](https://github.com/sebastienrousseau/pain001)
suite cadence. While pre-`1.0`, the latest released `0.0.x` receives
security fixes; older `0.0.x` versions do not.

| Version | Status | Receives security fixes? |
| :--- | :--- | :--- |
| `0.0.1` (latest) | Current | ✅ Yes |

## Reporting a vulnerability

**Do not open a public issue for security reports.** Use GitHub
Private Vulnerability Reporting:
<https://github.com/sebastienrousseau/pain001-loader-mt101/security/advisories/new>

**Acknowledgement**: within 48 hours. **Triage**: within 7 days.

## Security posture

### Scope

This package exposes one function, `parse_mt101(text)`, that converts
a SWIFT MT101 text payload into pain.001 flat records. It does **not**
parse XML, write files, or make network calls. Untrusted input is
regex-bounded to a small set of expected MT101 field shapes; anything
outside that grammar is rejected with a `ValueError` or omitted.

### Threat model

| Surface | How it's handled |
| :--- | :--- |
| **XML / XXE / billion-laughs** | Out of scope. MT101 is a flat text format with no XML envelope. |
| **Catastrophic regex backtracking** | Field regexes are anchored (`^`, `$`) with bounded quantifiers (`\d{6}`, `[A-Z]{3}`). No nested unbounded groups. |
| **Path traversal** | The loader never touches the filesystem. Callers pass strings, not paths. |
| **Resource exhaustion** | Parsing is O(input size). Impose an upstream byte cap for hostile input. |
| **Dependency CVEs** | `pain001 >= 0.0.53, < 1` is the only runtime dependency. |

### Cryptography status

This package implements **no** cryptographic functionality. MT101
payloads sometimes arrive in PGP envelopes; decrypt upstream before
passing plaintext to this loader.
