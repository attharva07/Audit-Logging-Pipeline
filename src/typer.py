"""Minimal Typer-compatible shim for offline usage."""

from __future__ import annotations

import inspect
import sys
from dataclasses import dataclass
from typing import Any, Callable


class BadParameter(ValueError):
    """Raised when CLI parameter parsing/validation fails."""


class Exit(SystemExit):
    """Typer-compatible exit exception."""


@dataclass
class OptionInfo:
    default: Any
    flags: tuple[str, ...]
    help: str = ""
    min: int | None = None


def Option(default: Any = ..., *flags: str, help: str = "", min: int | None = None) -> OptionInfo:
    return OptionInfo(default=default, flags=flags, help=help, min=min)


class Typer:
    def __init__(self, *, help: str = "") -> None:
        self.help = help
        self._commands: dict[str, Callable[..., Any]] = {}
        self._callback: Callable[[], Any] | None = None

    def callback(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._callback = func
            return func

        return decorator

    def command(self, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._commands[name or func.__name__.replace("_", "-")] = func
            return func

        return decorator

    def _print_help(self) -> None:
        print(self.help or "CLI")
        print("\nCommands:")
        for cmd in sorted(self._commands):
            print(f"  {cmd}")
        print("\nOptions:")
        print("  -h, --help  Show this message and exit.")

    def _parse_args(self, func: Callable[..., Any], args: list[str]) -> dict[str, Any]:
        sig = inspect.signature(func)
        values: dict[str, Any] = {}
        by_flag: dict[str, tuple[str, OptionInfo, Any]] = {}

        for name, param in sig.parameters.items():
            default = param.default
            ann = param.annotation
            if isinstance(default, OptionInfo):
                opt = default
            else:
                opt = OptionInfo(default=default, flags=(f"--{name.replace('_', '-')}",))
            typ = ann if ann is not inspect._empty else str
            for flag in opt.flags:
                by_flag[flag] = (name, opt, typ)
            if opt.default is not ...:
                values[name] = opt.default

        i = 0
        while i < len(args):
            token = args[i]
            if token in ("-h", "--help"):
                raise Exit(0)
            if token not in by_flag:
                raise BadParameter(f"Unknown option: {token}")
            name, opt, typ = by_flag[token]
            i += 1
            if i >= len(args):
                raise BadParameter(f"Missing value for {token}")
            raw = args[i]
            if typ is int:
                val: Any = int(raw)
            else:
                val = raw
            if opt.min is not None and isinstance(val, int) and val < opt.min:
                raise BadParameter(f"{token} must be >= {opt.min}")
            values[name] = val
            i += 1

        for name, param in sig.parameters.items():
            default = param.default
            if isinstance(default, OptionInfo) and default.default is ... and name not in values:
                flag = default.flags[0] if default.flags else f"--{name}"
                raise BadParameter(f"Missing required option {flag}")

        return values

    def __call__(self) -> None:
        args = sys.argv[1:]
        if not args or args[0] in ("-h", "--help"):
            self._print_help()
            return

        cmd_name = args[0]
        cmd = self._commands.get(cmd_name)
        if cmd is None:
            print(f"Unknown command: {cmd_name}")
            self._print_help()
            raise SystemExit(1)

        try:
            kwargs = self._parse_args(cmd, args[1:])
            cmd(**kwargs)
        except BadParameter as exc:
            print(f"Error: {exc}")
            raise SystemExit(2) from exc
        except Exit as exc:
            raise SystemExit(exc.code) from exc
