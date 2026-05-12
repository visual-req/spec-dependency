## CLI

### 扫描需求文件

```bash
cd backend
PYTHONPATH=. python -m app.cli.main scan -req ../work/input/req
```

常用参数：
- `-req`：需求文件或目录（必填）
- `--deps`：依赖清单入口文件（可选；不填则默认使用 `work/input/dependencies/index.json`，若不存在则选择目录下第一个 json）
- `--out`：输出目录（可选；不填则输出到 `work/output`）

输出：
- `*.module_deps.json`
- `*.module_deps.xlsx`
