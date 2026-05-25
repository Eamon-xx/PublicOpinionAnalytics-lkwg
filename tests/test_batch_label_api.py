from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import tempfile
import threading
import unittest
from pathlib import Path


from public_opinion.batch_label import BatchApiConfig, run_batch_labeling


class _FakeOpenAIHandler(BaseHTTPRequestHandler):
    received_payloads: list[dict] = []

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers["Content-Length"])
        body = self.rfile.read(length).decode("utf-8")
        payload = json.loads(body)
        _FakeOpenAIHandler.received_payloads.append(payload)

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
                                "confidence": 0.88,
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


class BatchLabelApiTests(unittest.TestCase):
    def test_run_batch_labeling_calls_chat_completions_and_writes_raw_results(self) -> None:
        _FakeOpenAIHandler.received_payloads = []
        server = HTTPServer(("127.0.0.1", 0), _FakeOpenAIHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                batch_path = tmp_path / "run-1-batch-0001.jsonl"
                raw_output_path = tmp_path / "raw_results.jsonl"
                batch_path.write_text(
                    json.dumps(
                        {
                            "request_id": "run-1-000001",
                            "run_id": "run-1",
                            "batch_id": "run-1-batch-0001",
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
                        },
                        ensure_ascii=False,
                    )
                    + "\n",
                    encoding="utf-8",
                )

                summary = run_batch_labeling(
                    batch_path=batch_path,
                    output_path=raw_output_path,
                    config=BatchApiConfig(
                        base_url=f"http://127.0.0.1:{server.server_port}/v1",
                        api_key="test-key",
                        model="test-model",
                        timeout_seconds=5,
                    ),
                )

                raw_rows = [
                    json.loads(line)
                    for line in raw_output_path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.assertEqual(summary.success_count, 1)
        self.assertEqual(summary.failure_count, 0)
        self.assertEqual(len(raw_rows), 1)
        self.assertEqual(raw_rows[0]["comment_id"], "c1")
        self.assertTrue(raw_rows[0]["response_text"])
        self.assertEqual(_FakeOpenAIHandler.received_payloads[0]["model"], "test-model")
        self.assertEqual(_FakeOpenAIHandler.received_payloads[0]["messages"][0]["role"], "system")


if __name__ == "__main__":
    unittest.main()
