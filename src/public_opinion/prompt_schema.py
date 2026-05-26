from __future__ import annotations

import json
from typing import Any


ALLOWED_SENTIMENTS = {"正面", "中性", "负面", "混合", "无法判断"}
ALLOWED_STANCES = {
    "支持官方处理",
    "反对官方处理",
    "要求进一步处理",
    "产品诉求导向",
    "跟随主评动员",
    "观望",
    "无法判断",
}
ALLOWED_TOPICS = {
    "认错态度",
    "处理方案",
    "处罚诉求",
    "产品改动",
    "自定义功能",
    "性别或群体对立",
    "公关质疑",
    "无明确主题",
}
ALLOWED_RISK_TAGS = {"辱骂攻击", "煽动动员", "群体对立", "极端表达", "无明显风险"}
ALLOWED_EMOTION_INTENSITY = {"低", "中", "高", "无法判断"}
SENTIMENT_ALIASES = {
    "positive": "正面",
    "neutral": "中性",
    "negative": "负面",
    "积极": "正面",
    "支持": "正面",
    "中立": "中性",
    "消极": "负面",
    "反对": "负面",
    "不满": "负面",
    "愤怒": "负面",
    "mixed": "混合",
    "unknown": "无法判断",
    "uncertain": "无法判断",
}
STANCE_ALIASES = {
    "support": "支持官方处理",
    "support_official_handling": "支持官方处理",
    "against": "反对官方处理",
    "against_official_handling": "反对官方处理",
    "disapproval": "反对官方处理",
    "反对": "反对官方处理",
    "request_further_action": "要求进一步处理",
    "request_more_action": "要求进一步处理",
    "punitive": "要求进一步处理",
    "product_demand": "产品诉求导向",
    "product_request": "产品诉求导向",
    "follow_mobilization": "跟随主评动员",
    "mobilization": "跟随主评动员",
    "wait_and_see": "观望",
    "observe": "观望",
    "unknown": "无法判断",
    "uncertain": "无法判断",
}
EMOTION_INTENSITY_ALIASES = {
    "low": "低",
    "medium": "中",
    "high": "高",
    "中等": "中",
    "强": "高",
    "高": "高",
    "低": "低",
    "unknown": "无法判断",
    "uncertain": "无法判断",
}
CONFIDENCE_ALIASES = {
    "high": 0.9,
    "高": 0.9,
    "medium": 0.6,
    "中": 0.6,
    "中等": 0.6,
    "low": 0.3,
    "低": 0.3,
}
TOPIC_TAG_ALIASES = {
    "其他": "无明确主题",
    "other": "无明确主题",
    "default": "无明确主题",
    "military": "无明确主题",
    "social_values": "无明确主题",
    "对个人的评价": "无明确主题",
    "公共管理": "无明确主题",
    "民族情绪": "无明确主题",
    "历史事件": "无明确主题",
    "comment_on_parent": "无明确主题",
    "网络文化": "无明确主题",
}
RISK_TAG_ALIASES = {
    "煽动情绪": "煽动动员",
    "煽动性言论": "煽动动员",
    "极端立场": "极端表达",
}


class LabelValidationError(ValueError):
    """Raised when a model label payload does not match the schema."""


def build_label_messages(request: dict[str, Any]) -> list[dict[str, str]]:
    system_content = (
        "你是中文舆情评论标注器。"
        "请根据输入评论输出单个 JSON 对象。"
        "不要输出 markdown，不要解释，只允许输出 JSON。"
        "sentiment 必须从固定枚举中选择；topic_tags 和 risk_tags 可以多选。"
        "topic_tags 只能从这些标签中选择：认错态度、处理方案、处罚诉求、产品改动、自定义功能、性别或群体对立、公关质疑、无明确主题。"
        "如果评论质疑官方是否转移话题、信息不透明、口径混乱、渠道来源不明、谁拍板、谁公关，优先标记为公关质疑，而不是无明确主题。"
        "stance 判断规则："
        "如果评论要求公布处罚名单、要求处理涉事人员、要求继续追责或补充方案，优先标记为要求进一步处理；"
        "只有在评论直接否定当前官方态度、当前官方方案、当前回应方式时，才标记为反对官方处理；"
        "如果只是支持父评论、支持另一个评论者、称赞他人观点，但没有明确表态官方处理是否正确，标记为无法判断，而不是支持官方处理；"
        "如果评论包含极端词汇（杀、死、自刎、滚）或诅咒且无具体诉求，sentiment 为负面时 stance 优先标为反对官方处理。"
        "注意：'冲''冲刺''顶'等打气口号即使标了煽动动员，也不代表 stance 是反对官方处理，如果口号本身没有否定官方的含义，stance 应标为无法判断。"
        "'战'字开头的口号（如'战至最后一刻''战！！！！！'）具有对抗性，sentiment 应标为负面，不是正面。"
        "emotion_intensity 判断规则：根据评论用词的激烈程度判断，不要参考点赞数。"
        "高：包含辱骂、诅咒、极端词汇（杀、死、滚、战）、大量感叹号（3个及以上）、愤怒表情符号（😡🤬等）、全大写或重复强调；"
        "中：包含不满、质疑、讽刺语气，有1-2个感叹号或1个表情符号（😂[打call]等）；"
        "低：平铺直叙、温和批评、纯陈述、无感叹号无表情符号；"
        "emoji 或表情符号（如😂😡[打call][生气]）存在时，emotion_intensity 至少为中，不论评论多短。"
        "如果评论非常简短（5字以内）且不含感叹号或表情符号，即使情感负面，emotion_intensity 也应为低。"
        "risk_tags 判断规则："
        "以下情况不标记煽动动员：单独的'顶''冲''加油'等1-3字打气词、简单复读、纯表情回复。"
        "以下情况标记煽动动员：(1)带有明确行动意图的口号，如'冲就完了''继续打''给我上去'等表达推动集体行动意图的完整语句；"
        "(2)用反问、羞辱、激将的方式施压他人行动，例如'其他人是没手吗''为什么不评论''是死人吗'等贬低沉默者；"
        "(3)将不行动等同于懦弱、背叛、不关心，制造道德压力。"
        "示例1：'我要看到涉事人员处罚名单' -> stance=要求进一步处理, topic_tags=[处罚诉求]。"
        "示例2：'皇叔说的在理' -> stance=无法判断。"
        "示例3：'态度也一般，这完全是在转移话题，谁拍板这么干的，渠道信息哪收集的' -> topic_tags 至少包含公关质疑。"
        "示例4：'其他人是没手吗，为什么不评论' -> risk_tags=[煽动动员]，这是用反问羞辱沉默者、施压他人行动，属于隐性煽动。"
        "示例5：'认错态度不端正，处理方案难服众' -> emotion_intensity=低，因为是平铺直叙的批评，无感叹号无表情。"
        "示例6：'冲就完了' -> risk_tags=[煽动动员]，有明确推动集体行动的意图。"
    )
    user_content = (
        "请标注下面的评论。\n"
        "返回字段必须包含：comment_id, template_group, sentiment, stance, topic_tags, "
        "emotion_intensity, risk_tags, is_low_info_confirmed, is_mobilization_confirmed, "
        "confidence, summary_reason。\n"
        f"输入数据：{json.dumps(request, ensure_ascii=False)}"
    )
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def validate_label_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload = _normalize_payload(payload)
    required_fields = [
        "comment_id",
        "template_group",
        "sentiment",
        "stance",
        "topic_tags",
        "emotion_intensity",
        "risk_tags",
        "is_low_info_confirmed",
        "is_mobilization_confirmed",
        "confidence",
        "summary_reason",
    ]
    missing_fields = [field for field in required_fields if field not in payload]
    if missing_fields:
        raise LabelValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    sentiment = _validated_choice(
        "sentiment",
        payload["sentiment"],
        ALLOWED_SENTIMENTS,
        SENTIMENT_ALIASES,
    )
    stance = _validated_choice(
        "stance",
        payload["stance"],
        ALLOWED_STANCES,
        STANCE_ALIASES,
    )
    emotion_intensity = _validated_choice(
        "emotion_intensity",
        payload["emotion_intensity"],
        ALLOWED_EMOTION_INTENSITY,
        EMOTION_INTENSITY_ALIASES,
    )
    topic_tags = _validated_list("topic_tags", payload["topic_tags"], ALLOWED_TOPICS)
    risk_tags = _validated_list("risk_tags", payload["risk_tags"], ALLOWED_RISK_TAGS)
    confidence = _validated_confidence(payload["confidence"])

    return {
        "comment_id": str(payload["comment_id"]),
        "template_group": str(payload["template_group"]),
        "sentiment": sentiment,
        "stance": stance,
        "topic_tags": topic_tags,
        "emotion_intensity": emotion_intensity,
        "risk_tags": risk_tags,
        "is_low_info_confirmed": _validated_bool("is_low_info_confirmed", payload["is_low_info_confirmed"]),
        "is_mobilization_confirmed": _validated_bool(
            "is_mobilization_confirmed",
            payload["is_mobilization_confirmed"],
        ),
        "confidence": confidence,
        "summary_reason": str(payload["summary_reason"]).strip(),
    }


def _validated_choice(
    field_name: str,
    value: Any,
    allowed: set[str],
    aliases: dict[str, str] | None = None,
) -> str:
    text = _normalize_choice_value(field_name, value, aliases or {})
    if text not in allowed:
        raise LabelValidationError(f"Invalid {field_name}: {text}")
    return text


def _validated_list(field_name: str, value: Any, allowed: set[str]) -> list[str]:
    if not isinstance(value, list):
        raise LabelValidationError(f"{field_name} must be a list")
    validated: list[str] = []
    for item in value:
        text = str(item).strip()
        if text not in allowed:
            raise LabelValidationError(f"Invalid {field_name} value: {text}")
        if text not in validated:
            validated.append(text)
    return validated


def _validated_bool(field_name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise LabelValidationError(f"{field_name} must be a bool")
    return value


def _validated_confidence(value: Any) -> float:
    if isinstance(value, str):
        alias_key = value.strip().lower()
        if alias_key in CONFIDENCE_ALIASES:
            return CONFIDENCE_ALIASES[alias_key]
    try:
        confidence = float(value)
    except (TypeError, ValueError) as exc:
        raise LabelValidationError("confidence must be numeric") from exc
    if confidence < 0 or confidence > 1:
        raise LabelValidationError("confidence must be between 0 and 1")
    return confidence


def _normalize_choice_value(field_name: str, value: Any, aliases: dict[str, str]) -> str:
    if field_name == "emotion_intensity" and isinstance(value, (int, float)):
        return _bucket_emotion_intensity(float(value))

    text = str(value).strip()
    if not text:
        return text

    alias_key = text.lower()
    if alias_key in aliases:
        return aliases[alias_key]
    return text


def _bucket_emotion_intensity(value: float) -> str:
    if value < 0:
        raise LabelValidationError("emotion_intensity must not be negative")
    if value <= 1:
        if value <= 0.33:
            return "低"
        if value <= 0.66:
            return "中"
        return "高"
    if value <= 3:
        return "低"
    if value <= 6:
        return "中"
    if value <= 10:
        return "高"
    raise LabelValidationError("emotion_intensity numeric scale must be between 0 and 10")


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    normalized["stance"] = _normalize_stance(payload)
    normalized["topic_tags"] = _normalize_topic_tags(payload.get("topic_tags"))
    normalized["risk_tags"] = _normalize_risk_tags(payload.get("risk_tags"))
    return normalized


def _normalize_stance(payload: dict[str, Any]) -> Any:
    value = payload.get("stance")
    if not isinstance(value, str):
        return value

    text = value.strip()
    alias_key = text.lower()
    if alias_key in STANCE_ALIASES:
        return STANCE_ALIASES[alias_key]
    if text in STANCE_ALIASES:
        return STANCE_ALIASES[text]

    if text in {"支持", "support", "supportive"}:
        if bool(payload.get("is_mobilization_confirmed")):
            return "跟随主评动员"
        return "无法判断"
    return value


def _normalize_topic_tags(value: Any) -> Any:
    if not isinstance(value, list):
        return value

    normalized: list[str] = []
    for item in value:
        text = str(item).strip()
        if not text:
            continue
        alias_key = text.lower()
        mapped = TOPIC_TAG_ALIASES.get(alias_key, TOPIC_TAG_ALIASES.get(text, text))
        if mapped not in normalized:
            normalized.append(mapped)
    return normalized


def _normalize_risk_tags(value: Any) -> Any:
    if not isinstance(value, list):
        return value

    normalized: list[str] = []
    for item in value:
        text = str(item).strip()
        if not text:
            continue
        alias_key = text.lower()
        mapped = RISK_TAG_ALIASES.get(alias_key, RISK_TAG_ALIASES.get(text, text))
        if mapped in {"质疑官方", "问责诉求"}:
            continue
        if mapped not in normalized:
            normalized.append(mapped)
    return normalized
