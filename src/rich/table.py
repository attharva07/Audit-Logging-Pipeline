"""Minimal Table shim."""

from __future__ import annotations


class Table:
    def __init__(self, title: str = "") -> None:
        self.title = title
        self.columns: list[str] = []
        self.rows: list[list[str]] = []

    def add_column(self, name: str, justify: str | None = None) -> None:
        self.columns.append(name)

    def add_row(self, *vals: str) -> None:
        self.rows.append(list(vals))

    def __str__(self) -> str:
        lines: list[str] = []
        if self.title:
            lines.append(self.title)
        if self.columns:
            lines.append(" | ".join(self.columns))
            lines.append("-" * max(3, len(lines[-1])))
        for row in self.rows:
            lines.append(" | ".join(row))
        return "\n".join(lines)
