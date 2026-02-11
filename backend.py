"""Minimal PEP 517 backend for offline scaffold builds."""

from __future__ import annotations

import base64
import csv
import hashlib
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

NAME = "auditlog"
VERSION = "0.1.0"
DIST = "auditlog"
TAG = "py3-none-any"


def _metadata_text() -> str:
    return "\n".join(
        [
            "Metadata-Version: 2.1",
            f"Name: {NAME}",
            f"Version: {VERSION}",
            "Summary: Standalone audit logging pipeline scaffold",
            "Requires-Python: >=3.10",
            "",
        ]
    )


def _wheel_name() -> str:
    return f"{DIST}-{VERSION}-{TAG}.whl"


def _dist_info_dir() -> str:
    return f"{DIST}-{VERSION}.dist-info"


def _entry_points_text() -> str:
    return "[console_scripts]\nauditlog = auditlog.cli:app\n"


def _iter_source_files() -> list[tuple[Path, str]]:
    src = Path("src")
    files: list[tuple[Path, str]] = []
    for path in src.rglob("*"):
        if path.is_file():
            rel = path.relative_to(src).as_posix()
            files.append((path, rel))
    return files


def _hash_bytes(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    return "sha256=" + base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _build_wheel_file(wheel_directory: str, metadata_directory: str | None = None) -> str:
    os.makedirs(wheel_directory, exist_ok=True)
    wheel_name = _wheel_name()
    wheel_path = Path(wheel_directory) / wheel_name
    dist_info = _dist_info_dir()

    rows: list[list[str]] = []
    with ZipFile(wheel_path, "w", compression=ZIP_DEFLATED) as zf:
        for src_path, arcname in _iter_source_files():
            data = src_path.read_bytes()
            zf.writestr(arcname, data)
            rows.append([arcname, _hash_bytes(data), str(len(data))])

        metadata = _metadata_text().encode("utf-8")
        wheel = "\n".join(["Wheel-Version: 1.0", "Generator: custom-backend", "Root-Is-Purelib: true", f"Tag: {TAG}", ""]).encode("utf-8")
        entry_points = _entry_points_text().encode("utf-8")

        zf.writestr(f"{dist_info}/METADATA", metadata)
        rows.append([f"{dist_info}/METADATA", _hash_bytes(metadata), str(len(metadata))])

        zf.writestr(f"{dist_info}/WHEEL", wheel)
        rows.append([f"{dist_info}/WHEEL", _hash_bytes(wheel), str(len(wheel))])

        zf.writestr(f"{dist_info}/entry_points.txt", entry_points)
        rows.append([f"{dist_info}/entry_points.txt", _hash_bytes(entry_points), str(len(entry_points))])

        record_path = f"{dist_info}/RECORD"
        record_lines = []
        for row in rows:
            record_lines.append(",".join(row))
        record_lines.append(f"{record_path},,")
        record_data = ("\n".join(record_lines) + "\n").encode("utf-8")
        zf.writestr(record_path, record_data)

    return wheel_name


def build_wheel(wheel_directory: str, config_settings=None, metadata_directory: str | None = None) -> str:
    return _build_wheel_file(wheel_directory, metadata_directory)


def build_editable(wheel_directory: str, config_settings=None, metadata_directory: str | None = None) -> str:
    return _build_wheel_file(wheel_directory, metadata_directory)


def get_requires_for_build_wheel(config_settings=None) -> list[str]:
    return []


def get_requires_for_build_editable(config_settings=None) -> list[str]:
    return []


def prepare_metadata_for_build_wheel(metadata_directory: str, config_settings=None) -> str:
    dist_info = Path(metadata_directory) / _dist_info_dir()
    dist_info.mkdir(parents=True, exist_ok=True)
    (dist_info / "METADATA").write_text(_metadata_text(), encoding="utf-8")
    (dist_info / "WHEEL").write_text(
        "\n".join(["Wheel-Version: 1.0", "Generator: custom-backend", "Root-Is-Purelib: true", f"Tag: {TAG}", ""]),
        encoding="utf-8",
    )
    (dist_info / "entry_points.txt").write_text(_entry_points_text(), encoding="utf-8")
    (dist_info / "RECORD").write_text("", encoding="utf-8")
    return _dist_info_dir()


def prepare_metadata_for_build_editable(metadata_directory: str, config_settings=None) -> str:
    return prepare_metadata_for_build_wheel(metadata_directory, config_settings)
