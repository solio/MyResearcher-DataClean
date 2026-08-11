from __future__ import annotations

from copy import deepcopy
import hashlib

import pytest

from myresearcher_dataclean.pipeline import CLEANING_VERSION, clean_records


def raw_record(
    observation_id: str = "obs-1",
    *,
    source_item_id: str = "1001",
    title: str | None = "标题",
    content: object = "正文",
) -> dict:
    return {
        "observation_id": observation_id,
        "source": "eastmoney_guba",
        "source_item_id": source_item_id,
        "observation_version": 1,
        "collector_storage_version": 1,
        "observed_at_utc": "2026-08-11T02:00:00.000000Z",
        "published_at_utc": "2026-08-11T01:00:00.000000Z",
        "source_updated_at_utc": None,
        "display_time_utc": None,
        "author_id": "author-1",
        "author_name": "作者",
        "title": title,
        "content": content,
        "content_sha256": (
            hashlib.sha256(content.encode("utf-8")).hexdigest()
            if isinstance(content, str)
            else None
        ),
        "url": "https://guba.eastmoney.com/news,600519,1001.html",
        "canonical_bar_code": "600519",
        "canonical_bar_name": "贵州茅台吧",
        "post_type": 0,
        "post_state": 0,
        "post_top_status": 0,
        "read_count": 1,
        "reply_count": 2,
        "like_count": 3,
        "forward_count": 4,
        "source_times_raw": {"post_publish_time": "2026-08-11 09:00:00"},
        "source_metadata": {"source_post_id": None, "extra": {}},
        "fact_fingerprint": "2" * 64,
        "schema_version": "eastmoney_guba.raw.v1",
        "collector_version": "eastmoney_guba.collector.v1",
        "parser_version": "eastmoney_guba.parser.v1",
        "drift_from_observation_id": None,
        "raw_evidence": [
            {
                "evidence_id": f"evidence-{observation_id}",
                "evidence_role": "detail",
                "run_id": "run-1",
                "evidence_kind": "detail",
                "request_url": "https://guba.eastmoney.com/news,600519,1001.html",
                "final_url": "https://guba.eastmoney.com/news,600519,1001.html",
                "fetched_at_utc": "2026-08-11T02:00:00.000000Z",
                "content_sha256": "3" * 64,
                "byte_size": 100,
                "filesystem_path": "raw/evidence.html",
                "storage_version": "raw.v1",
            }
        ],
        "scopes": [{"scope_key": "stock:600519", "requested_bar_code": "600519"}],
    }


def test_semantic_information_is_preserved_without_semantic_classification() -> None:
    content = "垃圾股，明天继续加仓\n跌停了！！！！明天继续抄底！！！\n@老股民 $600519$ https://example.com/p/1"

    result = clean_records([raw_record(content=content)])

    assert result.report["cleaning_version"] == CLEANING_VERSION
    assert result.report["cleaned_count"] == 1
    clean = result.clean_records[0]
    assert clean["content"] == content
    assert clean["cleaning"]["rules_applied"] == []
    assert "sentiment" not in clean
    assert "stance" not in clean


def test_conservative_html_entity_unicode_and_whitespace_normalization() -> None:
    record = raw_record(
        title="\ufeff<b>垃圾股</b>&nbsp;  明天",
        content=(
            "<p>跌停了！！！！</p>\r\n"
            "<p>@someone  继续抄底！！！ <a href='https://example.com/a'>原帖</a> $600519$</p>"
        ),
    )

    clean = clean_records([record]).clean_records[0]

    assert clean["title"] == "垃圾股 明天"
    assert "跌停了！！！！" in clean["content"]
    assert "@someone" in clean["content"]
    assert "https://example.com/a" in clean["content"]
    assert "$600519$" in clean["content"]
    assert "继续抄底！！！" in clean["content"]
    assert set(clean["cleaning"]["rules_applied"]) == {
        "LEADING_BOM_REMOVED",
        "HTML_TO_TEXT",
        "WHITESPACE_NORMALIZED",
    }


def test_unknown_markup_is_preserved_by_default() -> None:
    content = (
        "涨幅 < 5%，保留 <自定义表达>、"
        '<signal data-state="retracted">旧结论</signal> 与重复标点！！！'
    )

    clean = clean_records([raw_record(content=content)]).clean_records[0]

    assert "< 5%" in clean["content"]
    assert "<自定义表达>" in clean["content"]
    assert '<signal data-state="retracted">' in clean["content"]
    assert "旧结论" in clean["content"]
    assert "</signal>" in clean["content"]
    assert "！！！" in clean["content"]


def test_attributed_markup_is_preserved_by_default() -> None:
    content = (
        '<b class="signal">强调</b>；'
        '<div data-state="deleted">区块</div>；'
        '<del data-reason="retracted">旧结论</del>'
    )

    clean = clean_records([raw_record(content=content)]).clean_records[0]

    for marker in (
        '<b class="signal">',
        "</b>",
        '<div data-state="deleted">',
        "</div>",
        '<del data-reason="retracted">',
        "</del>",
    ):
        assert marker in clean["content"]
    assert "强调" in clean["content"]
    assert "区块" in clean["content"]
    assert "旧结论" in clean["content"]


def test_meaning_bearing_deletion_markup_remains_recoverable() -> None:
    content = (
        "<del>明天涨停</del> 明天跌停；"
        "<s>旧值</s> 新值；"
        "<strike>旧结论</strike> 新结论"
    )

    clean = clean_records([raw_record(content=content)]).clean_records[0]

    for tag, child_text in (
        ("del", "明天涨停"),
        ("s", "旧值"),
        ("strike", "旧结论"),
    ):
        assert f"<{tag}>" in clean["content"]
        assert child_text in clean["content"]
        assert f"</{tag}>" in clean["content"]


def test_post_validation_and_invalid_rejections_preserve_available_lineage() -> None:
    empty = raw_record("obs-empty", title=" <br> ", content="<!-- residue --> &nbsp;")
    empty["collector_storage_version"] = 2
    empty["raw_evidence"][0].update(
        {
            "body_state": "PURGED",
            "body_purged_at_utc": "2026-08-11T03:00:00.000000Z",
        }
    )
    empty["drift_from_observation_id"] = "obs-prior"
    invalid = raw_record("obs-invalid", content=123)
    invalid["collector_storage_version"] = 2
    invalid["raw_evidence"][0].update(
        {
            "body_state": "PRESENT",
            "body_purged_at_utc": None,
        }
    )
    invalid["drift_from_observation_id"] = "obs-invalid-prior"
    missing_lineage = raw_record("obs-no-lineage")
    missing_lineage["raw_evidence"] = []

    result = clean_records([empty, invalid, missing_lineage])

    assert result.clean_records == []
    assert [item["reason"] for item in result.rejections] == [
        "EMPTY_CONTENT",
        "INVALID_RECORD",
        "INVALID_RECORD",
    ]
    empty_lineage = result.rejections[0]["lineage"]
    expected_empty_lineage = {
        "observation_id": "obs-empty",
        "source": "eastmoney_guba",
        "source_item_id": "1001",
        "observation_version": 1,
        "collector_storage_version": 2,
        "collector_schema_version": "eastmoney_guba.raw.v1",
        "collector_version": "eastmoney_guba.collector.v1",
        "parser_version": "eastmoney_guba.parser.v1",
        "fact_fingerprint": "2" * 64,
        "drift_from_observation_id": "obs-prior",
        "raw_evidence": empty["raw_evidence"],
        "scopes": empty["scopes"],
    }
    for key, expected in expected_empty_lineage.items():
        assert empty_lineage[key] == expected
    invalid_lineage = result.rejections[1]["lineage"]
    expected_invalid_lineage = {
        "observation_id": "obs-invalid",
        "source": "eastmoney_guba",
        "source_item_id": "1001",
        "observation_version": 1,
        "collector_storage_version": 2,
        "collector_schema_version": "eastmoney_guba.raw.v1",
        "collector_version": "eastmoney_guba.collector.v1",
        "parser_version": "eastmoney_guba.parser.v1",
        "fact_fingerprint": "2" * 64,
        "drift_from_observation_id": "obs-invalid-prior",
        "raw_evidence": invalid["raw_evidence"],
        "scopes": invalid["scopes"],
    }
    for key, expected in expected_invalid_lineage.items():
        assert invalid_lineage[key] == expected
    missing_lineage_best_effort = result.rejections[2]["lineage"]
    expected_best_effort = {
        "observation_id": "obs-no-lineage",
        "source": "eastmoney_guba",
        "source_item_id": "1001",
        "observation_version": 1,
        "collector_storage_version": 1,
        "collector_schema_version": "eastmoney_guba.raw.v1",
        "collector_version": "eastmoney_guba.collector.v1",
        "parser_version": "eastmoney_guba.parser.v1",
        "fact_fingerprint": "2" * 64,
        "drift_from_observation_id": None,
        "raw_evidence": [],
        "scopes": missing_lineage["scopes"],
    }
    for key, expected in expected_best_effort.items():
        assert missing_lineage_best_effort[key] == expected
    assert result.report["reason_distribution"] == {
        "EMPTY_CONTENT": 1,
        "INVALID_RECORD": 2,
    }


def test_equal_clean_content_keeps_each_distinct_observation() -> None:
    first = raw_record(
        "obs-1", source_item_id="1001", title="同一标题", content="<p>同一 正文</p>"
    )
    second = raw_record(
        "obs-2", source_item_id="1002", title="同一标题", content="同一  正文"
    )

    result = clean_records([first, second])

    assert [record["observation_id"] for record in result.clean_records] == [
        "obs-1",
        "obs-2",
    ]
    assert result.rejections == []
    first_clean, second_clean = result.clean_records
    assert first_clean["cleaning"]["exact_content_key"] == (
        second_clean["cleaning"]["exact_content_key"]
    )
    assert first_clean["cleaning"]["duplicate_content_of"] is None
    assert second_clean["cleaning"]["duplicate_content_of"] == first_clean["clean_id"]
    assert result.report["exact_content_duplicate_count"] == 1
    assert result.report["cleaned_count"] == 2
    assert result.report["rejected_count"] == 0
    assert result.report["reason_distribution"] == {}


def test_repeated_observation_identity_is_an_input_contract_failure() -> None:
    first = raw_record("obs-same", source_item_id="1001", content="第一个正文")
    repeated = raw_record("obs-same", source_item_id="1001", content="不同的第二正文")

    with pytest.raises(
        ValueError,
        match=r"(?i)(duplicate.*observation_id|observation_id.*duplicate)",
    ):
        clean_records([first, repeated])


def test_report_counts_observations_and_satisfies_contract_equations() -> None:
    unchanged = raw_record("obs-1", source_item_id="1001", content="相同正文")
    same_content_modified = raw_record(
        "obs-2", source_item_id="1002", content="<b>相同正文</b>"
    )
    empty = raw_record("obs-3", source_item_id="1003", title="<br>", content="&nbsp;")
    invalid = raw_record("obs-4", source_item_id="1004", content=123)

    result = clean_records([unchanged, same_content_modified, empty, invalid])
    report = result.report

    assert report == {
        "cleaning_version": CLEANING_VERSION,
        "clean_schema_version": "dataclean.clean.v1",
        "input_count": 4,
        "cleaned_count": 2,
        "unchanged_count": 1,
        "modified_count": 1,
        "exact_content_duplicate_count": 1,
        "rejected_count": 2,
        "reason_distribution": {"EMPTY_CONTENT": 1, "INVALID_RECORD": 1},
    }
    assert report["input_count"] == report["cleaned_count"] + report["rejected_count"]
    assert report["cleaned_count"] == (
        report["unchanged_count"] + report["modified_count"]
    )
    assert report["exact_content_duplicate_count"] <= report["cleaned_count"]
    assert sum(report["reason_distribution"].values()) == report["rejected_count"]


def test_same_input_and_version_produce_identical_python_result() -> None:
    records = [
        raw_record("obs-1", source_item_id="1001", content="<p>可回放&nbsp;文本</p>"),
        raw_record("obs-2", source_item_id="1002", content="可回放 文本"),
    ]

    first = clean_records(deepcopy(records))
    second = clean_records(deepcopy(records))

    assert first == second
    assert len(first.clean_records) == 2
    clean = first.clean_records[0]
    assert clean["clean_schema_version"] == "dataclean.clean.v1"
    assert clean["cleaning"]["version"] == CLEANING_VERSION
    assert clean["cleaning"]["exact_content_key"] == (
        first.clean_records[1]["cleaning"]["exact_content_key"]
    )
    assert first.clean_records[1]["cleaning"]["duplicate_content_of"] == clean["clean_id"]
    assert len(clean["cleaning"]["input_text_sha256"]) == 64
    assert len(clean["cleaning"]["output_text_sha256"]) == 64
    assert clean["lineage"]["raw_evidence"][0]["evidence_id"] == "evidence-obs-1"
    assert clean["lineage"]["collector_storage_version"] == 1
