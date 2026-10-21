---
name: just-burger-it
description: 麦门之搭了个堡 — 定制专属于你的麦门汉堡🍔。逐层搭建汉堡（面包/肉/芝士/蔬菜/酱料），每层热量来自麦当劳中国官方 MCP 营养数据，实时校验门店在售食材，输出漫画风剖面图与营养核算。当用户说「搭个汉堡」「定制我的麦当劳汉堡」「麦门汉堡」「这个堡多少卡」「我附近门店有这些料吗」时使用。
---

# 麦门之搭了个堡

> 定制专属于你的麦门汉堡🍔

## 这是什么

一个基于麦当劳中国 MCP Server（`mcp.mcd.cn`）的汉堡搭建技能：

1. **组件库**：61 个 —— 面包 9 / 肉 18 / 芝士 5 / 蔬菜 13 / 酱料 16。其中官方 30 个（差值 7 + 推算 23）来自在售产品与官方特调配料清单，创意 7 个，传说层 24 个（官方与现实中都不存在，热量按同类粗估）
2. **营养核算**：热量、蛋白质、脂肪、碳水、钠，出自官方营养表（158 项）与真实餐品差值
3. **实时校验**：调用 `query-nearby-stores → query-meals → query-meal-detail`，判断你所在门店是否真的有这些食材
4. **原创度**：对 16 款官方产品做「按层计数 + 分类加权」比对。低于 40% 不说「最接近谁」，直接告诉你原创度、以及官方离你最近的一款差几层——越不像官方越值得炫耀
5. **传说层**：官方和现实里都不存在的食材（榴莲、螺蛳粉、整只龙虾…），热量按同类粗估，明确标注不冒充官方数据

## 前置条件

- 麦当劳 MCP Token：到 https://open.mcd.cn/mcp 手机号登录 → 控制台 → 激活 → 复制
- 设置环境变量：`export MCD_TOKEN="你的Token"`
- Token 只用于只读查询，不涉及下单/支付/积分

## 使用方法

所有脚本位于 `scripts/`，仓库根目录执行（依赖仅 Python 标准库）：

### 1. 看我附近有哪些门店

```bash
python3 scripts/burger.py stores --city 深圳市 --keyword 南山
```

### 2. 看组件库（含每层热量与数据口径）

```bash
python3 scripts/burger.py list
python3 scripts/burger.py list --cat patty
```

### 3. 搭一颗汉堡（本地模式：快照数据 + 营养核算 + 相似度）

```bash
python3 scripts/burger.py build \
  --bun sesame --patty spicychicken --patty bacon \
  --cheese cheese --veg choppedlettuce --sauce chickensauce \
  --name "麦辣培根双拼堡"
```

### 4. 搭一颗汉堡并实时校验门店在售（需要 Token）

```bash
python3 scripts/burger.py build --bun sesame --patty grilledchicken \
  --veg choppedlettuce --sauce grillsauce --live --city 深圳市 --keyword 南山
```

输出：终端剖面图 + 营养核算 + 与官方产品相似度 + 门店缺失食材提醒。

## 组件 id 速查

| 类别 | 可用 id |
|---|---|
| `--bun` | sesame(经典芝麻堡包) muffin(英式麦满分) angusbun(安格斯厚堡包) blackbun(墨鱼汁黑堡包·创意) ricebun(双层米饼·创意) |
| `--patty` | beef(经典牛肉饼) angus(安格斯厚牛饼) grilledchicken(板烧鸡腿肉) spicychicken(麦辣鸡腿肉) dragonchicken(龙焰棒腿肉) mcchickenpatty(麦香鸡鸡肉饼) fish(深海鳕鱼排) pork(猪柳) bacon(培根) shrimp(鲜虾排·创意) turkeynoodle(火鸡面肉饼·创意) |
| `--cheese` | cheese(吉士片) gouda(高达干酪片) |
| `--veg` | tomato(番茄片) lettuce(生菜) choppedlettuce(切块生菜) pickle(酸黄瓜片) onion(洋葱粒) avocado(牛油果片·创意) pineapple(夏威夷菠萝圈·创意) |
| `--sauce` | ketchup(番茄酱) mustard(芥末酱) beefsauce(烤牛肉风味酱) chickensauce(麦香鸡酱) bigmacsauce(巨无霸酱) cheesesauce(醇香芝士风味酱) grillsauce(烤味酱) chilibutter(辣椒黄油风味酱) mustardsalad(芥末沙拉酱) fishsauce(麦香鱼酱) butter(黄油) turkeysauce(火鸡面甜辣酱·创意) |

`--patty` / `--cheese` / `--veg` / `--sauce` 可重复传入多层。

### 传说层 id（官方与现实中都不存在，热量按同类粗估）

| 类别 | 传说食材 |
|---|---|
| `--bun` | cheesecrown(芝士火山包) charcoalbun(黑金竹炭包) croissant(可颂牛角包) tartbun(蛋挞壳包) |
| `--patty` | lobster(整只龙虾) malahotpot(麻辣香锅饼) luosifen(螺蛳粉饼) roastduck(北京烤鸭片) stinkytofu(臭豆腐排) crayfish(小龙虾肉饼) wagyu(和牛厚切) |
| `--cheese` | bluecheese(蓝纹芝士) cheesefall(芝士瀑布) mozzarella(马苏里拉球) |
| `--veg` | durian(榴莲果肉) boba(黑糖珍珠) nori(海苔脆片) kimchi(韩式泡菜) hashbrown(薯饼) strawberry(草莓) |
| `--sauce` | laoganma(老干妈) bobatea(珍珠奶茶酱) tomyum(冬阴功酱) honeymustard(蜂蜜芥末) |

## 数据口径（务必如实转述给用户）

- **官方差值**：如「双层吉士汉堡 429 − 吉士汉堡包 294 = 牛肉饼 135 kcal」，来自官方营养表
- **推算**：以官方数据为锚的估算，误差约 ±20%
- **创意**：官方暂无对应产品（火鸡面肉饼等），参照同类食材估算，仅作许愿

不得把推算值说成官方精确值；营养结果仅供娱乐参考，不构成饮食建议。

## 相关文件

本技能目录自带运行所需的全部文件，安装后无需仓库其他目录：

- `data/components.json` — 组件库与真实产品组成（技能内置快照）
- `scripts/mcp_client.py` — MCP 客户端（Streamable HTTP，无状态）
- `scripts/burger.py` — 本 CLI

仓库中还提供（可选，用于重新拉数据或看图形界面）：

- `data/nutrition.json` — 官方营养表快照（158 项）
- `index.html` — H5 搭建器（漫画风剖面图 + 许愿卡）
- `tools/` — 数据管道与本地代理
