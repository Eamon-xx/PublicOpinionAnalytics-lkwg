from __future__ import annotations

from datetime import datetime
import unittest


from public_opinion.aggregate import aggregate_by_field, aggregate_multi_value_field
from public_opinion.models import CommentRecord


def make_record(
    comment_id: str,
    user_id: str,
    stance: str,
    topic_tags: list[str],
    like_count: int,
) -> CommentRecord:
    record = CommentRecord(
        comment_id=comment_id,
        parent_comment_id="root",
        user_id=user_id,
        username=f"user-{user_id}",
        user_level=5,
        gender="保密",
        comment_text_raw="示例评论",
        comment_text_clean="示例评论",
        comment_time=datetime(2026, 5, 22, 0, 0, 0),
        reply_count=0,
        like_count=like_count,
        signature="",
        ip_location="浙江",
        vip_flag=False,
        avatar_url="",
        source_file="remark.csv",
    )
    record.stance = stance
    record.topic_tags = topic_tags
    return record


class AggregateTests(unittest.TestCase):
    def test_aggregate_counts_include_comment_and_unique_user_metrics(self) -> None:
        records = [
            make_record("c1", "u1", "要求进一步处理", ["处理方案"], 10),
            make_record("c2", "u1", "要求进一步处理", ["处理方案"], 5),
            make_record("c3", "u2", "产品诉求导向", ["产品改动"], 2),
        ]

        rows = aggregate_by_field(records, "stance")

        self.assertEqual(rows[0]["value"], "要求进一步处理")
        self.assertEqual(rows[0]["comment_count"], 2)
        self.assertEqual(rows[0]["unique_user_count"], 1)
        self.assertEqual(rows[0]["like_count_sum"], 15)

    def test_aggregate_multi_value_field_counts_list_tags(self) -> None:
        records = [
            make_record("c1", "u1", "要求进一步处理", ["处理方案", "处罚诉求"], 10),
            make_record("c2", "u2", "要求进一步处理", ["处理方案"], 5),
        ]

        rows = aggregate_multi_value_field(records, "topic_tags")

        self.assertEqual(rows[0]["value"], "处理方案")
        self.assertEqual(rows[0]["comment_count"], 2)
        self.assertEqual(rows[1]["value"], "处罚诉求")
        self.assertEqual(rows[1]["unique_user_count"], 1)


if __name__ == "__main__":
    unittest.main()
