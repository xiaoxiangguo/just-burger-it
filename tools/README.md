# tools/ — 数据管道（可复现）

本项目前端是纯静态应用，所有数据通过麦当劳中国 MCP Server 一次性实测获取并烘焙进 `data/`。
本目录提供完整的数据管道，任何人可重跑验证。

## 前置条件

1. 到 [麦当劳 MCP 开放平台](https://open.mcd.cn/mcp) 申请 MCP Token（免费，手机号登录）
2. 设置环境变量：

```bash
export MCD_TOKEN="你的MCP_TOKEN"
```

## 复现步骤

```bash
# 1. 连通性测试：枚举 35 个官方工具
python3 mcp_probe.py list-tools

# 2. 拉取官方营养表（158 项）
python3 mcp_probe.py call list-nutrition-foods > raw/nutrition.json

# 3. 查询门店（示例：深圳南山，到店自提）
python3 mcp_probe.py call query-nearby-stores \
  '{"beType":1,"searchType":2,"city":"深圳市","keyword":"南山"}' > raw/stores.json

# 4. 拉取门店菜单（用上一步返回的 storeCode）
python3 mcp_probe.py call query-meals \
  '{"storeCode":"1420207","orderType":1,"beType":1}' > raw/meals.json

# 5. 逐个拉取 11 款汉堡的组成与特调配料（见 build_components.py 逻辑）
#    query-meal-detail {"storeCode":"1420207","orderType":1,"beType":1,"code":"<汉堡编码>"}

# 6. 烘焙组件库
python3 build_components.py
```

## 文件说明

| 文件 | 作用 |
|---|---|
| `mcp_probe.py` | 极简 MCP 客户端（纯 Python 标准库，Streamable HTTP + JSON-RPC 2.0，无状态模式：每次请求携带 initialize + 调用） |
| `build_components.py` | 解析 MCP 原始响应 → `data/nutrition.json` + `data/mod_items.json`，并打印特调配料宇宙 |
| `sync_skill_data.py` | 把 `data/components.json` 与 `tools/mcp_client.py` 同步进 `skill/`，保证技能目录可独立安装；`--check` 只校验 |
| `raw/` | MCP 原始响应存档（2026-10-21 实测，不含任何凭证） |

## 注意事项

- Token 限流 600 次/分钟，脚本内已加 0.3s 间隔
- 请勿把 Token 写进任何文件或提交到仓库
- 门店数据随时间变化，重跑时营养表/菜单可能与存档略有差异
