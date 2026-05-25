from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
from urllib import request as urllib_request
from urllib import error as urllib_error

from public_opinion.prompt_schema import build_label_messages


@dataclass(slots=True)
class BatchBuildSummary:
    run_id: str
    batch_count: int
    request_count: int
    batch_paths: list[Path]


@dataclass(slots=True)
class BatchApiConfig:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: int = 30
    temperature: float = 0.0


@dataclass(slots=True)
class BatchRunSummary:
    batch_id: str
    request_count: int
    success_count: int
    failure_count: int


def build_batch_files(
    model_input_path: Path,
    output_dir: Path,
    batch_size: int,
    run_id: str,
) -> BatchBuildSummary:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    output_dir.mkdir(parents=True, exist_ok=True)
    requests = _read_jsonl(model_input_path)
    batch_paths: list[Path] = []

    for batch_index, start in enumerate(range(0, len(requests), batch_size), start=1):
        chunk = requests[start : start + batch_size]
        batch_id = f"{run_id}-batch-{batch_index:04d}"
        batch_path = output_dir / f"{batch_id}.jsonl"
        with batch_path.open("w", encoding="utf-8", newline="\n") as file:
            for row_index, row in enumerate(chunk, start=start + 1):
                payload = dict(row)
                payload["run_id"] = run_id
                payload["batch_id"] = batch_id
                payload["request_id"] = f"{run_id}-{row_index:06d}"
                file.write(json.dumps(payload, ensure_ascii=False) + "\n")
        batch_paths.append(batch_path)

    return BatchBuildSummary(
        run_id=run_id,
        batch_count=len(batch_paths),
        request_count=len(requests),
        batch_paths=batch_paths,
    )


def run_batch_labeling(
    batch_path: Path,
    output_path: Path,
    config: BatchApiConfig,
) -> BatchRunSummary:
    requests = _read_jsonl(batch_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    success_count = 0
    failure_count = 0
    batch_id = batch_path.stem

    with output_path.open("w", encoding="utf-8", newline="\n") as file:
        for row in requests:
            try:
                response_text = _call_chat_completions(row, config)
                raw_row = {
                    "request_id": row["request_id"],
                    "run_id": row["run_id"],
                    "batch_id": row["batch_id"],
                    "comment_id": row["comment_id"],
                    "template_group": row.get("template_group", ""),
                    "ok": True,
                    "response_text": response_text,
                    "error": "",
                    "model": config.model,
                }
                success_count += 1
            except Exception as exc:  # pragma: no cover - failure path exercised elsewhere
                raw_row = {
                    "request_id": row["request_id"],
                    "run_id": row["run_id"],
                    "batch_id": row["batch_id"],
                    "comment_id": row["comment_id"],
                    "template_group": row.get("template_group", ""),
                    "ok": False,
                    "response_text": "",
                    "error": str(exc),
                    "model": config.model,
                }
                failure_count += 1

            file.write(json.dumps(raw_row, ensure_ascii=False) + "\n")

    return BatchRunSummary(
        batch_id=batch_id,
        request_count=len(requests),
        success_count=success_count,
        failure_count=failure_count,
    )


def _read_jsonl(input_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with input_path.open("r", encoding="utf-8") as file:
        for line in file:
            text = line.strip()
            if not text:
                continue
            rows.append(json.loads(text))
    return rows


def _call_chat_completions(row: dict[str, Any], config: BatchApiConfig) -> str:
    endpoint = config.base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": config.model,
        "temperature": config.temperature,
        "messages": build_label_messages(row),
        "response_format": {"type": "json_object"},
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib_request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(request, timeout=config.timeout_seconds) as response:
            response_body = response.read().decode("utf-8")
    except urllib_error.HTTPError as exc:  # pragma: no cover - depends on remote
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {error_body}") from exc
    except urllib_error.URLError as exc:  # pragma: no cover - depends on remote
        raise RuntimeError(f"Request failed: {exc.reason}") from exc

    data = json.loads(response_body)
    return _extract_message_content(data)


def _extract_message_content(response_payload: dict[str, Any]) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("Missing choices in response payload")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise RuntimeError("Missing message in response payload")
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(str(item.get("text", "")))
        joined = "".join(text_parts).strip()
        if joined:
            return joined
    raise RuntimeError("Missing textual content in response payload")
