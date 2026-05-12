## 维护指南（外部依赖清单）

本项目通过“外部依赖清单”来完成依赖识别与 API 命中展示。清单维护主要涉及：
- 新增/调整外部系统（system）
- 新增/调整外部系统的 API 能力（api）
- 外部系统 API 升级/变更时的兼容策略

### 清单位置与加载规则

运行时依赖清单由配置项 `work_dir` 决定，默认会从：
- `<work_dir>/input/dependencies/index.json`

项目仓库中常见两份工作目录：
- `work/input/dependencies/`：开发运行时使用（通常配置 `work_dir: work`）
- `executable/work/input/dependencies/`：可执行分发目录的默认样例

建议以 `work/input/dependencies/` 为主维护源数据；如果你需要让 `executable/` 下的分发目录也同步更新，请将同样修改同步到 `executable/work/input/dependencies/`。

### 清单结构约定

入口文件：`index.json`

基本结构：
- `systems`: 外部系统数组
- 每个 system 建议包含：
  - `id`：系统唯一标识（稳定、全大写、下划线分隔，例如 `REALNAME_AUTH`）
  - `name`：系统展示名
  - `type`：类别（例如 `external_system` / `external_service` / `external_platform` / `identity`）
  - `description`：可选，帮助搜索与识别
  - `aliases`：可选，别名数组（包含常见缩写、英文名、历史名称）
  - `keywords`：可选，关键词数组（覆盖业务场景关键词）
  - `api_file`：推荐，指向该系统的 API 文件（例如 `OCR_SYS.apis.json`）
  - `apis`：可选，直接内嵌 API 列表（适用于少量 API）

API 文件结构（推荐）：
- `{ "system_id": "<SYS_ID>", "apis": [ ... ] }`
- `apis` 元素建议包含：
  - `id`：API 能力唯一标识（稳定、可读，例如 `RN_3_ELEM`）
  - `name`：能力名称
  - `method`：HTTP 方法（可选）
  - `path`：路径（可选）
  - `keywords`：关键词（用于命中）

### 新增一个外部系统

1) 在 `work/input/dependencies/index.json` 的 `systems` 中新增一个对象，至少包含 `id/name/type`
2) 为该系统创建/补充 API：
   - 推荐新增 `<SYS_ID>.apis.json`，并在 `index.json` 里通过 `api_file` 引用
   - 如果 API 很少，也可以直接写在 `index.json` 的 `apis` 字段
3) 为系统补充 `aliases/keywords/description`，提升识别命中率与检索体验
4) 启动服务，在“依赖列表”页确认该系统可搜索/可展开 API

### API 升级与变更策略

外部系统经常出现版本升级或接口变更（路径变更、参数变化、能力拆分/合并等）。建议遵循以下策略，保证识别稳定且便于追溯：

#### 1) 尽量保持 API `id` 稳定

当仅发生“小改动”且语义不变（例如 path 前缀变化、网关调整）：
- 保留原 `id`
- 更新 `method/path/keywords`
- 在 `keywords` 中保留旧路径或旧关键字一段时间，避免历史文档无法命中

#### 2) 发生“语义变化”时新建 API

当能力语义变化较大（例如接口从“实名核验”变成“实名 + 活体合并”，或拆分成多个能力）：
- 新建新的 `id`（必要时带版本后缀，例如 `RN_ID_VERIFY_V2`）
- 原 `id` 可保留一段时间用于历史命中（或只保留关键字，不保留 path）
- 在 `keywords` 中增加 “v2/新版/升级/废弃/旧版”等提示性词汇，帮助识别与人工校验

#### 3) 变更 path 时同时兼容新旧命中

建议：
- 将旧 `path` 以关键字形式保留（或保留旧 path 的第一段分组），让历史需求文本仍可命中
- 如果旧 path 完全下线且容易误命中，可逐步移除旧 path 关键字

#### 4) 系统级升级（整体版本迁移）

当系统整体升级（例如从 `v1` 网关迁移到 `v2` 网关），且大量 API 受影响：
- 优先批量更新 `path`（或增加新 path 关键字）而不是改动大量 `id`
- 如果需要区分新旧系统（例如两个系统并存），再考虑新增一个系统 `id`（如 `XXX_SYS_V2`）

### 通过大模型对话维护清单

当你需要批量新增/重构依赖清单（尤其是 API 数量较多时），可以用大模型做“结构化编辑”，但要控制输出严格满足本项目的 JSON 结构。

建议流程：

1) 准备输入材料
- 当前 `index.json`（或目标系统的 `*.apis.json`）
- 变更说明（新增系统/新增 API/接口升级说明/废弃说明等）
- 如果有 Swagger/OpenAPI 文档：提供原始 `openapi.json/yaml` 或链接/导出文件内容

2) 给大模型明确约束
- 只输出严格 JSON（不要 Markdown，不要说明文字）
- 必须保留既有字段结构（系统 id、API id 的稳定性规则见上文）
- 不允许凭空编造系统/接口（除非你明确要求新增）
- 每个 API 至少包含：`id/name/method/path/keywords`（method/path 可为空但建议补齐）

3) 推荐的对话指令模板

用于更新某个系统的 API 文件：
- 目标文件：`<work_dir>/input/dependencies/<SYS_ID>.apis.json`
- 指令示例：
  - “请基于下面的 Swagger(OpenAPI) 文档，生成 `<SYS_ID>.apis.json` 的 apis 数组。要求：method/path/name 必填，keywords 至少 3 个，keywords 要覆盖业务用词与旧版路径；如果接口为 v2 版本，在 keywords 里包含 v2/新版/升级；只输出 JSON。”

用于更新 index.json 的 systems 元信息：
- 指令示例：
  - “请在 `index.json` 中新增系统 REALNAME_AUTH，并补充 aliases/keywords/description，保持 systems 数组其余对象不变，只输出 JSON。”

4) 输出后的人工复核重点
- system `id` 是否稳定、无重复
- API `id` 是否稳定、无重复（同一系统内唯一）
- method/path 是否正确（尤其是 GET/POST/PUT/DELETE 与路径前缀）
- keywords 是否覆盖需求常用词（中文/英文/缩写/旧称）

### 通过 Swagger/OpenAPI 更新最新 API

如果外部系统提供 Swagger/OpenAPI 文档（OpenAPI 3.x 或 Swagger 2.0），建议用其作为“权威来源”更新 API 清单，保持与真实接口同步。

推荐做法：

1) 获取 OpenAPI 文档
- 若系统提供在线文档：通常可从 `/v3/api-docs`、`/openapi.json`、`/swagger.json` 等地址导出
- 若只能在平台下载：下载 `openapi.json` 或 `openapi.yaml`

2) 选择映射规则
- `path`：来自 OpenAPI paths 的 key（例如 `/realname/verify`）
- `method`：来自 http method（GET/POST/...）
- `name`：优先用 `summary`，其次用 `operationId`，最后用 `description` 的首行
- `id`：优先用 `operationId`；如果没有 operationId，则用“METHOD + PATH”做稳定映射（并做可读化处理）
- `keywords`：
  - 包含 `name` 的分词要点
  - 包含 path 的关键片段（尤其是第一段分组）
  - 结合 tag/summary 中的业务词补充 3~8 个

3) 增量升级建议
- 新增接口：直接新增到 `apis`
- 删除接口：建议先标记为“旧版/废弃”关键词并保留一段时间，再删除（避免历史文档无法命中）
- path 变更：保留旧 path 作为 keywords 一段时间，确保历史命中

4) 与本项目结构对齐
- 更新后的结果应落在对应系统的 `*.apis.json`，并通过 `index.json` 的 `api_file` 引用
- 若系统只有极少量 API，可选择内嵌到 `index.json` 的 `apis` 字段，但不推荐对大型系统这样做

### 维护后检查清单

完成修改后，建议进行以下快速验证：
- Web：打开“依赖列表”，用系统名/ID/关键词搜索，确认可找到并能展开 API
- Web：上传一段包含关键字的需求文本进行识别，确认命中系统与 API
- 输出：检查 `work/output/<scan_id>/` 下的 `*.module_deps.json` 与 `*.module_deps.xlsx` 是否符合预期

### 常见问题

#### 为什么新增了 API 但识别不到？

通常原因：
- `keywords` 覆盖不足（需求文本里没有出现 `name/path/keywords` 的关键字）
- 系统/接口命名与需求用词不一致（补充 `aliases/keywords`）
- 需求描述是内部模块而非外部依赖（应避免误把内部模块识别成外部系统）
