from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


from public_opinion.validate_labels import validate_raw_results


class ValidateLabelsTests(unittest.TestCase):
    def test_validate_raw_results_splits_valid_rows_and_failures(self) -> None:
        raw_rows = [
            {
                "request_id": "run-1-000001",
                "run_id": "run-1",
                "batch_id": "run-1-batch-0001",
                "comment_id": "c1",
                "template_group": "",
                "ok": True,
                "response_text": json.dumps(
                    {
                        "comment_id": "c1",
                        "template_group": "",
                        "sentiment": "负面",
                        "stance": "要求进一步处理",
                        "topic_tags": ["处理方案"],
                        "emotion_intensity": "高",
                        "risk_tags": ["无明显风险"],
                        "is_low_info_confirmed": False,
                        "is_mobilization_confirmed": False,
                        "confidence": 0.8,
                        "summary_reason": "评论表达不满",
                    },
                    ensure_ascii=False,
                ),
                "error": "",
                "model": "test-model",
            },
            {
                "request_id": "run-1-000002",
                "run_id": "run-1",
                "batch_id": "run-1-batch-0001",
                "comment_id": "c2",
                "template_group": "",
                "ok": True,
                "response_text": json.dumps(
                    {
                        "comment_id": "c2",
                        "template_group": "",
                        "sentiment": "非常生气",
                        "stance": "要求进一步处理",
                        "topic_tags": ["处理方案"],
                        "emotion_intensity": "高",
                        "risk_tags": ["无明显风险"],
                        "is_low_info_confirmed": False,
                        "is_mobilization_confirmed": False,
                        "confidence": 0.7,
                        "summary_reason": "评论表达不满",
                    },
                    ensure_ascii=False,
                ),
                "error": "",
                "model": "test-model",
            },
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            raw_path = tmp_path / "raw.jsonl"
            valid_path = tmp_path / "valid.jsonl"
            failure_path = tmp_path / "failures.jsonl"
            raw_path.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in raw_rows),
                encoding="utf-8",
            )

            summary = validate_raw_results(raw_path, valid_path, failure_path)

            valid_rows = [json.loads(line) for line in valid_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            failure_rows = [json.loads(line) for line in failure_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(summary.valid_count, 1)
        self.assertEqual(summary.failure_count, 1)
        self.assertEqual(valid_rows[0]["comment_id"], "c1")
        self.assertEqual(failure_rows[0]["comment_id"], "c2")
        self.assertIn("Invalid sentiment", failure_rows[0]["error"])


if __name__ == "__main__":
    unittest.main()
