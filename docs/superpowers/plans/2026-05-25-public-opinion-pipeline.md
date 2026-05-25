# Public Opinion Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable offline pipeline that normalizes comment CSV input, applies rule-based tagging, exports model-ready JSONL, merges model labels, and produces aggregation outputs for public-opinion analysis.

**Architecture:** Use a small Python package under `src/public_opinion/` with focused modules for normalization, rules, export, label merge, aggregation, and a thin CLI. Keep the first version dependency-light by using the Python standard library plus CSV/JSONL outputs, while preserving field names and interfaces that can later be upgraded to Parquet-backed storage.

**Tech Stack:** Python 3.11, Poetry, argparse, csv, json, dataclasses, pathlib, unittest

---

### Task 1: Initialize package and CLI skeleton

**Files:**
- Create: `src/public_opinion/__init__.py`
- Create: `src/public_opinion/cli.py`
- Modify: `pyproject.toml`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

```python
def test_cli_shows_help_and_subcommands():
    result = run_cli(["--help"])
    assert result.returncode == 0
    assert "normalize" in result.stdout
    assert "prepare-model" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python -m unittest tests.test_cli -v`
Expected: FAIL because `public_opinion.cli` and test helpers do not exist yet

- [ ] **Step 3: Write minimal implementation**

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(...)
    parser.add_subparsers(dest="command")
    return parser
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run python -m unittest tests.test_cli -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/public_opinion/__init__.py src/public_opinion/cli.py tests/test_cli.py
git commit -m "feat: add pipeline cli skeleton"
```

### Task 2: Implement CSV normalization

**Files:**
- Create: `src/public_opinion/models.py`
- Create: `src/public_opinion/normalize.py`
- Test: `tests/test_normalize.py`

- [ ] **Step 1: Write the failing test**

```python
def test_normalize_comments_parses_multiline_csv_and_deduplicates_ids():
    comments = normalize_comments(sample_csv_path)
    assert len(comments) == 2
    assert comments[0].comment_text_raw == "第一行\\n第二行"
    assert comments[0].is_root is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python -m unittest tests.test_normalize -v`
Expected: FAIL because normalization functions and comment models do not exist

- [ ] **Step 3: Write minimal implementation**

```python
@dataclass
class CommentRecord:
    comment_id: str
    ...

def normalize_comments(csv_path: Path) -> list[CommentRecord]:
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run python -m unittest tests.test_normalize -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/public_opinion/models.py src/public_opinion/normalize.py tests/test_normalize.py
git commit -m "feat: normalize raw comment csv"
```

### Task 3: Implement rule tagging and template grouping

**Files:**
- Create: `src/public_opinion/rules.py`
- Test: `tests/test_rules.py`

- [ ] **Step 1: Write the failing test**

```python
def test_apply_rules_marks_low_info_mobilization_and_template_groups():
    enriched = apply_rules(records)
    assert enriched[0].is_low_info is True
    assert enriched[0].is_mobilization is True
    assert enriched[2].template_group == enriched[3].template_group
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python -m unittest tests.test_rules -v`
Expected: FAIL because rule tagging is not implemented

- [ ] **Step 3: Write minimal implementation**

```python
def apply_rules(records: list[CommentRecord]) -> list[CommentRecord]:
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run python -m unittest tests.test_rules -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/public_opinion/rules.py tests/test_rules.py
git commit -m "feat: add rule-based opinion tags"
```

### Task 4: Export model-ready JSONL and merge model labels

**Files:**
- Create: `src/public_opinion/export_jsonl.py`
- Create: `src/public_opinion/merge_labels.py`
- Test: `tests/test_model_io.py`

- [ ] **Step 1: Write the failing test**

```python
def test_export_and_merge_model_labels_round_trip():
    export_model_inputs(records, output_path)
    merged = merge_model_labels(records, labels_path)
    assert merged[0].sentiment == "负面"
    assert "处理方案" in merged[0].topic_tags
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python -m unittest tests.test_model_io -v`
Expected: FAIL because export and merge modules do not exist

- [ ] **Step 3: Write minimal implementation**

```python
def export_model_inputs(...):
    ...

def merge_model_labels(...):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run python -m unittest tests.test_model_io -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/public_opinion/export_jsonl.py src/public_opinion/merge_labels.py tests/test_model_io.py
git commit -m "feat: support model input export and label merge"
```

### Task 5: Implement aggregation and end-to-end pipeline smoke test

**Files:**
- Create: `src/public_opinion/aggregate.py`
- Modify: `src/public_opinion/cli.py`
- Test: `tests/test_aggregate.py`
- Test: `tests/test_pipeline_smoke.py`

- [ ] **Step 1: Write the failing test**

```python
def test_aggregate_counts_include_comment_and_unique_user_metrics():
    rows = aggregate_by_field(records, "stance")
    assert rows[0]["comment_count"] == 2
    assert rows[0]["unique_user_count"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python -m unittest tests.test_aggregate tests.test_pipeline_smoke -v`
Expected: FAIL because aggregation and pipeline commands are incomplete

- [ ] **Step 3: Write minimal implementation**

```python
def aggregate_by_field(...):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run python -m unittest tests.test_aggregate tests.test_pipeline_smoke -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/public_opinion/aggregate.py src/public_opinion/cli.py tests/test_aggregate.py tests/test_pipeline_smoke.py
git commit -m "feat: add aggregation and pipeline commands"
```

### Task 6: Add docs and verify the full suite

**Files:**
- Create: `README.md`
- Modify: `docs/superpowers/specs/2026-05-25-public-opinion-analysis-design.md`

- [ ] **Step 1: Write the failing test**

No new behavior test for docs-only work. Use the existing smoke test output as the acceptance gate.

- [ ] **Step 2: Run verification before doc updates**

Run: `poetry run python -m unittest discover -s tests -v`
Expected: PASS before final documentation polish

- [ ] **Step 3: Write minimal implementation**

Add setup and usage instructions for:
- `normalize`
- `prepare-model`
- `merge-labels`
- `aggregate`
- `run-pipeline`

- [ ] **Step 4: Run verification after doc updates**

Run: `poetry run python -m unittest discover -s tests -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md docs/superpowers/specs/2026-05-25-public-opinion-analysis-design.md
git commit -m "docs: document public opinion pipeline usage"
```
