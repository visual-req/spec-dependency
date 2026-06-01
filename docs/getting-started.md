## Getting Started

### 1. 准备 work 目录

目录约定：
- `work/input/req`：需求文档（.doc/.docx）
- `work/input/dependencies`：外部系统清单 JSON
- `work/output`：输出（JSON + XLSX）
- `work/logs`：日志（前端/后端 JSONL）

如目录不存在，可手动创建上述目录结构。

### 2. 准备配置文件

通过环境变量 `SPEC_DEP_CONFIG` 指定配置文件路径（例如 `./config.yaml`）。

### 3. 启动服务

```bash
SPEC_DEP_CONFIG=./config.yaml python -m backend.app.cli.main web --host 127.0.0.1 --port 8766
```

### 4. 使用页面

打开终端输出的 URL，进入：
- 识别依赖：上传需求文件并开始识别
- 依赖列表：查看外部系统与 API 清单（点击 API 数打开抽屉）

更多使用说明见：
- docs/manual.md
