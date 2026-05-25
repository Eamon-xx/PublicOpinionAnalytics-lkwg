from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from public_opinion.prompt_schema import LabelValidationError, validate_label_payload


@dataclass(slots=True)
class LabelValidationSummary:
    valid_count: int
    failure_count: int


def validate_raw_results(
    raw_path: Path,
    valid_output_path: Path,
    failure_output_path: Path,
) -> LabelValidationSummary:
    valid_output_path.parent.mkdir(parents=True, exist_ok=True)
    failure_output_path.parent.mkdir(parents=True, exist_ok=True)

    valid_count = 0
    failure_count = 0

    with (
        raw_path.open("r", encoding="utf-8") as raw_file,
        valid_output_path.open("w", encoding="utf-8", newline="\n") as valid_file,
        failure_output_path.open("w", encoding="utf-8", newline="\n") as failure_file,
    ):
        for line in raw_file:
            text = line.strip()
            if not text:
                continue
            row = json.loads(text)
            try:
                if not bool(row.get("ok")):
                    raise LabelValidationError(str(row.get("error") or "Raw request failed"))
                payload = json.loads(str(row.get("response_text") or ""))
                validated = validate_label_payload(payload)
                valid_row = {
                    **validated,
                    "request_id": row.get("request_id", ""),
                    "run_id": row.get("run_id", ""),
                    "batch_id": row.get("batch_id", ""),
                    "model": row.get("model", ""),
                }
                valid_file.write(json.dumps(valid_row, ensure_ascii=False) + "\n")
                valid_count += 1
            except (json.JSONDecodeError, LabelValidationError, TypeError, ValueError) as exc:
                failure_row = _build_failure_row(row, str(exc))
                failure_file.write(json.dumps(failure_row, ensure_ascii=False) + "\n")
                failure_count += 1

    return LabelValidationSummary(valid_count=valid_count, failure_count=failure_count)


def _build_failure_row(row: dict[str, Any], error: str) -> dict[str, Any]:
    return {
        "request_id": row.get("request_id", ""),
        "run_id": row.get("run_id", ""),
        "batch_id": row.get("batch_id", ""),
        "comment_id": row.get("comment_id", ""),
        "template_group": row.get("template_group", ""),
        "response_text": row.get("response_text", ""),
        "error": error,
        "model": row.get("model", ""),
    }
