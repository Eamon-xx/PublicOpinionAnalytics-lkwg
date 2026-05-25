from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path


from public_opinion.cli import main


SAMPLE_CSV = """序号,上级评论ID,评论ID,用户ID,用户名,用户等级,性别,评论内容,评论时间,回复数,点赞数,个性签名,IP属地,是否是大会员,头像
1,,c1,u1,用户甲,5,男,"认错态度不端正，处理方案难服众！",2026-05-22 00:00:01,3,10,,浙江,否,https://example.com/a.jpg
2,c1,c2,u2,用户乙,6,保密,顶,2026-05-22 00:00:02,0,5,签名,江苏,是,https://example.com/b.jpg
"""


class PipelineSmokeTests(unittest.TestCase):
    def test_pipeline_commands_produce_expected_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            input_path = tmp_path / "remark.csv"
            normalized_path = tmp_path / "normalized.csv"
            ruled_path = tmp_path / "ruled.csv"
            model_input_path = tmp_path / "model_input.jsonl"
            labels_path = tmp_path / "labels.jsonl"
            labeled_path = tmp_path / "labeled.csv"
            report_dir = tmp_path / "reports"
            input_path.write_text(SAMPLE_CSV, encoding="utf-8")

            self.assertEqual(main(["normalize", "--input", str(input_path), "--output", str(normalized_path)]), 0)
            self.assertEqual(
                main(
                    [
                        "prepare-model",
                        "--input",
                        str(normalized_path),
                        "--records-output",
                        str(ruled_path),
                        "--jsonl-output",
                        str(model_input_path),
                    ]
                ),
                0,
            )

            exported = model_input_path.read_text(encoding="utf-8").strip().splitlines()
            payload = json.loads(exported[0])
            labels_path.write_text(
                json.dumps(
                    {
                        "comment_id": payload["comment_id"],
                        "template_group": payload["template_group"],
                        "sentiment": "负面",
                        "stance": "要求进一步处理",
                        "topic_tags": ["处理方案"],
                        "emotion_intensity": "高",
                        "risk_tags": ["无明显风险"],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertEqual(
                main(
                    [
                        "merge-labels",
                        "--input",
                        str(ruled_path),
                        "--labels",
                        str(labels_path),
                        "--output",
                        str(labeled_path),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "aggregate",
                        "--input",
                        str(labeled_path),
                        "--output-dir",
                        str(report_dir),
                    ]
                ),
                0,
            )

            self.assertTrue(normalized_path.exists())
            self.assertTrue(ruled_path.exists())
            self.assertTrue(labeled_path.exists())
            self.assertTrue((report_dir / "stance_summary.csv").exists())

            with (report_dir / "stance_summary.csv").open("r", encoding="utf-8-sig", newline="") as file:
                rows = list(csv.DictReader(file))

        self.assertEqual(rows[0]["value"], "要求进一步处理")
        self.assertEqual(rows[0]["comment_count"], "1")


if __name__ == "__main__":
    unittest.main()
