## Concept

### 目标

从需求文档中识别“外部依赖”（外部系统 / 外部 API），并将识别结果以可复用的数据结构落盘，便于：
- 浏览与检索
- 二次调整（AI 指令编辑）
- 导出交付（JSON / Excel）
- 维护外部依赖清单（系统与 API）

### 关键对象

- 外部依赖清单（Dependency Catalog）
  - 入口：`<work_dir>/input/dependencies/index.json`
  - 每个系统的 API：`<work_dir>/input/dependencies/<SYSTEM_ID>.apis.json`
  - 作用：限定“可被识别/可被选择”的外部系统与 API，避免模型臆造

- 扫描结果（Scan Result）
  - 位置：`<work_dir>/output/<scan_id>/scan.json`
  - 作用：记录一次识别的完整结果（按文件 → 模块 → 依赖系统 → API）

### 基本流程

1. 准备外部依赖清单（系统与 API）
2. 上传需求文档/指定需求文件
3. 进行依赖识别并生成 `scan.json`
4. 在页面中浏览结果、下载导出
5. 如需提升质量：对 `scan.json` 进行 AI 二次调整（生成 `scan.adjusted.json`）
6. 如需完善清单：在“依赖列表”中维护系统信息与 API 列表（会写回 dependencies JSON）

### 数据结构（概念层级）

结果以“逐级收敛”的结构组织：
- 文件（File）：对应一份需求文档
- 模块（Module）：需求中的功能模块/业务域（属于当前系统内部）
- 外部系统（Dependency System）：模块需要对接的外部系统
- 外部 API（API）：对外部系统的具体调用能力点（method/path/name 等）

### 维护边界

- “模块”属于被分析系统的内部结构；“外部系统/API”来自依赖清单。
- 识别与二次调整原则上只能从依赖清单中选择系统/API，除非你明确希望引入新系统或新 API。

