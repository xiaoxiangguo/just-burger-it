# 🍔 麦门之搭了个堡

> **定制专属于你的麦门汉堡🍔**

![License](https://img.shields.io/badge/license-MIT-green) ![MCP](https://img.shields.io/badge/data-McDonald's%20China%20MCP-red) ![1024](https://img.shields.io/badge/1024-程序员节-yellow)

<p align="center">
  <img src="docs/screenshots/01-default.png" width="49%" alt="默认页面">
  <img src="docs/screenshots/02-custom.png" width="49%" alt="自选配方页面">
</p>

<p align="center"><sub>左：默认配方「量子麦辣鸡腿堡」 · 右：自选配方「黄金麻辣香锅巨堡」——麻辣香锅饼为传说层（虚线 + 星点），原创度 68% · 图为真实页面截图</sub></p>

<p align="center">
  <img src="docs/screenshots/03-wishcard.png" width="30%" alt="许愿卡">
  <img src="docs/screenshots/04-sync-modal.png" width="33%" alt="同步门店弹窗">
  <img src="docs/screenshots/05-sync-done.png" width="33%" alt="同步成功">
</p>

<p align="center"><sub>许愿卡（编号 + 专利号 + 建议零售价） · 实时同步门店在售食材——真实调用麦当劳 MCP（示例：深圳桂庙路餐厅 · 在售汉堡 14 款 · 不可用食材 7 项）</sub></p>

<p align="center">
  <img src="docs/screenshots/06-synced.png" width="49%" alt="同步后的主页面">
</p>

<p align="center"><sub>同步后：本店没有的食材自动灰化标「本店暂未售」，官方产品标注「本店在售 / 本店不售」，顶部出现实时徽标</sub></p>

一个基于麦当劳中国 MCP Server 的**汉堡搭建技能 + H5 搭建器**：面包选什么、肉选什么、蔬菜酱料怎么叠，你说了算；每一层的热量都来自**麦当劳官方营养数据**。

## 两种形态，一套能力

| 形态 | 是什么 | 适合 |
|---|---|---|
| **Skill 真身**（`skill/`） | 可安装技能，运行时实时调用 MCP：查门店 → 拉菜单 → 校验特调食材 → 核算营养 → 输出终端剖面图 | 在 WorkBuddy / Claude 等支持 Skill 的客户端里直接用 |
| **H5 门面**（`index.html`） | 漫画风剖面图搭建器，点选即搭、实时营养面板、自动命名、许愿卡导出 | 演示、传播、朋友圈晒图 |

两者共用同一份组件库与营养口径，数据同源。

## 能玩什么

- 🍞 **5 类 61 个组件**：官方 30 个（差值 7 + 推算 23，来自在售产品与官方「特调」配料清单）+ 创意 7 个（火鸡面、鲜虾、墨鱼包…）+ **传说 24 个**（榴莲、螺蛳粉、整只龙虾、老干妈、珍珠奶茶酱…）
- ✍️ **报菜名**：想吃的东西库里没有？直接打字加一层，选个类别，热量按同类食材粗估，标「传说」
- 🔥 **官方营养背书**：热量、蛋白质、脂肪、碳水、钠；总热量以大号数字 + 每日推荐占比环呈现
- 🎨 **漫画风剖面图**：粗描边、双色明暗、芝麻粒、烤痕、芝士垂坠、生菜褶皱、蒸汽线条；**传说层画成虚线 + 星点**，一眼看出「这不是真食材」
- 🏷️ **原创度（相似度的反向用法）**：对 16 款官方产品做「按层计数 + 分类加权」比对。低于 40% 不再安慰你说「最接近谁」，而是直接给**原创度**和「官方离你最近的一款差 N 层」——越不像官方，越值得炫耀
- 🎭 **自动命名 + 麦门人格 + 荒诞档案**：配方指纹哈希生成稳定的中二堡名（例：`午夜螺蛳粉巨堡`），配一个人格词条（`嗜辣狂徒` `芝士信徒` `甜咸党`…），再算危险等级、≈几碗米饭、≈要跑几公里
- 🙏 **许愿卡**：编号 NO.xxxx、配方专利号、建议零售价（玩笑）、一句许愿语，PNG 导出
- 🔗 **实时模式**：填入自己的 Token，实时调用 MCP 判断**你所在门店今天有没有这些食材**，没有的直接灰掉；同时给官方产品标注「本店在售 / 本店不售」
- 🎲 **乱搭**：选择困难症一键随机（会随机到传说食材）

> 传说层是「许愿项」：官方菜单没有、现实里也没有，热量按同类食材粗估。别当真，当乐子。

## 一句话说清这个产品

> 官方菜单是给定的，**这口堡是你自己想的**。
> 你搭得越离谱，原创度越高；搭到官方 16 款里一层都对不上，你就是同人作者。

## 快速开始

### A. H5 搭建器（零依赖）

```bash
git clone https://github.com/xiaoxiangguo/just-burger-it.git
cd just-burger-it
python3 -m http.server 8080     # 打开 http://localhost:8080
```

快照模式开箱即玩，无需 Token。

想开「实时模式」再加一个本地代理（浏览器不能直连 MCP，CORS + Token 保护）：

```bash
export MCD_TOKEN="你的麦当劳MCP Token"   # 可选，也可在页面里临时填
python3 tools/live_proxy.py --port 8787
```

然后在页面点「🔗 实时同步门店在售食材」，填 Token + 城市 + 商圈。

### B. Skill（在 WorkBuddy 中安装）

把 `skill/` 目录整个复制到 `~/.workbuddy/skills/just-burger-it/`（目录内自带组件库快照与 MCP 客户端，复制即可独立运行，不依赖仓库其他目录），然后直接说：

> 帮我搭一颗汉堡：芝麻包、麦辣鸡腿、培根、吉士、生菜、麦香鸡酱，看看我附近门店有没有这些料

也可以命令行直接用：

```bash
export MCD_TOKEN="你的Token"
python3 skill/scripts/burger.py list --cat patty
python3 skill/scripts/burger.py build --bun sesame --patty spicychicken --patty bacon \
  --cheese cheese --veg choppedlettuce --sauce chickensauce --name "麦辣培根双拼堡"
python3 skill/scripts/burger.py build --bun sesame --patty grilledchicken \
  --veg choppedlettuce --sauce grillsauce --live --city 深圳市 --keyword 南山
```

## 数据从哪来

| 数据 | MCP 工具 | 规模 |
|---|---|---|
| 官方营养表 | `list-nutrition-foods` | 158 项餐品 |
| 门店菜单 | `query-nearby-stores` + `query-meals` | 122 个在售商品 |
| 汉堡特调配料 | `query-meal-detail` × 11 款汉堡 | 17 种官方食材级配料 |

复现步骤见 [tools/README.md](tools/README.md)，MCP 集成细节见 [MCP_INTEGRATION.md](MCP_INTEGRATION.md)。

### 营养口径（诚实声明）

- **官方差值**：如「双层吉士汉堡 429 kcal − 吉士汉堡包 294 kcal = 牛肉饼 135 kcal」，直接来自官方营养表
- **推算**（±20%）：以官方数据为锚的估算
- **创意**：官方暂无对应产品，参照同类食材估算

应用内用三种颜色徽标区分，不冒充精确数据；营养结果仅供娱乐参考，不构成饮食建议。

## 项目结构

```
just-burger-it/
├── index.html               # H5 搭建器（单文件，零依赖）
├── docs/                    # README 用的页面截图（真实浏览器截图）
├── skill/                   # 可直接独立安装的技能目录
│   ├── SKILL.md            # 技能声明（可安装到 WorkBuddy）
│   ├── data/components.json # 组件库快照（由 tools/sync_skill_data.py 分发）
│   └── scripts/
│       ├── burger.py       # CLI：搭建 + 营养核算 + 实时校验
│       └── mcp_client.py   # MCP 客户端（随技能分发，保证独立运行）
├── data/
│   ├── components.json     # 组件库（含来源标注与真实产品组成）
│   ├── nutrition.json      # 官方营养表快照
│   └── mod_items.json      # 官方特调配料宇宙
└── tools/
    ├── mcp_client.py       # MCP 客户端（Streamable HTTP，纯标准库）
    ├── live_proxy.py       # 本地代理（供 H5 实时模式）
    ├── mcp_probe.py        # MCP 连通性探测
    ├── build_components.py # 数据烘焙
    ├── validate_components.py # 组件库一致性校验
    ├── sync_skill_data.py  # 把 data/ 与 tools/ 同步进 skill/（含 --check）
    └── raw/                # MCP 原始响应存档
```

### 数据校验

`components.json` 里的官方产品组成是手工维护的（构建脚本只生成营养表与特调宇宙），所以配了一个校验脚本：

```bash
python3 tools/validate_components.py
```

它会检查：指纹引用了不存在的食材、分类内 id 重复、官方产品混入创意食材，以及**每款产品的估算热量与官方营养表的偏差是否超过 ±20%**。改完数据跑一次，就不会出现「改错一个 id 没人发现」的情况。

改完 `components.json` 后记得同步进技能目录（`skill/` 自带副本，保证可独立安装）：

```bash
python3 tools/sync_skill_data.py          # 同步
python3 tools/sync_skill_data.py --check  # 校验两份是否一致
```

## 目标用户

- 「要是 McDonald's 出这款我必买」的创意党
- 关注热量但不想放弃快乐的健身党
- 选择困难症（🎲 乱搭）
- 想在朋友圈晒一颗「只属于自己」的汉堡的麦门信徒

## 免责声明

本项目为参赛者独立开发的创意作品，非麦当劳官方出品；营养数值为基于官方公开数据的展示/估算，仅供娱乐参考。
