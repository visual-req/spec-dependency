## Getting Started

### 1. 准备 work 目录

初始化目录（可选）：

```bash
./executable/init_work.sh
```

Windows：

```bat
.\executable\init_work.bat
```

目录约定：
- `work/input/req`：需求文档（.doc/.docx）
- `work/input/dependencies`：外部系统清单 JSON
- `work/output`：输出（JSON + XLSX）
- `work/logs`：日志（前端/后端 JSONL）

### 2. 准备配置文件

配置文件通过环境变量 `SPEC_DEP_CONFIG` 指定。

默认配置文件位置：
- `executable/config.yaml`

### 3. 启动服务

```bash
SPEC_DEP_CONFIG=./executable/config.yaml ./executable/start.sh web
```

或指定配置路径（自定义）：

```bash
SPEC_DEP_CONFIG=/path/to/config.yaml ./executable/start.sh web
```

Windows：

```bat
.\executable\start.bat web
```

如果需要指定 config：

```bat
set SPEC_DEP_CONFIG=C:\path\to\config.yaml
.\executable\start.bat web
```

### 4. 使用页面

打开终端输出的 URL，进入：
- 识别依赖：上传需求文件并开始识别
- 依赖列表：查看外部系统与 API 清单（点击 API 数打开抽屉）

更多使用说明见：
- docs/manual.md
