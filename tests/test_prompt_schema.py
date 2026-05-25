from __future__ import annotations

import unittest


from public_opinion.prompt_schema import (
    LabelValidationError,
    build_label_messages,
    validate_label_payload,
)


class PromptSchemaTests(unittest.TestCase):
    def test_validate_label_payload_accepts_known_enums(self) -> None:
        payload = {
            "comment_id": "c1",
            "template_group": "认错态度不端正，处理方案难服众！",
            "sentiment": "负面",
            "stance": "要求进一步处理",
            "topic_tags": ["认错态度", "处理方案"],
            "emotion_intensity": "高",
            "risk_tags": ["无明显风险"],
            "is_low_info_confirmed": False,
            "is_mobilization_confirmed": False,
            "confidence": 0.91,
            "summary_reason": "评论明确表达对处理方案不满",
        }

        validated = validate_label_payload(payload)

        self.assertEqual(validated["sentiment"], "负面")
        self.assertEqual(validated["confidence"], 0.91)
        self.assertEqual(validated["topic_tags"], ["认错态度", "处理方案"])

    def test_validate_label_payload_rejects_unknown_enum(self) -> None:
        payload = {
            "comment_id": "c1",
            "template_group": "",
            "sentiment": "很生气",
            "stance": "要求进一步处理",
            "topic_tags": ["处理方案"],
            "emotion_intensity": "高",
            "risk_tags": ["无明显风险"],
            "is_low_info_confirmed": False,
            "is_mobilization_confirmed": False,
            "confidence": 0.5,
            "summary_reason": "bad",
        }

        with self.assertRaises(LabelValidationError):
            validate_label_payload(payload)

    def test_build_label_messages_includes_schema_guidance(self) -> None:
        request = {
            "request_id": "run-1-000001",
            "comment_id": "c1",
            "template_group": "",
            "comment_text_clean": "认错态度不端正，处理方案难服众！",
            "parent_comment_id": "",
            "is_root": True,
            "like_count": 100,
            "reply_count": 20,
            "char_len": 16,
            "rule_flags": {
                "is_template_text": False,
                "is_mobilization": False,
                "rule_topic_tags": ["认错态度", "处理方案"],
                "rule_risk_tags": [],
                "analysis_priority": "high",
            },
        }

        messages = build_label_messages(request)

        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("JSON", messages[0]["content"])
        self.assertIn("公关质疑", messages[0]["content"])
        self.assertIn("要求进一步处理", messages[0]["content"])
        self.assertIn("支持父评论", messages[0]["content"])
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("comment_id", messages[1]["content"])
        self.assertIn("认错态度不端正", messages[1]["content"])

    def test_validate_label_payload_normalizes_common_aliases(self) -> None:
        payload = {
            "comment_id": "c1",
            "template_group": "",
            "sentiment": "negative",
            "stance": "against",
            "topic_tags": ["认错态度", "处理方案"],
            "emotion_intensity": 8,
            "risk_tags": [],
            "is_low_info_confirmed": False,
            "is_mobilization_confirmed": False,
            "confidence": 0.9,
            "summary_reason": "评论明确批评态度和方案",
        }

        validated = validate_label_payload(payload)

        self.assertEqual(validated["sentiment"], "负面")
        self.assertEqual(validated["stance"], "反对官方处理")
        self.assertEqual(validated["emotion_intensity"], "高")

    def test_validate_label_payload_normalizes_contextual_synonyms(self) -> None:
        payload = {
            "comment_id": "c2",
            "template_group": "冲刺！冲！冲！冲！",
            "sentiment": "积极",
            "stance": "支持",
            "topic_tags": ["其他"],
            "emotion_intensity": 0.8,
            "risk_tags": ["煽动性言论"],
            "is_low_info_confirmed": False,
            "is_mobilization_confirmed": True,
            "confidence": "高",
            "summary_reason": "评论为动员式支持表达",
        }

        validated = validate_label_payload(payload)

        self.assertEqual(validated["sentiment"], "正面")
        self.assertEqual(validated["stance"], "跟随主评动员")
        self.assertEqual(validated["topic_tags"], ["无明确主题"])
        self.assertEqual(validated["emotion_intensity"], "高")
        self.assertEqual(validated["risk_tags"], ["煽动动员"])
        self.assertEqual(validated["confidence"], 0.9)

    def test_validate_label_payload_normalizes_additional_sentiment_aliases(self) -> None:
        payload = {
            "comment_id": "c3",
            "template_group": "",
            "sentiment": "中立",
            "stance": "无法判断",
            "topic_tags": ["无明确主题"],
            "emotion_intensity": "低",
            "risk_tags": [],
            "is_low_info_confirmed": True,
            "is_mobilization_confirmed": False,
            "confidence": 0.8,
            "summary_reason": "简短表态",
        }

        validated = validate_label_payload(payload)

        self.assertEqual(validated["sentiment"], "中性")

        payload["sentiment"] = "消极"
        validated = validate_label_payload(payload)
        self.assertEqual(validated["sentiment"], "负面")


if __name__ == "__main__":
    unittest.main()
