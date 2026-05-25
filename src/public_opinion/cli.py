from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from public_opinion.aggregate import (
    aggregate_by_field,
    aggregate_multi_value_field,
    write_summary_csv,
)
from public_opinion.batch_label import BatchApiConfig, build_batch_files, run_batch_labeling
from public_opinion.config import get_openai_settings
from public_opinion.export_jsonl import export_model_inputs
from public_opinion.io import load_records_csv, save_records_csv
from public_opinion.merge_labels import merge_model_labels
from public_opinion.normalize import normalize_comments
from public_opinion.rules import apply_rules
from public_opinion.validate_labels import validate_raw_results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="public-opinion",
        description="Offline public opinion analysis pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command")

    normalize_parser = subparsers.add_parser("normalize")
    normalize_parser.add_argument("--input", required=True)
    normalize_parser.add_argument("--output", required=True)

    prepare_model_parser = subparsers.add_parser("prepare-model")
    prepare_model_parser.add_argument("--input", required=True)
    prepare_model_parser.add_argument("--records-output", required=True)
    prepare_model_parser.add_argument("--jsonl-output", required=True)

    merge_labels_parser = subparsers.add_parser("merge-labels")
    merge_labels_parser.add_argument("--input", required=True)
    merge_labels_parser.add_argument("--labels", required=True)
    merge_labels_parser.add_argument("--output", required=True)

    aggregate_parser = subparsers.add_parser("aggregate")
    aggregate_parser.add_argument("--input", required=True)
    aggregate_parser.add_argument("--output-dir", required=True)

    build_batches_parser = subparsers.add_parser("build-batches")
    build_batches_parser.add_argument("--input", required=True)
    build_batches_parser.add_argument("--output-dir", required=True)
    build_batches_parser.add_argument("--batch-size", required=True, type=int)
    build_batches_parser.add_argument("--run-id", required=True)

    run_batch_label_parser = subparsers.add_parser("run-batch-label")
    run_batch_label_parser.add_argument("--input", required=True)
    run_batch_label_parser.add_argument("--output", required=True)
    run_batch_label_parser.add_argument("--base-url", required=False)
    run_batch_label_parser.add_argument("--model", required=False)
    run_batch_label_parser.add_argument("--timeout-seconds", required=False, type=int)

    validate_labels_parser = subparsers.add_parser("validate-labels")
    validate_labels_parser.add_argument("--input", required=True)
    validate_labels_parser.add_argument("--output", required=True)
    validate_labels_parser.add_argument("--failures-output", required=True)

    run_pipeline_parser = subparsers.add_parser("run-pipeline")
    run_pipeline_parser.add_argument("--input", required=True)
    run_pipeline_parser.add_argument("--output-dir", required=True)
    run_pipeline_parser.add_argument("--labels", required=False)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "normalize":
        records = normalize_comments(Path(args.input))
        save_records_csv(records, Path(args.output))
        return 0

    if args.command == "prepare-model":
        records = load_records_csv(Path(args.input))
        apply_rules(records)
        save_records_csv(records, Path(args.records_output))
        export_model_inputs(records, Path(args.jsonl_output))
        return 0

    if args.command == "merge-labels":
        records = load_records_csv(Path(args.input))
        merge_model_labels(records, Path(args.labels))
        save_records_csv(records, Path(args.output))
        return 0

    if args.command == "aggregate":
        _run_aggregate(Path(args.input), Path(args.output_dir))
        return 0

    if args.command == "build-batches":
        build_batch_files(
            model_input_path=Path(args.input),
            output_dir=Path(args.output_dir),
            batch_size=args.batch_size,
            run_id=args.run_id,
        )
        return 0

    if args.command == "run-batch-label":
        settings = get_openai_settings(
            base_url_override=args.base_url,
            model_override=args.model,
            timeout_seconds_override=args.timeout_seconds,
        )
        config = BatchApiConfig(
            base_url=settings.base_url,
            api_key=settings.api_key,
            model=settings.model,
            timeout_seconds=settings.timeout_seconds,
        )
        run_batch_labeling(
            batch_path=Path(args.input),
            output_path=Path(args.output),
            config=config,
        )
        return 0

    if args.command == "validate-labels":
        validate_raw_results(
            raw_path=Path(args.input),
            valid_output_path=Path(args.output),
            failure_output_path=Path(args.failures_output),
        )
        return 0

    if args.command == "run-pipeline":
        output_dir = Path(args.output_dir)
        normalized_path = output_dir / "normalized.csv"
        ruled_path = output_dir / "ruled.csv"
        model_input_path = output_dir / "model_input.jsonl"
        labeled_path = output_dir / "labeled.csv"
        report_dir = output_dir / "reports"

        records = normalize_comments(Path(args.input))
        save_records_csv(records, normalized_path)
        apply_rules(records)
        save_records_csv(records, ruled_path)
        export_model_inputs(records, model_input_path)

        if args.labels:
            merge_model_labels(records, Path(args.labels))
            save_records_csv(records, labeled_path)
            _write_aggregate_outputs(records, report_dir)

        return 0

    return 0


def _run_aggregate(input_path: Path, output_dir: Path) -> None:
    records = load_records_csv(input_path)
    _write_aggregate_outputs(records, output_dir)


def _write_aggregate_outputs(records: list, output_dir: Path) -> None:
    write_summary_csv(aggregate_by_field(records, "stance"), output_dir / "stance_summary.csv")
    write_summary_csv(aggregate_by_field(records, "sentiment"), output_dir / "sentiment_summary.csv")
    write_summary_csv(aggregate_multi_value_field(records, "topic_tags"), output_dir / "topic_tags_summary.csv")


if __name__ == "__main__":
    raise SystemExit(main())
