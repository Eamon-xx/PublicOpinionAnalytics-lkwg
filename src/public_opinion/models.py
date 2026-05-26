from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class CommentRecord:
    comment_id: str
    parent_comment_id: str
    user_id: str
    username: str
    user_level: int | None
    gender: str
    comment_text_raw: str
    comment_text_clean: str
    comment_time: datetime | None
    reply_count: int
    like_count: int
    signature: str
    ip_location: str
    vip_flag: bool | None
    avatar_url: str
    source_file: str
    is_root: bool = False
    reply_depth: int = 0
    is_direct_reply_to_root: bool = False
    char_len: int = 0
    token_len: int = 0
    is_empty_text: bool = False
    is_short_text: bool = False
    is_only_emoji_or_punct: bool = False
    is_template_text: bool = False
    template_group: str = ""
    canonical_template_group: str = ""
    is_low_info: bool = False
    is_mobilization: bool = False
    rule_topic_tags: list[str] = field(default_factory=list)
    rule_risk_tags: list[str] = field(default_factory=list)
    analysis_priority: str = "medium"
    sentiment: str = ""
    stance: str = ""
    topic_tags: list[str] = field(default_factory=list)
    emotion_intensity: str = ""
    risk_tags: list[str] = field(default_factory=list)
    is_low_info_confirmed: bool | None = None
    is_mobilization_confirmed: bool | None = None
    summary_reason: str = ""

