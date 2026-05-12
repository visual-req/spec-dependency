# Troubleshooting

## 新增系统/新增 API 失败，或新增后页面看不到

### 1) 先确认你改的是哪一份依赖清单

本项目读取的依赖清单来自运行时配置的 `work_dir`：
- 入口：`<work_dir>/input/dependencies/index.json`
- API 文件：`<work_dir>/input/dependencies/<SYSTEM_ID>.apis.json`

如果你启动时加载了错误的配置文件，可能会写到另一个 work 目录，导致页面看起来“没有变化”。可用接口确认当前生效配置：
- `GET /api/config`：查看 `work_dir` 与 `config_path`
- `GET /api/dependencies`：返回当前读取的 `index.json` 路径（file 字段）

### 2) 检查是否被“标记删除”隐藏了

系统或 API 如果被设置了 `deleted: true`，默认不会出现在识别与依赖列表中。
- 在“依赖列表”页勾选“显示已删除”查看原始数据
- 系统维护抽屉里取消“标记删除”后保存

### 3) 维护页面保存失败

常见原因：
- 服务端没有写权限：`<work_dir>/input/dependencies/` 不可写
- JSON 写入冲突：同一时间多人/多进程同时写

可通过日志定位：
- `<work_dir>/logs/spec_dep.log.jsonl` 中搜索 `save_dependency_system` / `import_deps_excel` / `import_swagger`

### 4) Excel 导入失败（AI 识别层级）

Excel 导入依赖 AI 能力：
- 需要配置 `DEEPSEEK_API_KEY`（`GET /api/config` 的 `deepseek_api_key_present` 必须为 true）

表格“相对自由”但仍建议：
- 明确列名：系统、接口、method、path、入参、出参、备注等
- 避免把多个系统的 API 混在同一块无分隔区域（尽量按 sheet 或分组行区分）

### 5) Swagger/YApi 导入失败

#### 网络不可达/内网/VPN
导入是“服务端发起请求”，需要服务所在机器能访问该 URL。

#### 需要 token
在导入抽屉填写：
- token
- header（默认 Authorization）
- scheme（Bearer/Raw）

#### 批量导入 + 断点续传
可在抽屉填写：
- 批量 URL 列表（每行一个 URL 或上传 txt）
- resume_key（断点续传 key）

同一 `resume_key` 再次提交会跳过已成功导入的 URL，避免反复访问。

### 6) 新增了 API 但“识别依赖”命中率很低

识别依赖主要依赖 `name/keywords/path` 命中：
- 为 API 补齐 `keywords`（覆盖业务常用词、别名、旧路径片段）
- 确保 `path` 与真实接口一致
- 若系统名在需求中有别称，补充到系统 `aliases/keywords`

