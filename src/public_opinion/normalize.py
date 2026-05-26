from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path

from public_opinion.models import CommentRecord


TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
WHITESPACE_RE = re.compile(r"\s+")


def normalize_comments(csv_path: Path) -> list[CommentRecord]:
    records: list[CommentRecord] = []
    seen_comment_ids: set[str] = set()

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            comment_id = (row.get("评论ID") or "").strip()
            if not comment_id or comment_id in seen_comment_ids:
                continue

            seen_comment_ids.add(comment_id)
            parent_comment_id = (row.get("上级评论ID") or "").strip()
            comment_text_raw = _normalize_raw_text(row.get("评论内容") or "")
            comment_text_clean = _normalize_clean_text(comment_text_raw)
            record = CommentRecord(
                comment_id=comment_id,
                parent_comment_id=parent_comment_id,
                user_id=(row.get("用户ID") or "").strip(),
                username=(row.get("用户名") or "").strip(),
                user_level=_parse_int(row.get("用户等级")),
                gender=(row.get("性别") or "").strip(),
                comment_text_raw=comment_text_raw,
                comment_text_clean=comment_text_clean,
                comment_time=_parse_time(row.get("评论时间")),
                reply_count=_parse_int(row.get("回复数")) or 0,
                like_count=_parse_int(row.get("点赞数")) or 0,
                signature=(row.get("个性签名") or "").strip(),
                ip_location=(row.get("IP属地") or "").strip(),
                vip_flag=_parse_bool_flag(row.get("是否是大会员") or row.get("是否为大会员")),
                avatar_url=(row.get("头像") or "").strip(),
                source_file=csv_path.name,
            )
            record.is_root = not bool(parent_comment_id)
            records.append(record)

    _assign_reply_metadata(records)
    return records


def _assign_reply_metadata(records: list[CommentRecord]) -> None:
    by_comment_id = {record.comment_id: record for record in records}
    root_ids = {record.comment_id for record in records if record.is_root}

    for record in records:
        if record.is_root:
            record.reply_depth = 0
            record.is_direct_reply_to_root = False
            continue

        record.reply_depth = _compute_reply_depth(record, by_comment_id)
        record.is_direct_reply_to_root = record.parent_comment_id in root_ids


def _compute_reply_depth(
    record: CommentRecord,
    by_comment_id: dict[str, CommentRecord],
) -> int:
    depth = 0
    current_parent_id = record.parent_comment_id
    visited: set[str] = set()

    while current_parent_id:
        if current_parent_id in visited:
            return max(depth, 1)
        visited.add(current_parent_id)
        depth += 1
        parent = by_comment_id.get(current_parent_id)
        if parent is None or parent.is_root:
            return depth
        current_parent_id = parent.parent_comment_id

    return max(depth, 1)


def _normalize_raw_text(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").strip()


def _normalize_clean_text(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value.replace("\n", " ")).strip()


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    text = value.strip().replace(",", "")
    if not text:
        return None
    return int(text)


def _parse_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    return datetime.strptime(text, TIME_FORMAT)


def _parse_bool_flag(value: str | None) -> bool | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if text == "是":
        return True
    if text == "否":
        return False
    return None
