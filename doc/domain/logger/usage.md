# Logger 使用说明

## 基本用法

业务代码统一从 `may_backend.logger` 引入 logger：

```python
from may_backend.logger import logger
```

直接传业务字段即可，`timestamp`、`level`、`trace_id`、`request_id` 会由日志模块自动补齐。

```python
logger.info(
    event="task.running",
    task_id="task_123",
    duration_ms=1250,
)
```

错误日志：

```python
logger.error(
    event="task.failed",
    task_id="task_123",
    error_code="MODEL_TIMEOUT",
    message="model call timeout",
)
```

## 日志级别

支持以下方法：

```python
logger.debug(event="task.debug", task_id="task_123")
logger.info(event="task.running", task_id="task_123")
logger.warning(event="task.slow", task_id="task_123")
logger.error(event="task.failed", task_id="task_123")
logger.critical(event="system.unavailable")
```

`LOG_LEVEL` 控制最低写入级别，低于该级别的日志不会写入文件。

## 上下文

异步任务或调度入口可以设置日志上下文，业务逻辑内部不用再传 `trace_id` 和 `request_id`。

```python
with logger.context(trace_id="trc_001", request_id="req_001"):
    logger.info(
        event="task.running",
        task_id="task_123",
    )
```

输出日志会包含：

```json
{
  "timestamp": "2026-06-24T13:30:10.123Z",
  "level": "INFO",
  "trace_id": "trc_001",
  "request_id": "req_001",
  "event": "task.running",
  "task_id": "task_123"
}
```

## 配置

```text
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_FILE=app.jsonl
LOG_RETENTION_DAYS=7
```

日志写入：

```text
${LOG_DIR}/${LOG_FILE}
```

默认示例：

```text
logs/app.jsonl
```
