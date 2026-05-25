# Batch Labeling Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reusable batch-labeling pipeline that shards model-ready JSONL into batch files, calls an OpenAI-compatible chat-completions API, validates structured label outputs, and writes validated JSONL ready for merge.

**Architecture:** Keep the current offline pipeline shape and add focused modules under `src/public_opinion/` for prompt/schema definition, batch request construction, remote labeling, and result validation. Use the Python standard library for HTTP transport so the feature works in the existing Poetry environment without introducing a networking dependency.

**Tech Stack:** Python 3.11, Poetry, argparse, json, urllib, pathlib, threading, unittest

---

### Task 1: Add prompt schema and label validation

**Files:**
- Create: `src/public_opinion/prompt_schema.py`
- Test: `tests/test_prompt_schema.py`

- [ ] **Step 1: Write the failing test**

```python
def test_validate_label_payload_accepts_known_enums():
    payload = {...}
    validated = validate_label_payload(payload)
    assert validated["sentiment"] == "负面"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python -m unittest tests.test_prompt_schema -v`
Expected: FAIL because schema helpers do not exist

- [ ] **Step 3: Write minimal implementation**

```python
ALLOWED_SENTIMENTS = {...}

def build_messages(request):
    ...

def validate_label_payload(payload):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run python -m unittest tests.test_prompt_schema -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/public_opinion/prompt_schema.py tests/test_prompt_schema.py
git commit -m "feat: add batch labeling prompt schema"
```

### Task 2: Build batch request shards

**Files:**
- Create: `src/public_opinion/batch_label.py`
- Modify: `src/public_opinion/export_jsonl.py`
- Test: `tests/test_batch_build.py`

- [ ] **Step 1: Write the failing test**

```python
def test_build_batch_files_splits_requests_and_adds_request_ids():
    result = build_batch_files(model_input_path, output_dir, batch_size=2, run_id="run-1")
    assert result.batch_count == 2
    assert first_request["request_id"].startswith("run-1-")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python -m unittest tests.test_batch_build -v`
Expected: FAIL because batch builder does not exist

- [ ] **Step 3: Write minimal implementation**

```python
def build_batch_files(...):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run python -m unittest tests.test_batch_build -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/public_opinion/batch_label.py src/public_opinion/export_jsonl.py tests/test_batch_build.py
git commit -m "feat: add batch request sharding"
```

### Task 3: Call OpenAI-compatible API and persist raw results

**Files:**
- Modify: `src/public_opinion/batch_label.py`
- Test: `tests/test_batch_label_api.py`

- [ ] **Step 1: Write the failing test**

```python
def test_run_batch_labeling_calls_chat_completions_and_writes_raw_results():
    result = run_batch_labeling(...)
    assert result.success_count == 1
    assert raw_rows[0]["response_text"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python -m unittest tests.test_batch_label_api -v`
Expected: FAIL because API client and batch execution do not exist

- [ ] **Step 3: Write minimal implementation**

```python
def run_batch_labeling(...):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run python -m unittest tests.test_batch_label_api -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/public_opinion/batch_label.py tests/test_batch_label_api.py
git commit -m "feat: add openai-compatible batch labeling client"
```

### Task 4: Validate raw results and surface failures

**Files:**
- Create: `src/public_opinion/validate_labels.py`
- Test: `tests/test_validate_labels.py`

- [ ] **Step 1: Write the failing test**

```python
def test_validate_raw_results_splits_valid_rows_and_failures():
    summary = validate_raw_results(raw_path, valid_path, failure_path)
    assert summary.valid_count == 1
    assert summary.failure_count == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python -m unittest tests.test_validate_labels -v`
Expected: FAIL because validation module does not exist

- [ ] **Step 3: Write minimal implementation**

```python
def validate_raw_results(...):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run python -m unittest tests.test_validate_labels -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/public_opinion/validate_labels.py tests/test_validate_labels.py
git commit -m "feat: validate structured label outputs"
```

### Task 5: Wire CLI commands and document secret-safe usage

**Files:**
- Modify: `src/public_opinion/cli.py`
- Modify: `README.md`
- Test: `tests/test_cli.py`
- Test: `tests/test_batch_pipeline_smoke.py`

- [ ] **Step 1: Write the failing test**

```python
def test_cli_exposes_batch_labeling_commands():
    help_text = build_parser().format_help()
    assert "build-batches" in help_text
    assert "run-batch-label" in help_text
    assert "validate-labels" in help_text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python -m unittest tests.test_cli tests.test_batch_pipeline_smoke -v`
Expected: FAIL because CLI and smoke flow are incomplete

- [ ] **Step 3: Write minimal implementation**

```python
def main(argv=None):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run python -m unittest tests.test_cli tests.test_batch_pipeline_smoke -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/public_opinion/cli.py README.md tests/test_cli.py tests/test_batch_pipeline_smoke.py
git commit -m "feat: expose batch labeling pipeline commands"
```

### Task 6: Verify full suite

**Files:**
- Modify: `docs/superpowers/specs/2026-05-25-public-opinion-analysis-design.md`

- [ ] **Step 1: Write the failing test**

No new behavior test. Use the complete suite as the acceptance gate.

- [ ] **Step 2: Run verification before final spec alignment**

Run: `poetry run python -m unittest discover -s tests -v`
Expected: PASS before spec wording updates

- [ ] **Step 3: Write minimal implementation**

Update the design spec so it matches the concrete batch-labeling commands, env-var-based credential handling, and validation outputs.

- [ ] **Step 4: Run verification after spec alignment**

Run: `poetry run python -m unittest discover -s tests -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-05-25-public-opinion-analysis-design.md
git commit -m "docs: align spec with batch labeling flow"
```
