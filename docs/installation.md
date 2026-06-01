## 安装

### 运行环境

- macOS / Linux / Windows
- Python 3.11+（建议使用虚拟环境）

### Python 依赖

后端依赖安装（示例）：

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### 系统依赖（解析 .doc）

如果需要解析 `.doc`（非 `.docx`），需要 `antiword`。

- macOS（Homebrew）：

```bash
brew install antiword
```

### 前端说明

运行时页面使用 `frontend/dist/index.html`，由后端作为静态文件返回。
