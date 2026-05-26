from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from public_opinion.models import CommentRecord
from public_opinion.rules import _canonical_for_grouping as _canonical_for_merge


def merge_model_labels(records: list[CommentRecord], labels_path: Path) -> list[CommentRecord]:
    labels_by_comment_id: dict[str, dict[str, Any]] = {}
    labels_by_template_group: dict[str, dict[str, Any]] = {}
    labels_by_canonical: dict[str, dict[str, Any]] = {}

    with labels_path.open("r", encoding="utf-8") as file:
        for line in file:
            payload = json.loads(line)
            comment_id = str(payload.get("comment_id") or "").strip()
            template_group = str(payload.get("template_group") or "").strip()
            if comment_id:
                labels_by_comment_id[comment_id] = payload
            if template_group:
                labels_by_template_group[template_group] = payload
                canonical = _canonical_for_merge(template_group)
                if canonical:
                    labels_by_canonical[canonical] = payload

    for record in records:
        payload = labels_by_comment_id.get(record.comment_id)
        if payload is None and record.template_group:
            payload = labels_by_template_group.get(record.template_group)
        if payload is None and record.canonical_template_group:
            payload = labels_by_canonical.get(record.canonical_template_group)
        if payload is None:
            continue
        _apply_payload(record, payload)

    return records


def _apply_payload(record: CommentRecord, payload: dict[str, Any]) -> None:
    record.sentiment = str(payload.get("sentiment") or "")
    record.stance = str(payload.get("stance") or "")
    record.topic_tags = _as_string_list(payload.get("topic_tags"))
    record.emotion_intensity = str(payload.get("emotion_intensity") or "")
    record.risk_tags = _as_string_list(payload.get("risk_tags"))
    record.is_low_info_confirmed = _as_optional_bool(payload.get("is_low_info_confirmed"))
    record.is_mobilization_confirmed = _as_optional_bool(payload.get("is_mobilization_confirmed"))
    record.summary_reason = str(payload.get("summary_reason") or "")


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _as_optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None
