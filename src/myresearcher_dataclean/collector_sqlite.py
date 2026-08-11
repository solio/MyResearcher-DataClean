"""Read the frozen ROUND-001 common subset of Collector SQLite schema v1/v2."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class CollectorContractError(RuntimeError):
    """Collector storage does not satisfy the ROUND-001 input contract."""


_REQUIRED_COLUMNS = {
    "source_item_observations": {
        "observation_id",
        "source",
        "source_item_id",
        "observation_version",
        "observed_at_utc",
        "published_at_utc",
        "source_updated_at_utc",
        "display_time_utc",
        "author_id",
        "author_name",
        "title",
        "content",
        "content_sha256",
        "url",
        "canonical_bar_code",
        "canonical_bar_name",
        "post_type",
        "post_state",
        "post_top_status",
        "read_count",
        "reply_count",
        "like_count",
        "forward_count",
        "source_times_raw_json",
        "source_metadata_json",
        "fact_fingerprint",
        "schema_version",
        "collector_version",
        "parser_version",
        "drift_from_observation_id",
    },
    "observation_evidence": {"observation_id", "evidence_id", "evidence_role"},
    "raw_evidence": {
        "evidence_id",
        "run_id",
        "evidence_kind",
        "request_url",
        "final_url",
        "fetched_at_utc",
        "http_status",
        "content_type",
        "content_sha256",
        "byte_size",
        "filesystem_path",
        "storage_version",
    },
    "observation_scopes": {"observation_id", "scope_key", "requested_bar_code"},
}

_OBSERVATION_FIELDS = (
    "observation_id",
    "source",
    "source_item_id",
    "observation_version",
    "observed_at_utc",
    "published_at_utc",
    "source_updated_at_utc",
    "display_time_utc",
    "author_id",
    "author_name",
    "title",
    "content",
    "content_sha256",
    "url",
    "canonical_bar_code",
    "canonical_bar_name",
    "post_type",
    "post_state",
    "post_top_status",
    "read_count",
    "reply_count",
    "like_count",
    "forward_count",
    "fact_fingerprint",
    "schema_version",
    "collector_version",
    "parser_version",
    "drift_from_observation_id",
)


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    try:
        rows = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
    except sqlite3.DatabaseError as exc:
        raise CollectorContractError(f"cannot inspect Collector table {table}") from exc
    return {row[1] for row in rows}


def _json_object(raw: str, field: str, observation_id: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise CollectorContractError(
            f"{field} is invalid JSON for observation {observation_id}"
        ) from exc
    if not isinstance(value, dict):
        raise CollectorContractError(
            f"{field} must be a JSON object for observation {observation_id}"
        )
    return value


def read_collector_records(database: str | Path) -> list[dict[str, Any]]:
    """Load Collector observations in stable order without write capability."""

    path = Path(database)
    if not path.is_file():
        raise CollectorContractError(f"Collector database does not exist: {path}")
    uri = path.resolve().as_uri() + "?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True)
    except sqlite3.Error as exc:
        raise CollectorContractError(
            f"cannot open Collector database read-only: {path}"
        ) from exc
    connection.row_factory = sqlite3.Row
    try:
        try:
            user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        except sqlite3.DatabaseError as exc:
            raise CollectorContractError("cannot read Collector user_version") from exc
        if user_version not in {1, 2}:
            raise CollectorContractError(
                f"Collector user_version must be one of [1, 2], got {user_version}"
            )
        for table, required in _REQUIRED_COLUMNS.items():
            actual = _columns(connection, table)
            missing = sorted(required - actual)
            if missing:
                raise CollectorContractError(
                    f"Collector table {table} is missing columns: {', '.join(missing)}"
                )
        if user_version == 2:
            retention_required = {
                "source",
                "content_sha256",
                "body_state",
                "purged_at_utc",
                "updated_at_utc",
            }
            retention_missing = sorted(
                retention_required - _columns(connection, "raw_body_state")
            )
            if retention_missing:
                raise CollectorContractError(
                    "Collector table raw_body_state is missing columns: "
                    + ", ".join(retention_missing)
                )

        try:
            connection.execute("BEGIN")
            rows = connection.execute(
                "SELECT * FROM source_item_observations "
                "ORDER BY source, source_item_id, observation_version, observation_id"
            ).fetchall()
        except sqlite3.DatabaseError as exc:
            raise CollectorContractError("cannot read Collector observations") from exc

        records: list[dict[str, Any]] = []
        for row in rows:
            observation_id = row["observation_id"]
            record = {name: row[name] for name in _OBSERVATION_FIELDS}
            record["collector_storage_version"] = user_version
            record["source_times_raw"] = _json_object(
                row["source_times_raw_json"], "source_times_raw_json", observation_id
            )
            record["source_metadata"] = _json_object(
                row["source_metadata_json"], "source_metadata_json", observation_id
            )
            retention_columns = (
                "bs.body_state, bs.purged_at_utc AS body_purged_at_utc"
                if user_version == 2
                else "NULL AS body_state, NULL AS body_purged_at_utc"
            )
            retention_join = (
                "LEFT JOIN raw_body_state AS bs "
                "ON bs.source = ? AND bs.content_sha256 = re.content_sha256"
                if user_version == 2
                else ""
            )
            evidence_rows = connection.execute(
                f"""SELECT oe.evidence_role, re.evidence_id, re.run_id,
                          re.evidence_kind, re.request_url, re.final_url,
                          re.fetched_at_utc, re.http_status, re.content_type,
                          re.content_sha256, re.byte_size, re.filesystem_path,
                          re.storage_version, {retention_columns}
                   FROM observation_evidence AS oe
                   JOIN raw_evidence AS re ON re.evidence_id = oe.evidence_id
                   {retention_join}
                   WHERE oe.observation_id = ?
                   ORDER BY oe.evidence_role, re.evidence_id""",
                (row["source"], observation_id)
                if user_version == 2
                else (observation_id,),
            ).fetchall()
            if not evidence_rows:
                raise CollectorContractError(
                    f"observation {observation_id} has no raw evidence lineage"
                )
            if user_version == 2 and any(
                item["body_state"] not in {"PRESENT", "PURGED"}
                for item in evidence_rows
            ):
                raise CollectorContractError(
                    f"observation {observation_id} has incomplete raw body retention state"
                )
            record["raw_evidence"] = [dict(item) for item in evidence_rows]
            scope_rows = connection.execute(
                """SELECT scope_key, requested_bar_code
                   FROM observation_scopes WHERE observation_id = ?
                   ORDER BY scope_key, requested_bar_code""",
                (observation_id,),
            ).fetchall()
            if not scope_rows:
                raise CollectorContractError(
                    f"observation {observation_id} has no Collector scope lineage"
                )
            record["scopes"] = [dict(item) for item in scope_rows]
            records.append(record)
        return records
    except sqlite3.DatabaseError as exc:
        raise CollectorContractError("Collector database read failed") from exc
    finally:
        connection.close()
