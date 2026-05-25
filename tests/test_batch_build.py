from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


from public_opinion.batch_label import build_batch_files


class BatchBuildTests(unittest.TestCase):
    def test_build_batch_files_splits_requests_and_adds_request_ids(self) -> None:
        rows = [
            {
                "comment_id": "c1",
                "template_group": "",
                "comment_text_clean": "评论1",
                "parent_comment_id": "",
                "is_root": True,
                "like_count": 1,
                "reply_count": 0,
                "char_len": 3,
                "rule_flags": {"analysis_priority": "high"},
            },
            {
                "comment_id": "c2",
                "template_group": "模板A",
                "comment_text_clean": "评论2",
                "parent_comment_id": "c1",
                "is_root": False,
                "like_count": 2,
                "reply_count": 0,
                "char_len": 3,
                "rule_flags": {"analysis_priority": "high"},
            },
            {
                "comment_id": "c3",
                "template_group": "",
                "comment_text_clean": "评论3",
                "parent_comment_id": "c1",
                "is_root": False,
                "like_count": 3,
                "reply_count": 1,
                "char_len": 3,
                "rule_flags": {"analysis_priority": "high"},
            },
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            input_path = tmp_path / "model_input.jsonl"
            output_dir = tmp_path / "batches"
            input_path.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_batch_files(input_path, output_dir, batch_size=2, run_id="run-1")

            first_batch_lines = (output_dir / "run-1-batch-0001.jsonl").read_text(encoding="utf-8").splitlines()
            second_batch_lines = (output_dir / "run-1-batch-0002.jsonl").read_text(encoding="utf-8").splitlines()
            first_request = json.loads(first_batch_lines[0])

        self.assertEqual(summary.batch_count, 2)
        self.assertEqual(summary.request_count, 3)
        self.assertEqual(len(first_batch_lines), 2)
        self.assertEqual(len(second_batch_lines), 1)
        self.assertEqual(first_request["batch_id"], "run-1-batch-0001")
        self.assertTrue(first_request["request_id"].startswith("run-1-"))
        self.assertEqual(first_request["comment_id"], "c1")


if __name__ == "__main__":
    unittest.main()
