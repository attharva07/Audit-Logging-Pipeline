"""Minimal local Typer-compatible shim for offline scaffold usage."""

from __future__ import annotations

import sys
from typing import Callable


class Typer:
    def __init__(self, *, help: str = "") -> None:
        self.help = help
        self._callback: Callable[[], None] | None = None

    def callback(self) -> Callable[[Callable[[], None]], Callable[[], None]]:
        def decorator(func: Callable[[], None]) -> Callable[[], None]:
            self._callback = func
            return func

        return decorator

    def __call__(self) -> None:
        args = sys.argv[1:]
        if "--help" in args or "-h" in args:
            print(self.help or "CLI")
            print("\nOptions:")
            print("  -h, --help  Show this message and exit.")
            return
        if self._callback is not None:
            self._callback()
