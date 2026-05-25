from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


from public_opinion.export_jsonl import export_model_inputs
from public_opinion.merge_labels import merge_model_labels
from public_opinion.models import CommentRecord
from public_opinion.rules import apply_rules


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
        comment_time=None,
        reply_count=0,
        like_count=like_count,
        signature="",
        ip_location="浙江",
        vip_flag=False,
        avatar_url="",
        source_file="remark.csv",
    )


class ModelIoTests(unittest.TestCase):
    def test_export_and_merge_model_labels_round_trip(self) -> None:
        records = apply_rules(
            [
                make_record("c1", "u1", "顶"),
                make_record("c2", "u2", "认错态度不端正，处理方案难服众！", like_count=100),
                make_record("c3", "u3", "认错态度不端正，处理方案难服众！", like_count=3),
            ]
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "model_input.jsonl"
            label_path = Path(tmp_dir) / "labels.jsonl"

            exported_count = export_model_inputs(records, output_path)
            exported_lines = output_path.read_text(encoding="utf-8").strip().splitlines()
            payload = json.loads(exported_lines[0])

            label_path.write_text(
                json.dumps(
                    {
                        "comment_id": "c2",
                        "template_group": records[1].template_group,
                        "sentiment": "负面",
                        "stance": "要求进一步处理",
                        "topic_tags": ["处理方案"],
                        "emotion_intensity": "高",
                        "risk_tags": ["煽动动员"],
                        "is_low_info_confirmed": False,
                        "is_mobilization_confirmed": False,
                        "summary_reason": "处理方案被认为难以服众",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            merged = merge_model_labels(records, label_path)

        self.assertEqual(exported_count, 1)
        self.assertEqual(len(exported_lines), 1)
        self.assertEqual(payload["comment_id"], "c2")
        self.assertEqual(payload["template_group"], records[1].template_group)
        self.assertEqual(merged[1].sentiment, "负面")
        self.assertEqual(merged[2].sentiment, "负面")
        self.assertIn("处理方案", merged[1].topic_tags)
        self.assertEqual(merged[1].summary_reason, "处理方案被认为难以服众")


if __name__ == "__main__":
    unittest.main()
