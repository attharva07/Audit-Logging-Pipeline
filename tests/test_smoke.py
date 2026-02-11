"""Smoke tests for initial package scaffold."""

import auditlog


def test_package_imports() -> None:
    assert auditlog is not None
