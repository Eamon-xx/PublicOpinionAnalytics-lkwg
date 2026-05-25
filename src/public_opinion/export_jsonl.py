from __future__ import annotations

import json
from pathlib import Path

from public_opinion.models import CommentRecord


def export_model_inputs(records: list[CommentRecord], output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    seen_template_groups: set[str] = set()

    with output_path.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            if record.is_low_info or record.analysis_priority == "low":
                continue

            if record.template_group:
                if record.template_group in seen_template_groups:
                    continue
                seen_template_groups.add(record.template_group)

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
