<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Policies

## Toolchain policy

Python 3.10 is the floor (`requires-python = ">=3.10"` in `pyproject.toml`),
with Linux CI on 3.10, 3.11, 3.12, 3.13 and 3.14. The floor matches the
`pain001` core library, which this package depends on; it moves when the
core's does, in the same family release, and the change is recorded in the
changelog. No distro-system Python is supported.

## Dependency policy

`pain001` is the only runtime dependency. Its floor is the family's
release version, capped below `1`, so a release never resolves an older
core and the older advisory floors it declares. CI installs every tool
from hash-pinned `requirements/*.txt`, compiled from the `.in` files
beside them with `make pip-compile`, and audits each of them with
`pip-audit` on every pull request. A dependency with a published advisory
is constrained so no affected version can resolve.

## Versioning policy

The package follows the pain001 suite: the members release together at
one version, core first, in `0.0.1` steps. `scripts/verify_versions.py`
checks every place the version is restated, and the scheduled Suite
Consistency workflow compares the tree and the published suite with PyPI.
