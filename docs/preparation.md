## Preparation

### 目标

把“外部依赖清单”维护成可复用的数据资产，供识别时匹配模块 -> 外部系统 -> API。

### 目录与文件约定

外部依赖清单放在：
- `work/input/dependencies/`

支持多份 JSON，入口固定为：
- `work/input/dependencies/index.json`

建议按“系统维度”拆分 API 文件，便于维护：
- `work/input/dependencies/<SYSTEM_ID>.apis.json`

#### index.json（入口文件）

示例结构：

```json
{
  "systems": [
    {
      "id": "PAY_ALIPAY",
      "name": "支付宝",
      "type": "external_platform",
      "aliases": ["Alipay", "支付宝"],
      "keywords": ["支付", "退款"],
      "api_file": "PAY_ALIPAY.apis.json"
    }
  ]
}
```

字段说明：
- `id/name/type`：系统基础信息
- `aliases/keywords`：用于识别时做命中
- `api_file`：该系统 API 列表文件（相对 `index.json` 所在目录）

#### <SYSTEM_ID>.apis.json（系统 API 列表）

示例结构：

```json
{
  "system_id": "PAY_ALIPAY",
  "apis": [
    {
      "id": "ALIPAY_PAY_CREATE",
      "name": "创建支付",
      "method": "POST",
      "path": "/v1/pay",
      "keywords": ["下单", "创建支付"]
    }
  ]
}
```

### 从 Excel 准备清单

推荐 Excel 列：
- 系统：`system_id / system_name / system_type / aliases / keywords`
- API：`api_id / api_name / method / path / keywords`

做法：
1) 先把系统层信息整理为 `index.json`
2) 再按 `system_id` 分组，把每个系统的 API 生成成 `<SYSTEM_ID>.apis.json`
3) 在 `index.json` 里为系统写上 `api_file`

### 从 Swagger/OpenAPI 文档获取

常见来源：
- Swagger UI 导出的 OpenAPI JSON/YAML
- 后端仓库中的 `openapi.json` / `swagger.json`
- 在线文档接口（API）直接获取 OpenAPI

建议步骤：
1) 解析 `paths`，得到每个 endpoint 的 `method` 和 `path`
2) 取 `summary/operationId/tags` 等作为 `name/keywords` 补充
3) 按业务域/网关/系统边界把 endpoints 归并到某个 `system_id`
4) 输出到对应 `<SYSTEM_ID>.apis.json`

常见在线获取地址（不同框架会有差异）：
- SpringDoc(OpenAPI 3)：`/v3/api-docs`、`/v3/api-docs/{group}`、`/v3/api-docs.yaml`
- Swagger 2：`/v2/api-docs`、`/swagger.json`
- 网关聚合文档：通常会有统一的 `api-docs` 聚合入口（需要按网关实际配置确认）

### 其它来源

- 网关路由表：按服务/域名聚合后生成 API 列表
- 代码扫描：从 Controller/Router 定义提取 method/path，再人工补齐 name/keywords
