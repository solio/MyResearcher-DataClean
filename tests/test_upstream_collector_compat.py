from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from myresearcher_dataclean.collector_sqlite import read_collector_records
from myresearcher_dataclean.pipeline import clean_records


COLLECTOR_SRC = (
    Path(__file__).resolve().parents[2] / "MyResearcher-DataCollector" / "src"
)
if not COLLECTOR_SRC.is_dir():
    pytest.skip(
        "sibling MyResearcher-DataCollector is unavailable", allow_module_level=True
    )
sys.path.insert(0, str(COLLECTOR_SRC))

from myresearcher_collector.models import GubaSourceItem  # noqa: E402
from myresearcher_collector.storage import RawEvidenceStore, SQLitePersistence  # noqa: E402


NOW = datetime(2026, 8, 11, 2, 0, tzinfo=timezone.utc)


def test_reads_database_created_by_upstream_collector_persistence(
    tmp_path: Path,
) -> None:
    database = tmp_path / "collector.db"
    raw_store = RawEvidenceStore(tmp_path / "collector-data")
    store = SQLitePersistence(database, raw_store)
    store.start_run(
        "run-upstream",
        "eastmoney_guba",
        "stock:600519",
        started_at=NOW,
        collector_version="eastmoney_guba.collector.v1",
        parser_version="eastmoney_guba.parser.v1",
        schema_version="eastmoney_guba.raw.v1",
    )
    evidence_links: list[tuple[str, str]] = []
    for ordinal, role in enumerate(("list", "detail")):
        attempt_id = f"attempt-{ordinal}"
        evidence_id = f"evidence-{ordinal}"
        url = (
            "https://guba.eastmoney.com/list,600519,f.html"
            if role == "list"
            else "https://guba.eastmoney.com/news,600519,1001.html"
        )
        store.record_attempt(
            "run-upstream",
            attempt_id,
            ordinal=ordinal,
            request_kind=role,
            request_url=url,
            started_at=NOW,
            finished_at=NOW,
            outcome="success",
            retry_number=1,
            retry_budget=3,
            http_status=200,
        )
        published = raw_store.publish(
            "run-upstream", ordinal, f"synthetic-{role}".encode()
        )
        store.record_raw_evidence(
            "run-upstream",
            attempt_id,
            evidence_id,
            published,
            evidence_kind=role,
            request_url=url,
            final_url=url,
            fetched_at=NOW,
            http_status=200,
            content_type="text/html",
        )
        evidence_links.append((evidence_id, role))

    item = GubaSourceItem(
        source="eastmoney_guba",
        schema_version="eastmoney_guba.raw.v1",
        source_item_id="1001",
        requested_bar_code="600519",
        canonical_bar_code="600519",
        canonical_bar_name="Synthetic Bar",
        author_id="author-1",
        author_name="Synthetic Author",
        title="synthetic title",
        content="<p>synthetic&nbsp;body</p>",
        published_at=NOW,
        last_updated_at=None,
        display_time=None,
        url="https://guba.eastmoney.com/news,600519,1001.html",
        post_type=0,
        post_state=0,
        post_top_status=0,
        read_count=0,
        reply_count=0,
        like_count=0,
        forward_count=0,
        source_post_id=None,
        collected_at=NOW,
        source_times_raw={"post_publish_time": "2026-08-11 10:00:00"},
        source_metadata={"extra": {"synthetic": True}},
        raw_ref={},
    )
    store.record_observation(
        "run-upstream",
        item,
        scope_key="stock:600519",
        evidence_links=evidence_links,
        collector_version="eastmoney_guba.collector.v1",
        parser_version="eastmoney_guba.parser.v1",
    )
    store.finish_run("run-upstream", status="SUCCESS", finished_at=NOW)
    store.close()

    records = read_collector_records(database)
    result = clean_records(records)

    assert len(records) == 1
    assert records[0]["collector_storage_version"] == 2
    assert len(records[0]["raw_evidence"]) == 2
    assert {item["body_state"] for item in records[0]["raw_evidence"]} == {"PRESENT"}
    assert result.report["cleaned_count"] == 1
    assert result.clean_records[0]["content"] == "synthetic body"
    assert (
        result.clean_records[0]["lineage"]["collector_schema_version"]
        == "eastmoney_guba.raw.v1"
    )
    assert result.clean_records[0]["lineage"]["collector_storage_version"] == 2
