from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from myresearcher_dataclean.fresh_pool import (
    DEFAULT_SEED,
    _exact_content_group,
    _forum_visible_text,
    build_fresh_pool,
    run,
)


def test_forum_html_attributes_are_removed_but_visible_text_and_breaks_remain() -> None:
    raw = (
        '<div class="outer" data-state="open"><span class="name">思源</span>'
        '<a href="https://example.test/002028">电气</a></div>'
        '<p>第二行</p><script>hidden()</script><style>.x{display:none}</style>'
    )

    visible = _forum_visible_text(raw)

    assert "思源" in visible and "电气" in visible and "第二行" in visible
    assert "hidden" not in visible and "display:none" not in visible
    assert "<" not in visible and "href=" not in visible and "class=" not in visible
    assert "data-state" not in visible
    assert "\n" in visible


def test_build_keeps_raw_content_and_uses_visible_model_text_for_long_body() -> None:
    raw_content = (
        '<div class="outer"><span data-kind="stock">思源</span>'
        '<a href="https://example.test/002028">电气</a></div>'
        '<p>' + ("完整正文" * 20) + "</p><script>do_not_emit()</script>"
    )
    records, _ = build_fresh_pool(
        [post("html", stock_code="002028", title="带标记正文", content=raw_content)],
        legacy_source_item_ids=set(),
        pilot_source_item_ids=set(),
        covered_groups=set(),
        pilot_records=[],
        collector_db_sha256="b" * 64,
        target_size=1,
        seed=DEFAULT_SEED,
    )

    assert len(records) == 1
    assert records[0]["content"] == raw_content
    assert "思源电气" in records[0]["model_text"]
    assert "do_not_emit" not in records[0]["model_text"]
    assert "<" not in records[0]["model_text"]
    assert records[0]["text_length"] > 40


def post(
    source_item_id: str,
    *,
    stock_code: str = "600519",
    title: str = "标题",
    content: str | None = "正文",
    published_at: str = "2026-08-11T01:00:00Z",
) -> dict:
    return {
        "source": "eastmoney_guba",
        "source_item_id": source_item_id,
        "stock_code": stock_code,
        "title": title,
        "content": content,
        "author_id": "author-1",
        "author_name": "作者",
        "published_at": published_at,
        "url": f"https://example.test/{source_item_id}",
        "read_count": 1,
        "reply_count": 2,
        "like_count": 3,
        "forward_count": 4,
        "created_at": "2026-08-11T02:00:00Z",
        "updated_at": "2026-08-11T02:00:00Z",
    }


def test_fresh_pool_filters_deduplicates_and_is_deterministic() -> None:
    covered_title = "已覆盖内容"
    covered_group = _exact_content_group(covered_title, covered_title)
    posts = [
        post("legacy", title="旧记录"),
        post("pilot", title="pilot记录"),
        post("covered", title=covered_title, content=None),
        post("truncated", title="一" * 39, content=None),
        post("punctuation", title="！！！", content=None),
        post("fragment", title="这公司真，", content=None),
        post("dup-a", stock_code="600519", title="A", content="<p>稳定  文本</p>"),
        post("dup-b", stock_code="601012", title="B", content="稳定 文本"),
        post("body-long", stock_code="601012", title="长正文", content="正文" * 40),
        post("title-short", stock_code="002028", title="短标题", content=None),
        post("title-medium", stock_code="002463", title="中等长度标题" * 2, content=None),
    ]
    pilot_records = [
        {
            "source_item_id": "pilot",
            "title": "pilot记录",
            "content": "pilot记录",
            "exact_content_group": _exact_content_group("pilot记录", "pilot记录"),
        },
        {
            "source_item_id": "covered",
            "title": covered_title,
            "content": covered_title,
            "exact_content_group": covered_group,
        },
    ]

    first, profile = build_fresh_pool(
        posts,
        legacy_source_item_ids={"legacy"},
        pilot_source_item_ids={"pilot"},
        covered_groups={covered_group},
        pilot_records=pilot_records,
        collector_db_sha256="a" * 64,
        target_size=4,
        seed=DEFAULT_SEED,
    )
    second, second_profile = build_fresh_pool(
        posts,
        legacy_source_item_ids={"legacy"},
        pilot_source_item_ids={"pilot"},
        covered_groups={covered_group},
        pilot_records=pilot_records,
        collector_db_sha256="a" * 64,
        target_size=4,
        seed=DEFAULT_SEED,
    )

    assert first == second
    assert profile == second_profile
    assert len(first) == 4
    assert len({record["sample_id"] for record in first}) == 4
    assert all(record["source_item_id"] not in {"legacy", "pilot", "covered"} for record in first)
    assert all(record["text_source"] in {"CONTENT", "TITLE_ONLY"} for record in first)
    assert all(record["model_text"] != "这公司真，" for record in first)
    assert profile["filter_counts"]["excluded_title_only_39_40_or_longer"] == 1
    assert profile["filter_counts"]["excluded_pure_punctuation"] == 1
    assert profile["filter_counts"]["excluded_obvious_fragment"] == 1
    assert profile["filter_counts"]["excluded_human_covered_content_group"] == 1
    assert profile["filter_counts"]["normalized_duplicate_rows_removed"] == 1
    assert profile["selected_count"] == 4
    body_long = next(record for record in first if record["source_item_id"] == "body-long")
    assert body_long["content"] == "正文" * 40
    assert body_long["text_length"] == 80


def _create_posts_db(path: Path, rows: list[dict]) -> None:
    connection = sqlite3.connect(path)
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
    connection.executemany(
        "INSERT INTO posts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                row["source"], row["source_item_id"], row["stock_code"], row["title"],
                row["content"], row["author_id"], row["author_name"], row["published_at"],
                row["url"], row["read_count"], row["reply_count"], row["like_count"],
                row["forward_count"], row["created_at"], row["updated_at"],
            )
            for row in rows
        ],
    )
    connection.commit()
    connection.close()


def test_run_writes_answer_free_jsonl_and_profile(tmp_path: Path) -> None:
    rows = [
        post("one", stock_code="002028", title="第一条", content="正文一"),
        post("two", stock_code="601012", title="第二条", content=None),
        post("three", stock_code="002463", title="第三条", content="正文三"),
    ]
    collector_db = tmp_path / "collector.db"
    legacy_db = tmp_path / "legacy.db"
    _create_posts_db(collector_db, rows)
    connection = sqlite3.connect(legacy_db)
    connection.execute("CREATE TABLE source_item_observations (source_item_id TEXT)")
    connection.execute("INSERT INTO source_item_observations VALUES (?)", ("not-present",))
    connection.commit()
    connection.close()
    pilot = tmp_path / "pilot.jsonl"
    pilot.write_bytes(b"{\"source_item_id\":\"pilot\"}\n")
    coverage = tmp_path / "coverage.jsonl"
    coverage.write_bytes(b"{}\n")

    profile = run(
        collector_db,
        legacy_db,
        pilot,
        coverage,
        tmp_path / "out",
        target_size=2,
        seed=DEFAULT_SEED,
    )

    output = tmp_path / "out/fresh-pool-2000.jsonl"
    assert output.is_file()
    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert len(records) == 2
    assert all("answer" not in record and "prediction" not in record for record in records)
    assert profile["selected_count"] == 2
    assert profile["output"]["sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert json.loads((tmp_path / "out/fresh-pool-profile.json").read_text())["seed"] == DEFAULT_SEED
