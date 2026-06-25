# 日志领域

## 定位

日志模块作为基础设施模块提供，不放在业务领域目录下，代码目录为：

```text
src/
  may_backend/
    logger/
      __init__.py
      logger.py
      context.py
      middleware.py
      config.py
      formatter.py
      writer.py
      archive.py
```

日志模块负责给其他领域提供统一、简单的日志调用方式，并完成日志上下文补齐、格式化、文件写入和归档。

其他业务领域只负责决定什么时候打印日志，以及传递业务信息。

## 第一版目标

第一版先实现文件日志，不接入数据库和外部日志平台。

需要提供以下能力：

- 提供统一的 `logger` 调用入口。
- 业务侧只传递业务字段。
- 自动补齐日志必须字段。
- 日志以 JSON Lines 格式写入单个文件。
- 支持日志文件归档。
- 日志写入失败不影响主业务流程。

## 对外调用方式

业务侧直接引入统一 logger：

```python
from may_backend.logger import logger
```

调用示例：

```python
logger.info(
    event="task.running",
    task_id=task_id,
    duration_ms=duration_ms,
)
```

失败日志示例：

```python
logger.error(
    event="task.failed",
    task_id=task_id,
    duration_ms=duration_ms,
    error_code="MODEL_TIMEOUT",
    message="model call timeout",
)
```

业务侧可以传任意业务字段 key/value。第一版不做业务字段白名单，也不做额外字段校验。

## 必须字段

每条日志必须包含以下 4 个字段：

```text
timestamp
level
trace_id
request_id
```

这 4 个字段由日志模块自动生成或从上下文中读取，业务侧不需要传递。

日志模块组装日志时，需要确保最终记录中一定存在这 4 个字段。

## 日志格式

日志最终以扁平 JSON 对象写入文件。

示例：

```json
{
  "timestamp": "2026-06-24T13:30:10.123Z",
  "level": "INFO",
  "trace_id": "trc_01JZ...",
  "request_id": "req_01JZ...",
  "event": "task.running",
  "task_id": "task_123",
  "duration_ms": 1250
}
```

错误日志示例：

```json
{
  "timestamp": "2026-06-24T13:30:14.901Z",
  "level": "ERROR",
  "trace_id": "trc_01JZ...",
  "request_id": "req_01JZ...",
  "event": "task.failed",
  "task_id": "task_123",
  "duration_ms": 5021,
  "error_code": "MODEL_TIMEOUT",
  "message": "model call timeout"
}
```

文件中实际存储为 JSON Lines，一行一条日志：

```jsonl
{"timestamp":"2026-06-24T13:30:10.123Z","level":"INFO","trace_id":"trc_01JZ...","request_id":"req_01JZ...","event":"task.running","task_id":"task_123","duration_ms":1250}
{"timestamp":"2026-06-24T13:30:14.901Z","level":"ERROR","trace_id":"trc_01JZ...","request_id":"req_01JZ...","event":"task.failed","task_id":"task_123","duration_ms":5021,"error_code":"MODEL_TIMEOUT","message":"model call timeout"}
```

## 上下文管理

日志模块需要通过 `contextvars` 保存当前执行上下文中的：

```text
trace_id
request_id
```

HTTP 请求入口由中间件负责生成或继承上下文：

```text
request
 -> logger middleware
 -> 读取或生成 trace_id
 -> 读取或生成 request_id
 -> 写入 contextvars
 -> 执行业务逻辑
 -> logger 自动补齐 trace_id 和 request_id
```

异步任务由任务调度或执行入口设置日志上下文：

```python
with logger.context(trace_id=trace_id, request_id=request_id):
    logger.info(
        event="task.running",
        task_id=task_id,
        duration_ms=duration_ms,
    )
```

任务领域内部仍然只传业务信息，不需要关心 `timestamp`、`level`、`trace_id`、`request_id` 如何生成。

## 配置

第一版支持以下配置：

```text
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_FILE=app.jsonl
LOG_RETENTION_DAYS=7
```

配置含义：

- `LOG_LEVEL`：最低日志级别。
- `LOG_DIR`：日志目录。
- `LOG_FILE`：日志文件名。
- `LOG_RETENTION_DAYS`：日志文件保留天数，默认 7 天。

日志最终统一写入：

```text
${LOG_DIR}/${LOG_FILE}
```

例如：

```text
logs/app.jsonl
```

## 文件写入

所有日志级别统一写入同一个文件，不按级别拆分文件。

写入方式：

- 使用追加写入。
- 每次写入一行 JSON。
- 每条日志必须是合法 JSON。
- 单条日志写入失败时，不阻断业务流程。

## 日志归档

第一版需要支持日志归档能力。

采用按天归档的方式。当前日期的日志始终写入：

```text
logs/app.jsonl
```

当日期切换后，将上一天的当前日志文件归档为：

```text
logs/app-20260625-213010.jsonl
```

归档后重新创建新的当前日志文件：

```text
logs/app.jsonl
```

第一版至少需要具备：

- 判断当前日志文件是否属于今天。
- 跨天后移动为同目录下带日期时间的历史日志文件。
- 创建新的当前日志文件。
- 清理超过 `LOG_RETENTION_DAYS` 的旧日志文件。

不引入单独的归档目录，归档文件和当前日志文件统一保存在 `LOG_DIR` 下。

## 模块职责

### logger.py

对外提供日志入口：

```python
logger.debug(...)
logger.info(...)
logger.warning(...)
logger.error(...)
logger.critical(...)
```

负责接收业务字段，并把日志级别传入内部记录生成流程。

### context.py

负责管理当前执行上下文：

- 设置 `trace_id`
- 设置 `request_id`
- 获取当前 `trace_id`
- 获取当前 `request_id`
- 提供上下文管理器

### middleware.py

负责 HTTP 请求入口的日志上下文初始化：

- 从请求头读取已有 `trace_id` / `request_id`
- 如果请求头没有，则生成新的 ID
- 写入 `contextvars`
- 请求结束后清理上下文

### config.py

负责读取日志配置：

- `LOG_LEVEL`
- `LOG_DIR`
- `LOG_FILE`
- `LOG_RETENTION_DAYS`

### formatter.py

负责把日志记录转换为 JSON Lines 字符串。

### writer.py

负责把格式化后的日志追加写入文件。

### archive.py

负责日志归档：

- 判断当前日志文件是否属于今天。
- 跨天后把旧日志文件移动为同目录下带日期时间的历史日志文件。
- 确保新的日志文件可继续写入。
- 清理超过保留天数的旧日志文件。

## 第一版验收标准

- 可以通过 `from may_backend.logger import logger` 使用日志模块。
- 可以调用 `logger.info(event="task.running", task_id=task_id)` 写日志。
- 每条日志自动包含 `timestamp`、`level`、`trace_id`、`request_id`。
- 业务侧不需要传递 `timestamp`、`level`、`trace_id`、`request_id`。
- 日志以 JSON Lines 格式写入单个文件。
- 日志文件路径由 `LOG_DIR` 和 `LOG_FILE` 控制。
- 支持按天进行日志归档。
- 历史日志文件默认只保留最近 7 天。
- 日志写入失败不影响业务主流程。

## 测试用例设计

第一版测试用例只关注对外行为，不要求覆盖全部代码。

测试对象只覆盖公开调用方式：

```python
from may_backend.logger import logger
```

内部实现文件和内部函数不单独写测试，例如：

- `formatter.py`
- `writer.py`
- `archive.py`
- 内部 ID 生成逻辑
- 内部文件打开方式

### test_logger_writes_json_lines_with_required_fields

验证目标：业务调用不同级别的日志方法后，日志模块会写入合法 JSON Lines，并自动补齐必须字段。

配置：

```text
LOG_LEVEL=DEBUG
LOG_DIR=<tmp_path>/logs
LOG_FILE=app.jsonl
```

调用：

```python
logger.debug(event="task.debug", task_id="task_123")
logger.info(event="task.running", task_id="task_123", duration_ms=1250)
logger.warning(event="task.slow", task_id="task_123", duration_ms=3000)
logger.error(event="task.failed", task_id="task_123", error_code="MODEL_TIMEOUT")
```

预期：

- 生成 `<tmp_path>/logs/app.jsonl`。
- 文件中每一行都是合法 JSON。
- 每条日志都包含：
  - `timestamp`
  - `level`
  - `trace_id`
  - `request_id`
- 每条日志的 `level` 与调用方法一致。
- 业务字段被扁平写入日志。
- 多个级别的日志统一写入同一个文件。

不验证：

- `timestamp` 的精确值。
- `trace_id` 的具体生成算法。
- `request_id` 的具体生成算法。
- 内部格式化和写文件实现细节。

### test_logger_context_adds_trace_and_request_id

验证目标：外部执行上下文中设置的 `trace_id` 和 `request_id` 会自动进入日志，业务调用时不需要传递这些字段。

调用：

```python
with logger.context(trace_id="trc_test", request_id="req_test"):
    logger.info(event="task.running", task_id="task_123")
```

预期：

```json
{
  "trace_id": "trc_test",
  "request_id": "req_test",
  "event": "task.running",
  "task_id": "task_123"
}
```

不验证：

- `contextvars` 的内部使用方式。
- 上下文管理器内部如何设置和恢复状态。
- 异步任务调度器如何调用上下文管理器。
