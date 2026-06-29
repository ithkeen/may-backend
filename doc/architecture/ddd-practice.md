# DDD 代码落地规则

本文面向 AI code agent。目标不是解释 DDD 概念，而是约束在本项目里怎么写代码、代码放哪里、哪些写法容易错。

架构规则只维护本文档。项目按四层组织，依赖方向固定为：

```text
api -> application -> domain
infrastructure -> domain
```

层职责：

- `api`：HTTP 边界，只处理请求、响应、依赖注入、错误映射，不写 SQL，不调用外部 SDK。
- `application`：用例编排，只负责加载对象、调用领域行为、保存结果、触发后续流程。
- `domain`：业务规则、聚合根、值对象、领域异常、Repository Protocol，不依赖框架和基础设施。
- `infrastructure`：数据库、对象存储、模型服务、外部 HTTP、Repository 实现、ORM 映射、事务。

## 先判断走哪条路径

每次实现新功能，先分类。

走复杂领域路径：

- 有状态流转，例如创建、排队、运行、成功、失败、重试、取消、审核、发布。
- 有业务不变量，例如成功任务必须有结果图，失败任务必须有失败原因。
- 多个字段或子对象必须在同一事务内保持一致。
- 有并发修改风险，例如多个 worker 抢同一个任务。
- 后续规则明显会变复杂，例如生图任务、审核流程、发布流程。

走简单 CRUD 路径：

- 只是增删改查。
- 没有状态机。
- 没有强业务不变量。
- 不需要聚合内多对象一致性。
- 例如分类、标签、配置项、平台选项、静态字典。

如果功能属于生图任务状态、生成结果、重试、审核、发布链路，默认按复杂领域处理。

## 复杂领域目录

以 `generation` 为例：

```text
src/may_backend/
  domain/
    generation/
      __init__.py
      generation_job.py       # 聚合根：状态流转和核心规则
      value_objects.py        # 参数、快照、引用、尺寸等值对象
      events.py               # 已发生的业务事实
      repositories.py         # Repository Protocol，只定义接口
      errors.py               # 领域异常，不使用 HTTPException

  application/
    use_cases/
      generation/
        __init__.py
        create_generation_job.py
        start_generation_job.py
        complete_generation_job.py
        retry_generation_job.py

  infrastructure/
    supabase/
      generation_job_models.py        # ORM / 表映射
      generation_job_repository.py    # Repository 实现、事务、映射

  api/
    v1/
      endpoints/
        generation_jobs.py            # HTTP 边界
```

职责边界：

- `domain/generation/generation_job.py`：只能写业务规则和状态变化，不导入 FastAPI、SQLAlchemy、Supabase、HTTP client、云 SDK。
- `domain/generation/repositories.py`：只放接口，不写 SQL。
- `application/use_cases/generation/`：一个文件表达一个用例，负责编排，不承载核心状态规则。
- `infrastructure/supabase/`：写 ORM、SQL、事务、行对象和领域对象的转换。
- `api/v1/endpoints/`：只处理 HTTP 请求、响应、依赖注入和错误映射。

## 简单 CRUD 目录

简单 CRUD 不强制创建 `domain/<module>/`，也不强制创建聚合根。

推荐结构：

```text
src/may_backend/
  api/
    v1/
      endpoints/
        product_categories.py

  application/
    use_cases/
      product_categories.py

  infrastructure/
    supabase/
      product_category_models.py
      product_category_repository.py
```

如果用例数量变多，再拆目录：

```text
src/may_backend/application/use_cases/product_categories/
  create_product_category.py
  update_product_category.py
  delete_product_category.py
  list_product_categories.py
```

简单 CRUD 的底线：

- API 层仍然不直接写 SQL。
- 不要为了“像 DDD”创建空洞的聚合根。
- 不要把 ORM row 包一层后伪装成领域实体。
- 当 CRUD 出现状态流转、不变量、并发一致性时，再提升为复杂领域路径。

## 聚合根写法

复杂领域里，外部代码不能直接改聚合内部状态。

不要这样写：

```python
job.status = JobStatus.SUCCEEDED
job.result_images.append(image_ref)
```

应该让聚合根暴露业务动作：

```python
job.complete_with_results(result_images)
```

聚合根方法必须做规则校验：

```python
def complete_with_results(self, results: list[GeneratedImageRef]) -> None:
    if self.status != JobStatus.RUNNING:
        raise InvalidJobState("Only running jobs can complete")

    if not results:
        raise InvalidGenerationResult("Succeeded job requires result images")

    self.result_images = results
    self.status = JobStatus.SUCCEEDED
```

应用服务只编排：

```python
job = await repository.get(command.job_id)
job.complete_with_results(command.results)
await repository.save(job)
```

## 跨聚合规则

聚合之间只通过 ID、快照或事件协作。

例如 `GenerationJob` 可以保存：

```text
product_id
product_snapshot
input_asset_ids
asset_snapshots
```

不要让 `GenerationJob` 直接修改 `Product` 或 `Asset` 的内部状态。跨聚合后续动作优先用 application use case 或领域事件串联。

## Repository 和建表规则

Repository 接口放 domain，Repository 实现放 infrastructure。

领域层接口：

```python
class GenerationJobRepository(Protocol):
    async def get(self, job_id: GenerationJobId) -> GenerationJob: ...
    async def save(self, job: GenerationJob) -> None: ...
```

基础设施实现负责：

- ORM row 和 domain aggregate 互转。
- 同一聚合内多表保存的事务。
- 乐观锁或并发控制。
- 数据库约束兜底。

建表不要按“一个类一张表”机械映射。一个 `GenerationJob` 聚合可以对应多张表：

```text
generation_jobs
generation_job_input_assets
generation_job_results
generation_job_events
```

值对象可以是列或 JSON：

```text
ImageSize        -> width / height 列
GenerationParams -> JSON 初期可接受
PromptSpec       -> JSON 初期可接受
```

需要查询、分页、约束、统计、独立状态的数据，优先单独建表。

复杂列表页和报表不要强迫聚合承担。可以在 infrastructure/application 增加 query/read model，但不要把读模型当聚合根。

## 日志位置

新增或修改日志前，先读：

```text
doc/domain/logger/usage.md
doc/domain/logger/rules.md
```

默认做法：

- API 层记录请求边界、拒绝、HTTP 错误映射。
- Application 层记录用例开始、关键业务状态变化、可预期失败。
- Infrastructure 层记录外部依赖调用结果、重试、异常。
- Domain 聚合方法默认不直接打日志，避免领域层依赖运行时设施。

## 最容易写错的地方

不要写：

- `domain` 导入 FastAPI、SQLAlchemy、Supabase、云 SDK、HTTP client。
- API endpoint 直接操作 database session。
- application use case 直接写 SQL。
- ORM model 直接作为领域实体返回。
- 聚合根只有字段，所有业务判断都写在 service。
- 外部代码直接改 `job.status`、`job.results`、`job.retry_count`。
- 每张表都建一个领域实体。
- 每个对象都建成聚合。
- 为简单 CRUD 创建没有行为的空聚合。
- 在一个聚合方法里修改另一个聚合的内部状态。
- 用裸 `dict` / `list` 表达复杂业务对象。

应该写：

- 复杂状态规则放聚合根方法。
- 用例只做加载、调用领域行为、保存、触发后续流程。
- 跨聚合只保存 ID、快照或发布事件。
- Repository 接口只面向领域对象。
- Repository 实现负责数据映射和事务。
- 数据库用非空、唯一、外键、状态约束、乐观锁兜底。
- 简单 CRUD 保持轻量，等规则变复杂再升级。

## Agent 实现顺序

复杂领域功能按这个顺序写：

1. 确认用例和状态规则。
2. 在 `domain/<module>/` 写聚合根、值对象、领域异常。
3. 在 `domain/<module>/repositories.py` 定义仓储接口。
4. 在 `application/use_cases/<module>/` 写用例编排。
5. 在 `infrastructure/supabase/` 写 ORM、映射、仓储实现和事务。
6. 在 `api/v1/endpoints/` 写 HTTP 入口和错误映射。
7. 补测试：优先测聚合规则，再测用例，再测 API 或 repository。

简单 CRUD 功能按这个顺序写：

1. 写 API schema 和 endpoint。
2. 写 application use case。
3. 写 infrastructure model/repository。
4. 依靠数据库约束和少量应用校验。
5. 不创建聚合根，除非出现真实业务行为。
