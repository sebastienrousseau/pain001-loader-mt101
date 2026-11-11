# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Every relative link in the repository's Markdown resolves.

The manual is built from these files and GitHub renders them as they
are, so a moved or renamed file breaks a link in both places at once.
This checks links to files in the tree and ``#anchor`` links to headings
in the same file. External URLs are not fetched: a network check would
fail on someone else's outage, not on a change here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "node_modules", "_build", "mutants", ".pytest_cache"}

_INLINE = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_REFERENCE = re.compile(r"^\[[^\]]+\]:\s+(\S+)", re.MULTILINE)
_HTML = re.compile(r"""(?:src|href)="([^"]+)\"""")
_FENCE = re.compile(r"^(```|~~~).*?^\1", re.MULTILINE | re.DOTALL)
_HEADING = re.compile(r"^#{1,6} (.+)$", re.MULTILINE)


def _markdown() -> list[Path]:
    return sorted(
        p
        for p in ROOT.rglob("*.md")
        if not SKIP_DIRS.intersection(p.relative_to(ROOT).parts)
    )


def _slug(heading: str) -> str:
    """GitHub's anchor for a heading."""
    text = re.sub(r"[`*_]|<[^>]+>", "", heading).strip().lower()
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def _targets(text: str) -> list[str]:
    prose = _FENCE.sub("", text)
    found = _INLINE.findall(prose) + _REFERENCE.findall(prose) + _HTML.findall(prose)
    return [t for t in found if not re.match(r"^[a-z][a-z0-9+.-]*:", t)]


def broken_links(path: Path) -> list[str]:
    """The relative links in ``path`` that point at nothing."""
    text = path.read_text(encoding="utf-8")
    anchors = {_slug(h) for h in _HEADING.findall(_FENCE.sub("", text))}
    broken = []
    for target in _targets(text):
        file_part, _, anchor = target.partition("#")
        if not file_part:
            if anchor not in anchors:
                broken.append(target)
        elif not (path.parent / file_part).exists():
            broken.append(target)
    return broken


@pytest.mark.parametrize(
    "path", _markdown(), ids=lambda p: p.relative_to(ROOT).as_posix()
)
def test_every_relative_link_resolves(path: Path) -> None:
    assert broken_links(path) == []


def test_a_broken_file_link_and_a_broken_anchor_are_caught(tmp_path: Path) -> None:
    page = tmp_path / "page.md"
    (tmp_path / "there.md").write_text("# There\n", encoding="utf-8")
    page.write_text(
        "# Title\n\n## Next steps\n\n"
        "[ok](there.md) [ok](#next-steps) [ok](https://example.com/x)\n"
        "[gone](missing.md) [gone](#nowhere)\n\n"
        '<img src="also-missing.gif" />\n\n'
        "```md\n[ignored](in-a-fence.md)\n```\n\n"
        "[ref]: missing-ref.md\n",
        encoding="utf-8",
    )
    assert broken_links(page) == [
        "missing.md",
        "#nowhere",
        "missing-ref.md",
        "also-missing.gif",
    ]
