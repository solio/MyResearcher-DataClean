from __future__ import annotations

import json
import hashlib
import sqlite3
from pathlib import Path

import pytest

from myresearcher_dataclean.collector_sqlite import (
    CollectorContractError,
    read_collector_records,
    read_collector_posts,
)


OBSERVATION_COLUMNS = """
    observation_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_item_id TEXT NOT NULL,
    observation_version INTEGER NOT NULL,
    observed_at_utc TEXT NOT NULL,
    published_at_utc TEXT NOT NULL,
    source_updated_at_utc TEXT,
    display_time_utc TEXT,
    author_id TEXT,
    author_name TEXT,
    title TEXT,
    content TEXT NOT NULL,
    content_sha256 TEXT,
    url TEXT NOT NULL,
    canonical_bar_code TEXT,
    canonical_bar_name TEXT,
    post_type INTEGER NOT NULL,
    post_state INTEGER,
    post_top_status INTEGER,
    read_count INTEGER,
    reply_count INTEGER,
    like_count INTEGER,
    forward_count INTEGER,
    source_times_raw_json TEXT NOT NULL,
    source_metadata_json TEXT NOT NULL,
    fact_fingerprint TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    collector_version TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    drift_from_observation_id TEXT
"""


def create_collector_db(
    path: Path, *, user_version: int = 1, bad_json: bool = False
) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        f"""
        PRAGMA user_version = {user_version};
        CREATE TABLE source_item_observations ({OBSERVATION_COLUMNS});
        CREATE TABLE raw_evidence (
            evidence_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, attempt_id TEXT NOT NULL,
            evidence_kind TEXT NOT NULL, request_url TEXT NOT NULL, final_url TEXT,
            fetched_at_utc TEXT NOT NULL, http_status INTEGER, content_type TEXT,
            content_sha256 TEXT NOT NULL, byte_size INTEGER NOT NULL,
            filesystem_path TEXT NOT NULL, storage_version TEXT NOT NULL
        );
        CREATE TABLE observation_evidence (
            observation_id TEXT NOT NULL, evidence_id TEXT NOT NULL, evidence_role TEXT NOT NULL
        );
        CREATE TABLE observation_scopes (
            observation_id TEXT NOT NULL, scope_key TEXT NOT NULL, requested_bar_code TEXT NOT NULL
        );
        """
    )
    metadata = "{" if bad_json else json.dumps({"extra": {}, "source_post_id": None})
    content = "<p>正文&nbsp;内容</p>"
    connection.execute(
        """INSERT INTO source_item_observations VALUES (
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )""",
        (
            "obs-1",
            "eastmoney_guba",
            "1001",
            1,
            "2026-08-11T02:00:00.000000Z",
            "2026-08-11T01:00:00.000000Z",
            None,
            None,
            "author-1",
            "作者",
            "标题",
            content,
            hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "https://guba.eastmoney.com/news,600519,1001.html",
            "600519",
            "贵州茅台吧",
            0,
            0,
            0,
            1,
            2,
            3,
            4,
            json.dumps({"post_publish_time": "2026-08-11 09:00:00"}),
            metadata,
            "2" * 64,
            "eastmoney_guba.raw.v1",
            "eastmoney_guba.collector.v1",
            "eastmoney_guba.parser.v1",
            None,
        ),
    )
    connection.execute(
        "INSERT INTO raw_evidence VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "evidence-detail",
            "run-1",
            "attempt-1",
            "detail",
            "https://guba.eastmoney.com/news,600519,1001.html",
            "https://guba.eastmoney.com/news,600519,1001.html",
            "2026-08-11T02:00:00.000000Z",
            200,
            "text/html",
            "3" * 64,
            100,
            "raw/evidence.html",
            "raw.v1",
        ),
    )
    connection.execute(
        "INSERT INTO observation_evidence VALUES (?,?,?)",
        ("obs-1", "evidence-detail", "detail"),
    )
    connection.execute(
        "INSERT INTO observation_scopes VALUES (?,?,?)",
        ("obs-1", "stock:600519", "600519"),
    )
    connection.commit()
    connection.close()


def test_reads_exact_collector_v1_fields_and_lineage(tmp_path: Path) -> None:
    database = tmp_path / "collector.db"
    create_collector_db(database)

    records = read_collector_records(database)

    assert len(records) == 1
    record = records[0]
    assert record["observation_id"] == "obs-1"
    assert record["collector_storage_version"] == 1
    assert record["source_metadata"] == {"extra": {}, "source_post_id": None}
    assert record["raw_evidence"][0]["evidence_role"] == "detail"
    assert record["raw_evidence"][0]["run_id"] == "run-1"
    assert record["raw_evidence"][0]["body_state"] is None
    assert record["scopes"] == [
        {"scope_key": "stock:600519", "requested_bar_code": "600519"}
    ]


def test_rejects_wrong_schema_version_and_bad_json(tmp_path: Path) -> None:
    wrong = tmp_path / "wrong.db"
    create_collector_db(wrong, user_version=3)
    with pytest.raises(CollectorContractError, match="user_version"):
        read_collector_records(wrong)

    bad_json = tmp_path / "bad-json.db"
    create_collector_db(bad_json, bad_json=True)
    with pytest.raises(CollectorContractError, match="source_metadata_json"):
        read_collector_records(bad_json)


def test_requires_raw_evidence_lineage(tmp_path: Path) -> None:
    database = tmp_path / "missing-lineage.db"
    create_collector_db(database)
    connection = sqlite3.connect(database)
    connection.execute("DELETE FROM observation_evidence")
    connection.commit()
    connection.close()

    with pytest.raises(CollectorContractError, match="raw evidence lineage"):
        read_collector_records(database)


def test_requires_collector_scope_lineage(tmp_path: Path) -> None:
    database = tmp_path / "missing-scope.db"
    create_collector_db(database)
    connection = sqlite3.connect(database)
    connection.execute("DELETE FROM observation_scopes")
    connection.commit()
    connection.close()

    with pytest.raises(CollectorContractError, match="scope lineage"):
        read_collector_records(database)


def test_reads_mutable_posts_with_narrow_read_only_adapter(tmp_path: Path) -> None:
    database = tmp_path / "posts.db"
    connection = sqlite3.connect(database)
    connection.execute(
        """CREATE TABLE posts (
            source TEXT NOT NULL, source_item_id TEXT NOT NULL,
            stock_code TEXT NOT NULL, title TEXT, content TEXT,
            author_id TEXT, author_name TEXT, published_at TEXT NOT NULL,
            url TEXT NOT NULL, read_count INTEGER, reply_count INTEGER,
            like_count INTEGER, forward_count INTEGER,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            PRIMARY KEY(source, source_item_id)
        )"""
    )
    connection.execute(
        "INSERT INTO posts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "eastmoney_guba", "post-1", "600519", "标题", "正文",
            "author-1", "作者", "2026-08-11T01:00:00Z",
            "https://example.test/post-1", 1, 2, 3, 4,
            "2026-08-11T02:00:00Z", "2026-08-11T02:00:00Z",
        ),
    )
    connection.commit()
    connection.close()

    records = read_collector_posts(database)

    assert records == [
        {
            "source": "eastmoney_guba",
            "source_item_id": "post-1",
            "stock_code": "600519",
            "title": "标题",
            "content": "正文",
            "author_id": "author-1",
            "author_name": "作者",
            "published_at": "2026-08-11T01:00:00Z",
            "url": "https://example.test/post-1",
            "read_count": 1,
            "reply_count": 2,
            "like_count": 3,
            "forward_count": 4,
            "created_at": "2026-08-11T02:00:00Z",
            "updated_at": "2026-08-11T02:00:00Z",
        }
    ]


def test_posts_adapter_rejects_missing_column(tmp_path: Path) -> None:
    database = tmp_path / "posts-missing.db"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE posts (source TEXT, source_item_id TEXT)")
    connection.commit()
    connection.close()

    with pytest.raises(CollectorContractError, match="posts is missing columns"):
        read_collector_posts(database)
