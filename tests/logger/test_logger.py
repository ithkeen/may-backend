import json
from pathlib import Path
from uuid import uuid4

from may_backend.config import log_config
from may_backend.logger import logger


LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}


def read_json_lines(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


def read_records_for_test(test_id: str) -> list[dict[str, object]]:
    return [
        record
        for record in read_json_lines(log_config.log_path)
        if record.get("test_id") == test_id
    ]


def test_logger_writes_json_lines_with_required_fields() -> None:
    test_id = f"test_{uuid4().hex}"

    logger.debug(event="task.debug", task_id="task_123", test_id=test_id)
    logger.info(
        event="task.running",
        task_id="task_123",
        duration_ms=1250,
        test_id=test_id,
    )
    logger.warning(
        event="task.slow",
        task_id="task_123",
        duration_ms=3000,
        test_id=test_id,
    )
    logger.error(
        event="task.failed",
        task_id="task_123",
        error_code="MODEL_TIMEOUT",
        test_id=test_id,
    )
    logger.critical(event="task.critical", task_id="task_123", test_id=test_id)

    records = read_records_for_test(test_id)
    expected_levels = [
        level
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if LEVELS[level] >= LEVELS[log_config.level]
    ]

    assert [record["level"] for record in records] == expected_levels

    for record in records:
        assert "timestamp" in record
        assert "trace_id" in record
        assert "request_id" in record
        assert record["task_id"] == "task_123"

    records_by_event = {record["event"]: record for record in records}
    if "task.running" in records_by_event:
        assert records_by_event["task.running"]["duration_ms"] == 1250
    if "task.failed" in records_by_event:
        assert records_by_event["task.failed"]["error_code"] == "MODEL_TIMEOUT"


def test_logger_context_adds_trace_and_request_id() -> None:
    test_id = f"test_{uuid4().hex}"

    with logger.context(trace_id="trc_test", request_id="req_test"):
        logger.critical(event="task.running", task_id="task_123", test_id=test_id)

    records = read_records_for_test(test_id)

    assert len(records) == 1
    assert records[0]["trace_id"] == "trc_test"
    assert records[0]["request_id"] == "req_test"
    assert records[0]["event"] == "task.running"
    assert records[0]["task_id"] == "task_123"
