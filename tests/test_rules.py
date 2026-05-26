from __future__ import annotations

from datetime import datetime
import unittest


from public_opinion.models import CommentRecord
from public_opinion.rules import apply_rules, _canonical_for_grouping


def make_record(comment_id: str, user_id: str, text: str, like_count: int = 0) -> CommentRecord:
    return CommentRecord(
        comment_id=comment_id,
        parent_comment_id="root",
        user_id=user_id,
        username=f"user-{user_id}",
        user_level=5,
        gender="保密",
        comment_text_raw=text,
        comment_text_clean=text,
        comment_time=datetime(2026, 5, 22, 0, 0, 0),
        reply_count=0,
        like_count=like_count,
        signature="",
        ip_location="浙江",
        vip_flag=False,
        avatar_url="",
        source_file="remark.csv",
    )


class RuleTaggingTests(unittest.TestCase):
    def test_apply_rules_marks_low_info_mobilization_and_template_groups(self) -> None:
        records = [
            make_record("c1", "u1", "顶"),
            make_record("c2", "u2", "不接受这样的处理"),
            make_record("c3", "u3", "认错态度不端正，处理方案难服众！", like_count=100),
            make_record("c4", "u4", "认错态度不端正，处理方案难服众！", like_count=5),
        ]

        enriched = apply_rules(records)

        self.assertTrue(enriched[0].is_low_info)
        self.assertTrue(enriched[0].is_mobilization)
        self.assertEqual(enriched[0].analysis_priority, "low")
        self.assertFalse(enriched[1].is_low_info)
        self.assertIn("处理方案", enriched[1].rule_topic_tags)
        self.assertTrue(enriched[2].is_template_text)
        self.assertEqual(enriched[2].template_group, enriched[3].template_group)
        self.assertEqual(enriched[2].analysis_priority, "high")

    def test_canonical_for_grouping_strips_punctuation_and_emoji(self) -> None:
        self.assertEqual(_canonical_for_grouping("认错态度不端正，处理方案难服众！"), "认错态度不端正处理方案难服众")
        self.assertEqual(_canonical_for_grouping("认错态度不端正，处理方案难服众"), "认错态度不端正处理方案难服众")
        self.assertEqual(_canonical_for_grouping("冲[打call]"), "冲")
        self.assertEqual(_canonical_for_grouping("冲冲冲😡😡"), "冲冲冲")
        self.assertEqual(_canonical_for_grouping(""), "")
        self.assertEqual(_canonical_for_grouping("顶"), "顶")

    def test_near_duplicates_share_template_group(self) -> None:
        records = apply_rules([
            make_record("c1", "u1", "认错态度不端正，处理方案难服众！", like_count=100),
            make_record("c2", "u2", "认错态度不端正，处理方案难服众", like_count=50),
            make_record("c3", "u3", "认错态度不端正，处理方案难服众。", like_count=10),
        ])

        self.assertTrue(records[0].is_template_text)
        self.assertTrue(records[1].is_template_text)
        self.assertTrue(records[2].is_template_text)
        self.assertEqual(records[0].template_group, records[1].template_group)
        self.assertEqual(records[1].template_group, records[2].template_group)
        self.assertEqual(records[0].canonical_template_group, "认错态度不端正处理方案难服众")

    def test_canonical_groups_emoji_variants(self) -> None:
        records = apply_rules([
            make_record("c1", "u1", "冲[打call]", like_count=10),
            make_record("c2", "u2", "冲", like_count=5),
        ])

        self.assertTrue(records[0].is_template_text)
        self.assertTrue(records[1].is_template_text)
        self.assertEqual(records[0].template_group, records[1].template_group)


if __name__ == "__main__":
    unittest.main()
