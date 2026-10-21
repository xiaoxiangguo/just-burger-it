# workbuddy.md — 麦门汉堡搭建器 · WorkBuddy 开发上下文

> 本文件为参赛作品「麦门汉堡搭建器」（定制专属于你的麦门汉堡🍔）在腾讯 WorkBuddy 中完成创意构思、数据实测与开发全过程的对话上下文摘要。
> 导出时间：2026-10-21（北京时间）

## 会话概况

| 项 | 内容 |
|---|---|
| 工具 | 腾讯 WorkBuddy（Agent 模式） |
| 日期 | 2026-10-21 |
| 主题 | 麦当劳程序员创意开发大赛 · 选题调研与项目开发 |
| 产出 | 汉堡搭建器应用 + 数据管道 + 参赛材料 |

## 关键对话节点

### 1. 赛事情报梳理
- 解析活动仓库与活动规则，确认报名截止 2026-10-25 23:59、按 GitHub Star 排名、前 100 名获奖
- 确认必需交付文件：README.md / CONTEST_DECLARATION.md / MCP_INTEGRATION.md / mcp-config.example.json / workbuddy.md

### 2. 竞品与赛道分析（基于排行榜与 200 条报名 Issue 实测）
- 抓取官方 RANKING.md（2026-10-21 11:00 更新）：100 个项目上榜，第 1 名 812 星，第 100 名 23 星
- 抓取活动 Issue 列表（约 200 条，其中规范参赛申请约 162 条），按主题归类：
  - 省钱/优惠/凑单 ~30 个（最大红海，头部 800+ 星）
  - 点餐推荐/全能助手 ~30 个（同质化最严重）
  - 游戏/娱乐/人格化 ~15 个（跑出来的都是「测验/占卜/认证」轻互动形态）
  - 营养健康 ~12 个，派对组局 ~10 个，周边/联名仅 3 个（最冷门）
- 逐方向实测竞品 Star：麦麦消消乐 3 星、3D 食材连消 0 星、联名馆 17 星、限定黄金眼 2 星、麦卡收藏家 5 星
- 结论：Star 转化依赖「真实 MCP 数据 + 人格化 + 可分享产出」；功能型工具已饱和，汉堡自定义为空白位

### 3. 技术可行性验证（MCP 实测）
- 在 WorkBuddy 中确认需求：用户要的是「面包/蔬菜/肉逐层自选的专属汉堡」，产出希望是漫画风或实物风剖面图
- 编写 `tools/mcp_probe.py`（Streamable HTTP + JSON-RPC，纯标准库），实测结论：
  - 服务端为无状态模式（不返回 session id），每次请求需带 initialize
  - Token 可用，枚举到 35 个 Tool
  - `list-nutrition-foods` 返回 158 项官方营养数据
  - `query-meal-detail` 的 `data.modification.items` 是**食材级特调配料清单**（17 种配料），构成组件库的真实来源
  - 官方不售卖原料 SKU，逐层自选只能做「虚拟搭建 + 营养估算」，不能真实下单 → 据此确定产品形态为创意型搭建器
- 用官方营养表差值法反推单食材热量（牛肉饼 135 kcal、安格斯厚牛饼 307 kcal、吉士片 46 kcal），并在前端区分「官方差值/推算/创意」三种口径

### 4. 开发与验证
- 产出 `data/components.json`（初版 5 类 34 个组件、10 款真实产品指纹；对照官方菜单补表后为 **37 个组件、16 款产品指纹**）
- 产出 `index.html`：漫画风 SVG 剖面图（粗描边/芝麻粒/烤痕/芝士垂坠/生菜褶皱/蒸汽）、营养主视觉（大号热量 + 每日占比环 + 三大营养素能量占比条 + 钠预警）、相似度彩蛋、出餐卡导出
- 用 Node + DOM stub 执行页面渲染逻辑做无头验证：默认汉堡识别为「麦辣鸡腿汉堡 100%」、随机组合渲染正常、SVG 几何无越界

### 5. 形态确认与运行时 MCP 补强
- 用户确认官方「Skill」定义包含「应用程序」，H5 形态合规；但为满足「须真实使用麦当劳 MCP 能力」，补充了运行时调用链路：
  - `skill/SKILL.md` + `skill/scripts/burger.py`：可安装技能，运行时 query-nearby-stores → query-meals → query-meal-detail 校验门店在售
  - `tools/live_proxy.py` + H5「实时模式」：本地代理转发，门店缺货食材自动灰显
- 实测：CLI 对深圳桂庙路餐厅校验 6 层食材全部在售；代理返回 soldOut 7 项（全部为创意层）
- 视觉迭代：按用户反馈重绘剖面图（原版"难看"）、营养面板升级为 hero 区（原版"不够突出"）

## 复现提示

- 数据管道：`tools/README.md`
- MCP 集成说明：`MCP_INTEGRATION.md`
- 应用本身零依赖，`python3 -m http.server` 即可运行

## 可核验点（本次会话的结论如何被独立复现）

| 会话中的结论 | 核验方式 |
|---|---|
| MCP 为无状态模式、共 35 个 Tool、`serverInfo` 为 mcd-mcp 1.0.0 | `python3 tools/mcp_probe.py list-tools` |
| 官方营养表 158 项 | `data/nutrition.json`、存档 `tools/raw/nutrition.json` |
| 门店菜单 122 个商品、15 个分类 | 存档 `tools/raw/meals.json` |
| 11 款汉堡可拉取 `modification` 食材级配料（汇总 17 种） | 存档 `tools/raw/burger_details.json`、`data/mod_items.json` |
| 运行时确实调用 MCP 校验门店在售 | `python3 skill/scripts/burger.py build --bun sesame --patty spicychicken --veg choppedlettuce --sauce chickensauce --live --city 深圳市 --keyword 南山` |
| 组件库自洽（37 个组件 / 16 款产品指纹，热量偏差 ≤ ±20%） | `python3 tools/validate_components.py` |

以上每一条命令都在本仓库内可独立执行，不依赖会话记录本身。
