## structuer

```text
spec_dep/
  backend/
    app/
    tests/
  executable/
    config.yaml
    init_work.sh
    init_work.bat
    start.sh
    start.bat
    run.sh
  frontend/
    dist/
  work/
    input/
      req/
      dependencies/
    output/
    logs/
    uploads/
```

说明：
- `executable/`：可执行脚本与默认配置
- `work/`：运行时输入/输出/日志目录约定
- `frontend/dist/`：运行时页面（无需重新构建也能直接改 `dist/index.html`）
