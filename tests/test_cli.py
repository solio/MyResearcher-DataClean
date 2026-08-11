from __future__ import annotations

import json
from pathlib import Path

from myresearcher_dataclean.cli import run

from test_collector_sqlite import create_collector_db


def test_cli_writes_replayable_outputs_and_required_report_counts(
    tmp_path: Path,
) -> None:
    database = tmp_path / "collector.db"
    create_collector_db(database)
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    assert run(database, first_dir) == 0
    assert run(database, second_dir) == 0

    names = ("clean-records.jsonl", "rejections.jsonl", "run-report.json")
    for name in names:
        assert (first_dir / name).read_bytes() == (second_dir / name).read_bytes()

    report = json.loads((first_dir / "run-report.json").read_text(encoding="utf-8"))
    assert report["input_count"] == 1
    assert report["cleaned_count"] == 1
    assert report["unchanged_count"] == 0
    assert report["modified_count"] == 1
    assert report["rejected_count"] == 0
    assert report["duplicate_count"] == 0
    assert report["reason_distribution"] == {}
    assert len(report["input_database_sha256"]) == 64
    assert len(report["input_records_sha256"]) == 64
