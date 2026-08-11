from __future__ import annotations

from copy import deepcopy
import hashlib

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


def test_unknown_angle_text_is_not_silently_removed() -> None:
    content = "涨幅 < 5%，保留 <自定义表达>、<script>示例</script> 与重复标点！！！"

    clean = clean_records([raw_record(content=content)]).clean_records[0]

    assert "< 5%" in clean["content"]
    assert "<自定义表达>" in clean["content"]
    assert "<script>示例</script>" in clean["content"]
    assert "！！！" in clean["content"]


def test_empty_and_invalid_records_have_machine_readable_reasons() -> None:
    empty = raw_record("obs-empty", title=" <br> ", content="<!-- residue --> &nbsp;")
    invalid = raw_record("obs-invalid", content=123)
    missing_lineage = raw_record("obs-no-lineage")
    missing_lineage["raw_evidence"] = []

    result = clean_records([empty, invalid, missing_lineage])

    assert result.clean_records == []
    assert [item["reason"] for item in result.rejections] == [
        "EMPTY_CONTENT",
        "INVALID_RECORD",
        "INVALID_RECORD",
    ]
    assert result.rejections[0]["lineage"]["observation_id"] == "obs-empty"
    assert result.report["reason_distribution"] == {
        "EMPTY_CONTENT": 1,
        "INVALID_RECORD": 2,
    }


def test_exact_duplicate_is_based_on_clean_text_and_keeps_stable_first_record() -> None:
    first = raw_record(
        "obs-1", source_item_id="1001", title="同一标题", content="<p>同一 正文</p>"
    )
    second = raw_record(
        "obs-2", source_item_id="1002", title="同一标题", content="同一  正文"
    )

    result = clean_records([first, second])

    assert [record["observation_id"] for record in result.clean_records] == ["obs-1"]
    rejection = result.rejections[0]
    assert rejection["reason"] == "EXACT_DUPLICATE"
    assert rejection["duplicate_of"] == result.clean_records[0]["clean_id"]
    assert rejection["lineage"]["observation_id"] == "obs-2"
    assert rejection["record_metadata"]["author_id"] == "author-1"
    assert result.report["duplicate_count"] == 1


def test_same_input_and_version_produce_identical_python_result() -> None:
    records = [raw_record(content="<p>可回放&nbsp;文本</p>")]

    first = clean_records(deepcopy(records))
    second = clean_records(deepcopy(records))

    assert first == second
    clean = first.clean_records[0]
    assert clean["clean_schema_version"] == "dataclean.clean.v1"
    assert clean["cleaning"]["version"] == CLEANING_VERSION
    assert len(clean["cleaning"]["input_text_sha256"]) == 64
    assert len(clean["cleaning"]["output_text_sha256"]) == 64
    assert clean["lineage"]["raw_evidence"][0]["evidence_id"] == "evidence-obs-1"
    assert clean["lineage"]["collector_storage_version"] == 1
