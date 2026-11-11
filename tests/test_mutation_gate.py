# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The mutation gate fails below its floor and never passes on no data.

``scripts/mutation_gate.py`` is the last step of the mutation workflow; a
gate that passed without stats, or rounded a low score up, would let the
weekly run go green while the tests stopped catching wrong records.
"""

from __future__ import annotations

import importlib.util
import json
import runpy
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "mutation_gate.py"


@pytest.fixture
def gate() -> ModuleType:
    """The script as a module."""
    spec = importlib.util.spec_from_file_location("mutation_gate", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _stats(tmp_path: Path, **counts: int) -> str:
    path = tmp_path / "stats.json"
    path.write_text(json.dumps(counts), encoding="utf-8")
    return str(path)


def test_the_score_counts_only_checked_mutants(gate: ModuleType) -> None:
    stats = {"killed": 9, "survived": 1, "no_tests": 50, "timeout": 3}
    assert gate.score(stats) == (90.0, 9, 10)


def test_no_checked_mutants_scores_zero(gate: ModuleType) -> None:
    assert gate.score({}) == (0.0, 0, 0)


def test_a_score_at_the_floor_passes(
    gate: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stats = _stats(tmp_path, killed=88, survived=12, no_tests=2, timeout=1)
    assert gate.main(["--floor", "88", "--stats", stats]) == 0
    out = capsys.readouterr().out
    assert "mutation score 88.0% (88 of 100 checked mutants killed" in out
    assert "2 unreached, 1 timed out, floor 88%" in out


def test_a_score_below_the_floor_fails(gate: ModuleType, tmp_path: Path) -> None:
    stats = _stats(tmp_path, killed=87, survived=13)
    assert gate.main(["--floor", "88", "--stats", stats]) == 1


def test_missing_stats_fail(
    gate: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = str(tmp_path / "absent.json")
    assert gate.main(["--floor", "0", "--stats", missing]) == 1
    assert "run mutmut first" in capsys.readouterr().err


def test_the_script_runs_as_a_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stats = _stats(tmp_path, killed=1, survived=0)
    monkeypatch.setattr(
        sys, "argv", ["mutation_gate.py", "--floor", "1", "--stats", stats]
    )
    with pytest.raises(SystemExit) as stopped:
        runpy.run_path(str(SCRIPT), run_name="__main__")
    assert stopped.value.code == 0
