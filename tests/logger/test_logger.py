import json
from pathlib import Path

import pytest

from may_backend.logger import logger


def read_json_lines(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_logger_writes_json_lines_with_required_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    log_dir = tmp_path / "logs"
    log_file = log_dir / "app.jsonl"

    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_DIR", str(log_dir))
    monkeypatch.setenv("LOG_FILE", "app.jsonl")

    logger.debug(event="task.debug", task_id="task_123")
    logger.info(event="task.running", task_id="task_123", duration_ms=1250)
    logger.warning(event="task.slow", task_id="task_123", duration_ms=3000)
    logger.error(event="task.failed", task_id="task_123", error_code="MODEL_TIMEOUT")

    records = read_json_lines(log_file)

    assert [record["level"] for record in records] == [
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
    ]
    assert records[0]["event"] == "task.debug"
    assert records[1]["event"] == "task.running"
    assert records[1]["task_id"] == "task_123"
    assert records[1]["duration_ms"] == 1250
    assert records[2]["event"] == "task.slow"
    assert records[3]["event"] == "task.failed"
    assert records[3]["error_code"] == "MODEL_TIMEOUT"

    for record in records:
        assert "timestamp" in record
        assert "trace_id" in record
        assert "request_id" in record


def test_logger_context_adds_trace_and_request_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    log_dir = tmp_path / "logs"
    log_file = log_dir / "app.jsonl"

    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("LOG_DIR", str(log_dir))
    monkeypatch.setenv("LOG_FILE", "app.jsonl")

    with logger.context(trace_id="trc_test", request_id="req_test"):
        logger.info(event="task.running", task_id="task_123")

    records = read_json_lines(log_file)

    assert len(records) == 1
    assert records[0]["trace_id"] == "trc_test"
    assert records[0]["request_id"] == "req_test"
    assert records[0]["event"] == "task.running"
    assert records[0]["task_id"] == "task_123"
