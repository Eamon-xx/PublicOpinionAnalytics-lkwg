from __future__ import annotations

import json
from pathlib import Path

from public_opinion.models import CommentRecord


def export_model_inputs(records: list[CommentRecord], output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    eligible = [
        r for r in records
        if not r.is_low_info and r.analysis_priority != "low"
    ]

    representatives = _pick_group_representatives(eligible)

    written = 0
    with output_path.open("w", encoding="utf-8", newline="\n") as file:
        for record in representatives:
            payload = {
                "comment_id": record.comment_id,
                "comment_text_clean": record.comment_text_clean,
                "parent_comment_id": record.parent_comment_id,
                "is_root": record.is_root,
                "like_count": record.like_count,
                "reply_count": record.reply_count,
                "char_len": record.char_len,
                "template_group": record.template_group,
                "rule_flags": {
                    "is_template_text": record.is_template_text,
                    "is_mobilization": record.is_mobilization,
                    "rule_topic_tags": record.rule_topic_tags,
                    "rule_risk_tags": record.rule_risk_tags,
                    "analysis_priority": record.analysis_priority,
                },
            }
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")
            written += 1

    return written


def _pick_group_representatives(records: list[CommentRecord]) -> list[CommentRecord]:
    best_by_group: dict[str, CommentRecord] = {}
    ungrouped: list[CommentRecord] = []

    for record in records:
        canonical = record.canonical_template_group
        if not canonical:
            ungrouped.append(record)
            continue

        existing = best_by_group.get(canonical)
        if existing is None or _record_sort_key(record) > _record_sort_key(existing):
            best_by_group[canonical] = record

    return list(best_by_group.values()) + ungrouped


def _record_sort_key(record: CommentRecord) -> tuple[int, int]:
    return (record.like_count, record.char_len)
