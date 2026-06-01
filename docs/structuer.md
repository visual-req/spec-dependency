## structure

```text
spec_dep/
  backend/
    app/
    tests/
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
- `work/`：运行时输入/输出/日志目录约定
- `frontend/dist/`：运行时页面（无需重新构建也能直接改 `dist/index.html`）
