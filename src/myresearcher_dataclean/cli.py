"""Command-line RAW-to-CLEAN execution with deterministic artifacts."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

from .collector_sqlite import CollectorContractError, read_collector_records
from .pipeline import canonical_json_bytes, clean_records


def _database_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _jsonl(records: Iterable[dict[str, Any]]) -> bytes:
    lines = [canonical_json_bytes(record) for record in records]
    return b"" if not lines else b"\n".join(lines) + b"\n"


def run(database: str | Path, output_directory: str | Path) -> int:
    database_path = Path(database)
    output_path = Path(output_directory)
    records = read_collector_records(database_path)
    result = clean_records(records)
    report = {
        **result.report,
        "input_contract": "collector.sqlite.v1-v2.common.v1",
        "input_database_sha256": _database_sha256(database_path),
        "input_records_sha256": hashlib.sha256(
            canonical_json_bytes(records)
        ).hexdigest(),
        "artifacts": {
            "clean_records": "clean-records.jsonl",
            "rejections": "rejections.jsonl",
        },
    }
    _atomic_write(output_path / "clean-records.jsonl", _jsonl(result.clean_records))
    _atomic_write(output_path / "rejections.jsonl", _jsonl(result.rejections))
    _atomic_write(output_path / "run-report.json", canonical_json_bytes(report) + b"\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="myresearcher-dataclean",
        description="Convert Collector SQLite v1/v2 observations to deterministic CLEAN JSONL.",
    )
    parser.add_argument(
        "collector_db", type=Path, help="Collector SQLite v1 or v2 database"
    )
    parser.add_argument(
        "output_directory",
        type=Path,
        help="Directory for CLEAN/rejection/report artifacts",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        return run(arguments.collector_db, arguments.output_directory)
    except CollectorContractError as exc:
        print(f"Collector input contract error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
