# 配置领域

配置模块负责读取 `.env` 文件，并对外暴露日志配置对象。logger 不关心配置文件怎么读取，只直接使用 `log_config`。

## 初版设计

使用 `pydantic-settings`。

初版不做复杂配置中心，只新增日志配置：

```text
src/may_backend/config/
  __init__.py
  config.py
.env.example
```

以后配置变多，再在 `config/` 包内拆更多文件。

## 对外暴露

`may_backend.config` 对外只暴露日志配置对象：

```python
log_config
```

使用方式：

```python
from may_backend.config import log_config

level = log_config.level
log_path = log_config.log_path
```

## 配置对象

初版配置对象：

```text
_LogConfig
  level
  log_dir
  log_file
  retention_days
  log_path
```

## 配置项

`.env.example`：

```text
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_FILE=app.jsonl
LOG_RETENTION_DAYS=7
```

## 文件职责

`src/may_backend/config/config.py`：

- 定义内部 `_LogConfig` 配置模型。
- 使用 `pydantic-settings` 读取 `.env`。
- 创建默认配置对象 `log_config`。

`src/may_backend/config/__init__.py`：

- 对外导出 `log_config`。

`.env.example`：

- 提供完整配置示例。

## logger 接入

logger 直接使用：

```python
from may_backend.config import log_config
```

这样 `LOG_LEVEL`、`LOG_DIR`、`LOG_FILE`、`LOG_RETENTION_DAYS` 仍然保留，不需要改配置项名称。

## 实施顺序

1. 增加依赖：`pydantic-settings`。
2. 新增 `src/may_backend/config/config.py` 和 `src/may_backend/config/__init__.py`。
3. 新增 `.env.example`。
4. 迁移 logger 使用 `log_config`。
5. 运行现有 logger 测试。
