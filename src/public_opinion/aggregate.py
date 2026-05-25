from __future__ import annotations

import csv
from pathlib import Path

from public_opinion.models import CommentRecord


def aggregate_by_field(records: list[CommentRecord], field_name: str) -> list[dict[str, int | str]]:
    buckets: dict[str, dict[str, int | str | set[str]]] = {}
    for record in records:
        value = str(getattr(record, field_name, "") or "")
        if not value:
            continue
        bucket = buckets.setdefault(
            value,
            {
                "value": value,
                "comment_count": 0,
                "unique_user_ids": set(),
                "like_count_sum": 0,
            },
        )
        bucket["comment_count"] = int(bucket["comment_count"]) + 1
        bucket["like_count_sum"] = int(bucket["like_count_sum"]) + record.like_count
        user_ids = bucket["unique_user_ids"]
        assert isinstance(user_ids, set)
        user_ids.add(record.user_id)

    return _finalize_buckets(buckets)


def aggregate_multi_value_field(records: list[CommentRecord], field_name: str) -> list[dict[str, int | str]]:
    buckets: dict[str, dict[str, int | str | set[str]]] = {}
    for record in records:
        values = getattr(record, field_name, []) or []
        for value in values:
            bucket = buckets.setdefault(
                str(value),
                {
                    "value": str(value),
                    "comment_count": 0,
                    "unique_user_ids": set(),
                    "like_count_sum": 0,
                },
            )
            bucket["comment_count"] = int(bucket["comment_count"]) + 1
            bucket["like_count_sum"] = int(bucket["like_count_sum"]) + record.like_count
            user_ids = bucket["unique_user_ids"]
            assert isinstance(user_ids, set)
            user_ids.add(record.user_id)

    return _finalize_buckets(buckets)


def write_summary_csv(rows: list[dict[str, int | str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["value", "comment_count", "unique_user_count", "like_count_sum"],
        )
        writer.writeheader()
        writer.writerows(rows)


def _finalize_buckets(buckets: dict[str, dict[str, int | str | set[str]]]) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    for bucket in buckets.values():
        user_ids = bucket["unique_user_ids"]
        assert isinstance(user_ids, set)
        rows.append(
            {
                "value": str(bucket["value"]),
                "comment_count": int(bucket["comment_count"]),
                "unique_user_count": len(user_ids),
                "like_count_sum": int(bucket["like_count_sum"]),
            }
        )

    rows.sort(key=lambda row: (-int(row["comment_count"]), -int(row["like_count_sum"]), str(row["value"])))
    return rows
