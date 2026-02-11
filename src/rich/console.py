"""Minimal Console shim."""

from __future__ import annotations


class Console:
    def print(self, obj: object) -> None:
        print(obj)
