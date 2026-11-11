# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Every example runs to completion and prints what the README says it does.

The examples are the second thing a reader copies after the Quick Start.
Running them here, on every leg of the test matrix, keeps them working
against the current parser and the current pain001 core.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"

EXPECTED = {
    "01_minimal_parse.py": "2 transaction(s) parsed",
    "02_validate_against_pain001.py": "All records are schema-valid pain.001.001.09.",
}


def test_every_example_is_listed() -> None:
    assert sorted(p.name for p in EXAMPLES.glob("*.py")) == sorted(EXPECTED)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_the_example_runs(name: str) -> None:
    done = subprocess.run(
        [sys.executable, str(EXAMPLES / name)],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert done.returncode == 0, done.stderr
    assert EXPECTED[name] in done.stdout
