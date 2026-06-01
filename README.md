## spec_dep

用于从需求文档中识别“外部依赖”（外部系统 / 外部 API），并把结果落盘为 JSON + Excel，提供 Web UI 便于浏览、搜索、二次调整。

### 你可能想从这里开始

- 只想跑起来：看 [快速开始](#快速开始)
- 想了解页面怎么用：看 [docs/manual.md](docs/manual.md)
- 想维护外部依赖清单（系统/接口/升级）：看 [docs/maintenance.md](docs/maintenance.md)
- 想从 Swagger/OpenAPI 准备清单：看 [docs/preparation.md](docs/preparation.md)
- 想跑 CLI 批量扫描：看 [docs/cli.md](docs/cli.md)

## 快速开始

### 1) 准备配置文件（推荐）

准备一个配置文件（例如 `config.yaml`）。

配置项说明见 [docs/manual.md](docs/manual.md)（包含 `server` / `work_dir` / `llm`）。

### 2) 启动服务

```bash
python -m backend.app.cli.main web --host 127.0.0.1 --port 8766
```

启动后访问：
- http://127.0.0.1:8766/

如需显式指定配置文件：

```bash
python -m backend.app.cli.main /path/to/config.yaml web --host 127.0.0.1 --port 8766
```

## 目录结构

工作目录由配置项 `work_dir` 决定，典型结构：
- `work/input/dependencies/`：外部依赖清单（index.json + 各系统 *.apis.json）
- `work/input/req/`：待扫描的需求文档（可选，CLI 常用）
- `work/output/<scan_id>/`：每次扫描的输出（scan.json、每个文件的 *.module_deps.json/*.xlsx）
- `work/logs/`：运行日志

## 外部依赖清单维护

- 清单入口：`<work_dir>/input/dependencies/index.json`
- 系统 API 文件：`<work_dir>/input/dependencies/<SYSTEM_ID>.apis.json`
- API 升级/兼容策略、大模型对话维护、Swagger/OpenAPI 更新流程：见 [docs/maintenance.md](docs/maintenance.md)

## Web 功能概览

Web UI 分为两页：
- 识别依赖：上传需求文件后识别，结果支持列表展示、分页、简略/详细模式、AI 二次调整、Excel 下载
- 依赖列表：浏览/搜索外部系统与 API 清单

使用细节见 [docs/manual.md](docs/manual.md)。

## 文档导航

- 安装： [docs/installation.md](docs/installation.md)
- 入门： [docs/getting-started.md](docs/getting-started.md)
- 使用手册： [docs/manual.md](docs/manual.md)
- 依赖清单准备： [docs/preparation.md](docs/preparation.md)
- 清单维护（含 API 升级与 Swagger/OpenAPI 更新）： [docs/maintenance.md](docs/maintenance.md)
- CLI： [docs/cli.md](docs/cli.md)
- 工作流： [docs/workflow.md](docs/workflow.md)
- 结构说明： [docs/structuer.md](docs/structuer.md)
