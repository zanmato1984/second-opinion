from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable, List, Optional, Tuple


_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@dataclass
class DiffLine:
    kind: str  # 'context', 'add', 'del'
    text: str
    old_line: Optional[int]
    new_line: Optional[int]


@dataclass
class Hunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[DiffLine] = field(default_factory=list)


@dataclass
class FileDiff:
    path: str
    hunks: List[Hunk] = field(default_factory=list)

    def added_lines(self) -> List[Tuple[int, str]]:
        lines: List[Tuple[int, str]] = []
        for hunk in self.hunks:
            for line in hunk.lines:
                if line.kind == "add" and line.new_line is not None:
                    lines.append((line.new_line, line.text))
        return lines


@dataclass
class Diff:
    files: List[FileDiff] = field(default_factory=list)

    def file_paths(self) -> List[str]:
        return [file.path for file in self.files]


class DiffParseError(RuntimeError):
    pass


def parse_unified_diff(text: str) -> Diff:
    files: List[FileDiff] = []
    current_file: Optional[FileDiff] = None
    current_hunk: Optional[Hunk] = None
    old_line = new_line = None

    def finalize_hunk() -> None:
        nonlocal current_hunk, current_file
        if current_hunk and current_file:
            current_file.hunks.append(current_hunk)
        current_hunk = None

    def finalize_file() -> None:
        nonlocal current_file
        if current_file:
            files.append(current_file)
        current_file = None

    for raw_line in text.splitlines():
        if raw_line.startswith("diff --git "):
            finalize_hunk()
            finalize_file()
            continue
        if raw_line.startswith("--- "):
            continue
        if raw_line.startswith("+++ "):
            path = raw_line[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            current_file = FileDiff(path=path)
            continue
        if raw_line.startswith("@@ "):
            match = _HUNK_RE.match(raw_line)
            if not match:
                raise DiffParseError(f"Invalid hunk header: {raw_line}")
            finalize_hunk()
            old_start = int(match.group(1))
            old_count = int(match.group(2) or "1")
            new_start = int(match.group(3))
            new_count = int(match.group(4) or "1")
            current_hunk = Hunk(
                old_start=old_start,
                old_count=old_count,
                new_start=new_start,
                new_count=new_count,
            )
            old_line = old_start
            new_line = new_start
            continue
        if current_hunk is None:
            continue
        if raw_line.startswith("+" ) and not raw_line.startswith("+++"):
            current_hunk.lines.append(
                DiffLine(kind="add", text=raw_line[1:], old_line=None, new_line=new_line)
            )
            new_line = new_line + 1 if new_line is not None else None
            continue
        if raw_line.startswith("-") and not raw_line.startswith("---"):
            current_hunk.lines.append(
                DiffLine(kind="del", text=raw_line[1:], old_line=old_line, new_line=None)
            )
            old_line = old_line + 1 if old_line is not None else None
            continue
        if raw_line.startswith("\\"):
            continue
        if raw_line.startswith(" "):
            current_hunk.lines.append(
                DiffLine(kind="context", text=raw_line[1:], old_line=old_line, new_line=new_line)
            )
            old_line = old_line + 1 if old_line is not None else None
            new_line = new_line + 1 if new_line is not None else None
            continue

    finalize_hunk()
    finalize_file()

    return Diff(files=files)
