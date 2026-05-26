from __future__ import annotations

import csv
from datetime import datetime
import json
from pathlib import Path

from public_opinion.models import CommentRecord


TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
CSV_FIELDS = [
    "comment_id",
    "parent_comment_id",
    "user_id",
    "username",
    "user_level",
    "gender",
    "comment_text_raw",
    "comment_text_clean",
    "comment_time",
    "reply_count",
    "like_count",
    "signature",
    "ip_location",
    "vip_flag",
    "avatar_url",
    "source_file",
    "is_root",
    "reply_depth",
    "is_direct_reply_to_root",
    "char_len",
    "token_len",
    "is_empty_text",
    "is_short_text",
    "is_only_emoji_or_punct",
    "is_template_text",
    "template_group",
    "canonical_template_group",
    "is_low_info",
    "is_mobilization",
    "rule_topic_tags",
    "rule_risk_tags",
    "analysis_priority",
    "sentiment",
    "stance",
    "topic_tags",
    "emotion_intensity",
    "risk_tags",
    "is_low_info_confirmed",
    "is_mobilization_confirmed",
    "summary_reason",
]


def save_records_csv(records: list[CommentRecord], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(_record_to_row(record))


def load_records_csv(input_path: Path) -> list[CommentRecord]:
    records: list[CommentRecord] = []
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            records.append(_row_to_record(row))
    return records


def _record_to_row(record: CommentRecord) -> dict[str, str]:
    return {
        "comment_id": record.comment_id,
        "parent_comment_id": record.parent_comment_id,
        "user_id": record.user_id,
        "username": record.username,
        "user_level": _stringify_int(record.user_level),
        "gender": record.gender,
        "comment_text_raw": record.comment_text_raw,
        "comment_text_clean": record.comment_text_clean,
        "comment_time": record.comment_time.strftime(TIME_FORMAT) if record.comment_time else "",
        "reply_count": str(record.reply_count),
        "like_count": str(record.like_count),
        "signature": record.signature,
        "ip_location": record.ip_location,
        "vip_flag": _stringify_optional_bool(record.vip_flag),
        "avatar_url": record.avatar_url,
        "source_file": record.source_file,
        "is_root": _stringify_bool(record.is_root),
        "reply_depth": str(record.reply_depth),
        "is_direct_reply_to_root": _stringify_bool(record.is_direct_reply_to_root),
        "char_len": str(record.char_len),
        "token_len": str(record.token_len),
        "is_empty_text": _stringify_bool(record.is_empty_text),
        "is_short_text": _stringify_bool(record.is_short_text),
        "is_only_emoji_or_punct": _stringify_bool(record.is_only_emoji_or_punct),
        "is_template_text": _stringify_bool(record.is_template_text),
        "template_group": record.template_group,
        "canonical_template_group": record.canonical_template_group,
        "is_low_info": _stringify_bool(record.is_low_info),
        "is_mobilization": _stringify_bool(record.is_mobilization),
        "rule_topic_tags": json.dumps(record.rule_topic_tags, ensure_ascii=False),
        "rule_risk_tags": json.dumps(record.rule_risk_tags, ensure_ascii=False),
        "analysis_priority": record.analysis_priority,
        "sentiment": record.sentiment,
        "stance": record.stance,
        "topic_tags": json.dumps(record.topic_tags, ensure_ascii=False),
        "emotion_intensity": record.emotion_intensity,
        "risk_tags": json.dumps(record.risk_tags, ensure_ascii=False),
        "is_low_info_confirmed": _stringify_optional_bool(record.is_low_info_confirmed),
        "is_mobilization_confirmed": _stringify_optional_bool(record.is_mobilization_confirmed),
        "summary_reason": record.summary_reason,
    }


def _row_to_record(row: dict[str, str]) -> CommentRecord:
    return CommentRecord(
        comment_id=row.get("comment_id", ""),
        parent_comment_id=row.get("parent_comment_id", ""),
        user_id=row.get("user_id", ""),
        username=row.get("username", ""),
        user_level=_parse_optional_int(row.get("user_level", "")),
        gender=row.get("gender", ""),
        comment_text_raw=row.get("comment_text_raw", ""),
        comment_text_clean=row.get("comment_text_clean", ""),
        comment_time=_parse_optional_datetime(row.get("comment_time", "")),
        reply_count=_parse_optional_int(row.get("reply_count", "")) or 0,
        like_count=_parse_optional_int(row.get("like_count", "")) or 0,
        signature=row.get("signature", ""),
        ip_location=row.get("ip_location", ""),
        vip_flag=_parse_optional_bool(row.get("vip_flag", "")),
        avatar_url=row.get("avatar_url", ""),
        source_file=row.get("source_file", ""),
        is_root=_parse_bool(row.get("is_root", "")),
        reply_depth=_parse_optional_int(row.get("reply_depth", "")) or 0,
        is_direct_reply_to_root=_parse_bool(row.get("is_direct_reply_to_root", "")),
        char_len=_parse_optional_int(row.get("char_len", "")) or 0,
        token_len=_parse_optional_int(row.get("token_len", "")) or 0,
        is_empty_text=_parse_bool(row.get("is_empty_text", "")),
        is_short_text=_parse_bool(row.get("is_short_text", "")),
        is_only_emoji_or_punct=_parse_bool(row.get("is_only_emoji_or_punct", "")),
        is_template_text=_parse_bool(row.get("is_template_text", "")),
        template_group=row.get("template_group", ""),
        canonical_template_group=row.get("canonical_template_group", ""),
        is_low_info=_parse_bool(row.get("is_low_info", "")),
        is_mobilization=_parse_bool(row.get("is_mobilization", "")),
        rule_topic_tags=_parse_json_list(row.get("rule_topic_tags", "")),
        rule_risk_tags=_parse_json_list(row.get("rule_risk_tags", "")),
        analysis_priority=row.get("analysis_priority", "medium"),
        sentiment=row.get("sentiment", ""),
        stance=row.get("stance", ""),
        topic_tags=_parse_json_list(row.get("topic_tags", "")),
        emotion_intensity=row.get("emotion_intensity", ""),
        risk_tags=_parse_json_list(row.get("risk_tags", "")),
        is_low_info_confirmed=_parse_optional_bool(row.get("is_low_info_confirmed", "")),
        is_mobilization_confirmed=_parse_optional_bool(row.get("is_mobilization_confirmed", "")),
        summary_reason=row.get("summary_reason", ""),
    )


def _parse_optional_int(value: str) -> int | None:
    text = value.strip()
    if not text:
        return None
    return int(text)


def _parse_optional_datetime(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    return datetime.strptime(text, TIME_FORMAT)


def _parse_json_list(value: str) -> list[str]:
    text = value.strip()
    if not text:
        return []
    parsed = json.loads(text)
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return [str(parsed)]


def _parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def _parse_optional_bool(value: str) -> bool | None:
    text = value.strip().lower()
    if not text:
        return None
    if text == "true":
        return True
    if text == "false":
        return False
    return None


def _stringify_bool(value: bool) -> str:
    return "true" if value else "false"


def _stringify_optional_bool(value: bool | None) -> str:
    if value is None:
        return ""
    return _stringify_bool(value)


def _stringify_int(value: int | None) -> str:
    if value is None:
        return ""
    return str(value)
