from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path


from public_opinion.cli import main


class _BatchSmokeHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        response_payload = {
            "id": "chatcmpl-1",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
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
                                "confidence": 0.9,
                                "summary_reason": "评论表达不满",
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ],
        }
        response_bytes = json.dumps(response_payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def log_message(self, format: str, *args: object) -> None:
        return


class BatchPipelineSmokeTests(unittest.TestCase):
    def test_batch_commands_produce_valid_label_file(self) -> None:
        server = HTTPServer(("127.0.0.1", 0), _BatchSmokeHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        keys = [
            "PUBLIC_OPINION_ENV_FILE",
            "PUBLIC_OPINION_OPENAI_BASE_URL",
            "PUBLIC_OPINION_OPENAI_API_KEY",
            "PUBLIC_OPINION_OPENAI_MODEL",
            "PUBLIC_OPINION_OPENAI_TIMEOUT_SECONDS",
        ]
        old_values = {key: os.environ.get(key) for key in keys}

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                model_input_path = tmp_path / "model_input.jsonl"
                batches_dir = tmp_path / "batches"
                raw_path = tmp_path / "raw.jsonl"
                valid_path = tmp_path / "valid.jsonl"
                failure_path = tmp_path / "failures.jsonl"
                env_path = tmp_path / ".env"
                model_input_path.write_text(
                    json.dumps(
                        {
                            "comment_id": "c1",
                            "template_group": "",
                            "comment_text_clean": "认错态度不端正，处理方案难服众！",
                            "parent_comment_id": "",
                            "is_root": True,
                            "like_count": 100,
                            "reply_count": 10,
                            "char_len": 16,
                            "rule_flags": {"analysis_priority": "high"},
                        },
                        ensure_ascii=False,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                env_path.write_text(
                    "\n".join(
                        [
                            f"PUBLIC_OPINION_OPENAI_BASE_URL=http://127.0.0.1:{server.server_port}/v1",
                            "PUBLIC_OPINION_OPENAI_API_KEY=dummy-key",
                            "PUBLIC_OPINION_OPENAI_MODEL=test-model",
                            "PUBLIC_OPINION_OPENAI_TIMEOUT_SECONDS=5",
                        ]
                    )
                    + "\n",
                    encoding="utf-8",
                )
                for key in keys:
                    os.environ.pop(key, None)
                os.environ["PUBLIC_OPINION_ENV_FILE"] = str(env_path)

                self.assertEqual(
                    main(
                        [
                            "build-batches",
                            "--input",
                            str(model_input_path),
                            "--output-dir",
                            str(batches_dir),
                            "--batch-size",
                            "10",
                            "--run-id",
                            "run-1",
                        ]
                    ),
                    0,
                )
                self.assertEqual(
                    main(
                        [
                            "run-batch-label",
                            "--input",
                            str(batches_dir / "run-1-batch-0001.jsonl"),
                            "--output",
                            str(raw_path),
                        ]
                    ),
                    0,
                )
                self.assertEqual(
                    main(
                        [
                            "validate-labels",
                            "--input",
                            str(raw_path),
                            "--output",
                            str(valid_path),
                            "--failures-output",
                            str(failure_path),
                        ]
                    ),
                    0,
                )

                valid_rows = [
                    json.loads(line)
                    for line in valid_path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                failure_rows = [
                    json.loads(line)
                    for line in failure_path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
        finally:
            for key, value in old_values.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.assertEqual(len(valid_rows), 1)
        self.assertEqual(len(failure_rows), 0)
        self.assertEqual(valid_rows[0]["stance"], "要求进一步处理")


if __name__ == "__main__":
    unittest.main()
