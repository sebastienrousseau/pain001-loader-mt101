<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Contributing

Thanks for looking. This package is small on purpose: it turns an MT101
input into the flat `pain.001` records the rest of the `pain001` suite
already understands, and nothing else.

[DEVELOPMENT.md](DEVELOPMENT.md) has the mechanics: toolchain, every CI
gate and its local command, the test layout and the release model. This
file is the etiquette.

## Before you open a pull request

```sh
make install   # .venv from the hash-pinned requirements
make check     # lint, strict mypy, complexity, versions, tests, docstrings, examples
```

`make check` fails below **100% line and branch coverage** of the package
and `scripts/`. That is not a stretch goal here: the package is a few
hundred lines, and the branches that go untested are the malformed-input
ones, which is exactly where a parser earns its keep.

- Open the pull request against `main`. The maintainer folds accepted
  changes into the active `feat/v<next-version>` release branch, which
  is the only pull request merged into `main`.
- Add tests with the change, in the same commit. A fixed bug gets a
  regression test that fails without the fix.
- Add a line under `## [Unreleased]` in `CHANGELOG.md` for anything a
  user would notice.
- Use synthetic data only: no real account numbers or personal data.
  Sample IBANs pass mod-97 and BICs are structurally valid.

## Commits

- Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`),
  imperative subject, a body that explains why.
- Every commit carries a `Signed-off-by:` trailer (`git commit -s`), the
  [Developer Certificate of Origin](DCO.txt); `dco.yml` checks it.

## Shared files

`tests/test_suite_conformance.py` is shared across the pain001 suite.
**Do not edit it here.** It is copied from one canonical file, and a local
edit fails `test_this_file_is_the_canonical_copy` by design: no repository
can quietly weaken a shared gate. `scripts/release_notes.py` and its test
are vendored from the core in the same way.

## Benchmarks

`benches/` measures throughput as a message grows. It asserts nothing,
because wall-clock numbers are not comparable between machines, but CI
runs it with `--quick` so a benchmark that no longer runs against the
current API fails the build rather than rotting unnoticed.

Read the per-transaction column. Flat across sizes means linear. A number
that climbs with size means the parser has gone superlinear, which no
unit test will tell you and a month-end batch will.

## Versioning

The version moves in `0.0.1` steps, in lockstep with the pain001 suite,
and only when the maintainer opens a release. Do not bump it in a
feature change. `0.1.0` follows `0.0.999`, not `0.0.9`.

## Licence

Apache-2.0 OR MIT, at your option. By contributing you agree your work is
released under the same dual grant.
