# MCP Integration — 麦门之搭了个堡

> 麦门信徒，要吃属于自己的汉堡🍔

本文档说明本项目如何**在运行时真实使用**麦当劳中国 MCP Server（`https://mcp.mcd.cn`），包含两条调用路径：Skill 实时路径与 H5 实时模式路径。

## 1. 使用的 MCP Server

| 项 | 值 |
|---|---|
| Server | `mcd-mcp` v1.0.0（麦当劳中国官方） |
| 接入地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP（JSON-RPC 2.0，无状态模式） |
| 鉴权 | `Authorization: Bearer <MCP_TOKEN>` |

## 2. 实际调用的 Tools

| Tool | 调用入参 | 用途 | 获取的数据 |
|---|---|---|---|
| `list-nutrition-foods` | 无 | 官方营养表 | 158 项餐品的能量(kJ/kcal)、蛋白质、脂肪、碳水、钠、钙 |
| `query-nearby-stores` | `beType=1, searchType=2, city=深圳市, keyword=南山` | 查询到店自提门店 | storeCode（示例门店 1420207） |
| `query-meals` | `storeCode=1420207, orderType=1, beType=1` | 门店在售菜单 | 15 个分类、122 个商品的编码/名称/图片/价格 |
| `query-meal-detail` | `storeCode, orderType=1, beType=1, code=<汉堡编码>` | 汉堡组成与特调 | 11 款汉堡的 `modification.items`（17 种官方食材级配料，含可加/减与数量上限） |

## 3. 调用流程

```
list-nutrition-foods ─────────────────────────► data/nutrition.json (158项官方营养)
                                                      │
query-nearby-stores → query-meals ────────────► 单品汉堡编码清单 (11款)
                                                      │
query-meal-detail × 11 ───────────────────────► modification 配料宇宙 (17项)
                                                      │
                                        tools/build_components.py
                                                      ▼
                                       data/components.json (烘焙进前端)
                                                      ▼
                                  index.html 快照模式（零Token、零后端）
```

### 运行时实时调用（合规关键）

除了一次性烘焙，本项目**运行时同样直接调用 MCP**，两条入口各自独立可验证：

**① Skill 入口**（`skill/scripts/burger.py`）

```
用户请求 "搭一颗麦辣培根堡，看看我门店有没有"
        │
        ▼
query-nearby-stores(city, keyword)  ──► 选定门店 storeCode
        │
        ▼
query-meals(storeCode)              ──► 当前在售 122 个商品
        │
        ▼
逐层比对在售产品与特调配料  ─────────► ✓ 在售可搭 / ✗ 本店未见在售
        │
        ▼
本地组件库核算营养 + 相似度 ────────► 终端剖面图 + 营养报告
```

**② H5 实时模式**（浏览器 → `tools/live_proxy.py` → MCP）

```
[浏览器] 填入 Token + 城市 + 商圈
        │  POST /api/live-menu
        ▼
[本地代理 127.0.0.1:8787]  ──► find_stores → fetch_menu → 匹配在售
        │
        ▼
{storeName, burgers, onSaleReal:[产品名...], unlisted:[菜单有但未收录...], soldOut:[componentId...]}
        │
        ▼
[浏览器] 门店缺货的食材直接灰掉，标「本店暂未售」；
         相似度 Top3 逐个标「本店在售 / 本店不售」；
         本店菜单里未收录的汉堡单独提示
```

> 浏览器不能直连 `mcp.mcd.cn`（CORS 与 Token 暴露风险），因此实时模式经由本地代理转发；
> 代理为纯标准库实现，Token 逐请求传入、仅内存使用、不落盘、不上传。
>
> **为什么同步门店时不去改 `components.json`**：产品配方是产品属性，不是门店属性
> （巨无霸在深圳和北京是同一颗），真正随门店变的只是「卖不卖它」。所以组件库保持全局，
> 门店差异通过 `onSaleReal` / `soldOut` 在运行时叠加。

### 关键发现（本项目的数据护城河）

麦当劳 MCP Server（`serverInfo: mcd-mcp v1.0.0`，2026-10-21 实测）提供食材级定制能力：`query-meal-detail` 返回的
`data.modification.items[].values[]` 就是**官方真实存在的特调配料清单**，
例如芝士安格斯厚牛堡支持：醇香芝士风味酱、高达干酪片、番茄片、黄油（最多选 4 项）。

本项目把 11 款汉堡的特调配料做了全量汇总，构成「麦门之搭了个堡」的食材宇宙——
**每一层食材都不是编的，都是官方接口真实支持的配料**。

> 关于「11 款」与「16 款」的口径差异：11 是指拉到了 `query-meal-detail` 详情（含 modification）的汉堡，
> 原始响应存档在 `tools/raw/burger_details.json`；16 是指参与相似度比对的官方产品总数，
> 其中 5 款（巨无霸、麦香鱼、麦香鸡、汉堡包、吉士汉堡包）没有拉到详情，由菜单返回的商品名与
> 官方公开组成手工整理成指纹，**只用于相似度计算，不引入任何额外营养数据**。
> 两者用途不同，不冲突。

### 营养差值推算方法

MCP 不提供单食材营养，本项目用官方营养表做线性差值：

- 经典牛肉饼 = 双层吉士汉堡(429 kcal) − 吉士汉堡包(294 kcal) = **135 kcal**
- 安格斯厚牛饼 = 芝士双层安格斯(1003 kcal) − 芝士安格斯厚牛堡(696 kcal) = **307 kcal**
- 吉士片 = 吉士汉堡包(294 kcal) − 汉堡包(248 kcal) = **46 kcal**

无法做差值的食材（蔬菜/酱料）以官方数据为锚估算，前端以颜色徽标区分三种口径
（官方差值 / 推算 / 创意），不冒充精确数据。

## 4. 业务价值

1. **解决真实问题**：麦当劳官方 App 不提供"自由组合汉堡"的想象空间，本项目给了麦门用户一个可玩、可分享的创意出口
2. **营养科普**：搭一颗汉堡的过程 = 直观理解每一层的热量来源，比翻营养表有效
3. **数据驱动的内容生成**：相似度算法反向用作「原创度」——基于官方真实产品组成算出你离官方有多远，越远越值得炫耀
4. **实时库存感知**：把「门店今天有没有这个食材」变成可玩的信息，官方层与创意/传说层自动区分
5. **可复现的数据管道**：`tools/` 目录提供从 MCP 拉数到烘焙前端的完整脚本，任何人可重跑验证

## 5. 合规说明

- 仓库不含任何真实 MCP Token / 账号凭证（配置见 [mcp-config.example.json](mcp-config.example.json)，仅环境变量占位符）
- 数据仅做只读查询（`query-meal-detail` 等均为查询类工具），不涉及下单/支付/积分等写操作
- 数据采集于 2026-10-21，仅用于本项目的静态展示；遵守麦当劳 MCP 服务规则（600 次/分钟限流内使用）
