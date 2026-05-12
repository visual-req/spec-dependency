## 工作流

### 1) 维护外部系统清单

编辑：
- `work/input/dependencies/index.json`（入口文件）
- `work/input/dependencies/<SYSTEM_ID>.apis.json`（各系统 API 列表）

清单获取与完善：
- 从 Excel 整理系统与 API（推荐）
- 从 Swagger/OpenAPI 文档提取 endpoints（method/path/summary/tags）
- 从网关路由/后端代码提取 endpoint，再人工补齐关键词

详细说明见：
- docs/preparation.md

结构要点：
- 顶层：`{ "systems": [ ... ] }`
- system：`id / name / type / aliases / keywords / api_file`
- api：`id / name / method / path / keywords`

### 2) 放入需求文档

将 `.doc/.docx` 放到：
- `work/input/req/`

### 3) 识别依赖

方式 A：Web 上传识别
- 页面点击“开始识别”

方式 B：CLI 扫描
- `python -m app.cli.main scan -req work/input/req`

解析过程（核心逻辑）：
- 从需求文档提取文本
- 按模块拆分文本（模块标题/章节）
- 使用系统名/别名/关键词与 API 关键词/path 对文本做命中，得到模块 -> 系统 -> API 的映射

### 4) 查看产物与日志

- 输出：`work/output/*.module_deps.json`、`work/output/*.module_deps.xlsx`
- 日志：`work/logs/spec_dep.log.jsonl`
