from __future__ import annotations

from collections import Counter
import re
import unicodedata

from public_opinion.models import CommentRecord


LOW_INFO_TEXTS = {
    "顶",
    "顶！",
    "顶。",
    "冲",
    "冲！",
    "1",
    "支持",
    "顶上去",
}
MOBILIZATION_KEYWORDS = ("顶", "冲", "战", "扩", "转")
TOPIC_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("认错态度", "认错"),
    ("认错态度", "道歉"),
    ("处理方案", "处理"),
    ("处理方案", "方案"),
    ("处罚诉求", "处罚"),
    ("处罚诉求", "名单"),
    ("处罚诉求", "严惩"),
    ("产品改动", "回退"),
    ("产品改动", "动作"),
    ("产品改动", "鞋子"),
    ("自定义功能", "自定义"),
    ("公关质疑", "公关"),
    ("性别或群体对立", "男玩家"),
    ("性别或群体对立", "集美"),
)
RISK_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("辱骂攻击", "护主犬"),
    ("煽动动员", "顶"),
    ("煽动动员", "冲"),
    ("群体对立", "男玩家"),
    ("群体对立", "集美"),
    ("极端表达", "杀"),
)
NON_WORD_RE = re.compile(r"\s+")


def apply_rules(records: list[CommentRecord]) -> list[CommentRecord]:
    template_counts = Counter(record.comment_text_clean for record in records if record.comment_text_clean)

    for record in records:
        clean_text = record.comment_text_clean.strip()
        record.char_len = len(clean_text)
        record.token_len = len([part for part in NON_WORD_RE.split(clean_text) if part]) if clean_text else 0
        record.is_empty_text = not bool(clean_text)
        record.is_short_text = record.char_len <= 4
        record.is_only_emoji_or_punct = _is_only_emoji_or_punct(clean_text)
        record.is_mobilization = any(keyword in clean_text for keyword in MOBILIZATION_KEYWORDS)
        record.is_low_info = _is_low_info(clean_text, record)
        record.rule_topic_tags = _collect_tags(clean_text, TOPIC_KEYWORDS)
        record.rule_risk_tags = _collect_tags(clean_text, RISK_KEYWORDS)
        record.is_template_text = template_counts[clean_text] > 1 if clean_text else False
        record.template_group = clean_text if record.is_template_text else ""
        record.analysis_priority = _assign_priority(record)

    return records


def _is_low_info(text: str, record: CommentRecord) -> bool:
    if not text:
        return True
    if text in LOW_INFO_TEXTS:
        return True
    if record.is_only_emoji_or_punct:
        return True
    if record.char_len <= 2 and not _collect_tags(text, TOPIC_KEYWORDS):
        return True
    return False


def _collect_tags(text: str, rules: tuple[tuple[str, str], ...]) -> list[str]:
    tags: list[str] = []
    for tag, keyword in rules:
        if keyword in text and tag not in tags:
            tags.append(tag)
    return tags


def _assign_priority(record: CommentRecord) -> str:
    if record.is_low_info:
        return "low"
    if record.like_count >= 50 or record.reply_count >= 10:
        return "high"
    if record.is_template_text or record.char_len >= 12 or record.rule_topic_tags:
        return "high"
    return "medium"


def _is_only_emoji_or_punct(text: str) -> bool:
    if not text:
        return False

    for char in text:
        if char.isspace():
            continue
        category = unicodedata.category(char)
        if not (category.startswith("P") or category.startswith("S")):
            return False
    return True
