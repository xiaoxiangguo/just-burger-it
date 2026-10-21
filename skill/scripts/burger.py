#!/usr/bin/env python3
"""麦门汉堡搭建器 · CLI

用法：
  python3 skill/scripts/burger.py list [--cat patty]
  python3 skill/scripts/burger.py stores --city 深圳市 --keyword 南山
  python3 skill/scripts/burger.py build --bun sesame --patty spicychicken \
      --veg choppedlettuce --sauce chickensauce [--live --city 深圳市 --keyword 南山]

本地模式只读 data/components.json（快照）；--live 会实时调用麦当劳 MCP 校验门店在售。
"""
import argparse
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)                  # skill/（安装态根）
REPO_ROOT = os.path.dirname(SKILL_ROOT)             # <repo>/（开发态根）

# 数据查找：安装态读 skill/data（随技能一起分发），开发态回退仓库 data/
_CANDIDATES = [
    os.path.join(SKILL_ROOT, "data", "components.json"),
    os.path.join(REPO_ROOT, "data", "components.json"),
]
DATA_PATH = next((p for p in _CANDIDATES if os.path.exists(p)), "")
if not DATA_PATH:
    sys.exit("找不到 components.json，请先在仓库根运行：python3 tools/sync_skill_data.py")

# mcp_client 查找：安装态与本脚本同目录，开发态在 <repo>/tools/
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

DATA = json.load(open(DATA_PATH, encoding="utf-8"))
CATS = {"bun": "buns", "patty": "patties", "cheese": "cheeses", "veg": "veggies", "sauce": "sauces"}
INDEX = {cat: {c["id"]: c for c in DATA[key]} for cat, key in CATS.items()}
NAME_OF = {cid: c["name"] for cat in INDEX for cid, c in INDEX[cat].items()}
SRC_LABEL = {"mcp-diff": "官方差值", "estimated": "推算", "creative": "创意"}


# ---------------- ASCII 剖面图 ----------------
GLYPH = {
    "bun":     ("╭{pad}╮", "╰{pad}╯"),
    "patty":   "▬▬▬ ▬▬▬",
    "cheese":  "≈≈≈≈≈≈≈",
    "sauce":   "∼∼∼∼∼∼∼",
    "veg":     "∧∧∧∧∧∧∧",
}


def center(text, width):
    return text.center(width)


def ascii_burger(stack, name):
    w = 46
    lines = []
    lines.append("┌" + "─" * w + "┐")
    lines.append("│" + center(f"🍔 {name}", w) + "│")
    lines.append("├" + "─" * w + "┤")
    bun = next((s for s in stack if s["cat"] == "bun"), None)
    rest = [s for s in stack if s is not bun]

    def label(s):
        tag = SRC_LABEL.get(s["item"]["source"], "")
        return f"{s['item']['name']} {round(s['item']['kcal'])}kcal · {tag}"

    if bun:
        lines.append("│" + center("◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠◠", w) + "│")
        lines.append("│" + center(label(bun), w) + "│")
    for s in reversed(rest):
        g = GLYPH.get(s["cat"], "───────")
        lines.append("│" + center(g, w) + "│")
        lines.append("│" + center(label(s), w) + "│")
    if bun:
        lines.append("│" + center("◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡◡", w) + "│")
    lines.append("└" + "─" * w + "┘")
    return "\n".join(lines)


def totals(stack):
    t = {"kcal": 0, "protein": 0, "fat": 0, "carb": 0, "sodium": 0}
    for s in stack:
        for k in t:
            t[k] += s["item"][k]
    return t


SIM_MIN = 0.40   # 低于此分数不声称“官方最接近”
SIM_TOP = 3
# 面包/肉饼/芝士定义身份，蔬菜/酱料是点缀：不按类加权的话，层数少的产品会永远占优
WEIGHT = {"bun": 3, "patty": 3, "cheese": 2, "veg": 1, "sauce": 1}
W_OF = {cid: WEIGHT[cat] for cat in INDEX for cid in INDEX[cat]}


def similarity(stack):
    """按层计数 + 分类加权的多重集合相似度：{牛肉×2} 和 {牛肉×1} 不再等价。

    交集 = Σ 权重 × min(你放的层数, 官方层数)；并集 = Σ 权重 × max(...)
    同时返回还缺哪几层，方便提示“再补 N 层就是它”。
    """
    if not stack:
        return None
    u = Counter(s["item"]["id"] for s in stack)
    scored = []
    for rb in DATA["realBurgers"]:
        r = Counter(rb["layers"])
        keys = set(u) | set(r)
        inter = sum(W_OF.get(k, 1) * min(u[k], r[k]) for k in keys)
        if not inter:
            continue
        union = sum(W_OF.get(k, 1) * max(u[k], r[k]) for k in keys)
        missing = [k for k in r if r[k] > u[k]]
        scored.append({"name": rb["name"], "score": inter / union,
                       "inter": inter, "missing": missing})
    if not scored:
        return {"top": [], "confident": False}
    scored.sort(key=lambda x: (-x["score"], -x["inter"]))
    return {"top": scored[:SIM_TOP], "confident": scored[0]["score"] >= SIM_MIN}


def report(stack, name):
    t = totals(stack)
    print(ascii_burger(stack, name))
    print()
    bar = lambda pct, n=24: "█" * max(1, round(pct / 100 * n)) + "░" * (n - max(1, round(pct / 100 * n)))
    print("── 营养核算 ─────────────────────────────")
    print(f"  总热量   {round(t['kcal']):>5} kcal   每日推荐 {round(t['kcal']/2000*100)}%")
    print(f"  蛋白质   {t['protein']:>5.1f} g     {bar(t['protein']*4/max(1,t['kcal'])*100)}")
    print(f"  脂肪     {t['fat']:>5.1f} g     {bar(t['fat']*9/max(1,t['kcal'])*100)}")
    print(f"  碳水     {t['carb']:>5.1f} g     {bar(t['carb']*4/max(1,t['kcal'])*100)}")
    flag = "⚠ 超过每日建议上限" if t["sodium"] > 2000 else "在建议范围内"
    print(f"  钠       {round(t['sodium']):>5} mg    {flag}")
    sim = similarity(stack)
    if sim and sim["top"]:
        a = sim["top"][0]
        if sim["confident"]:
            print(f"\n  官方最接近产品：{a['name']} · 相似度 {round(a['score']*100)}%")
            if a["missing"]:
                gap = "、".join(NAME_OF.get(k, k) for k in a["missing"][:3])
                more = " 等" if len(a["missing"]) > 3 else ""
                print(f"  再补 {len(a['missing'])} 层就是它：{gap}{more}")
            else:
                print("  配方完全一致 ✓")
            rest = sim["top"][1:]
            if rest:
                print("  次选：" + " · ".join(f"{x['name']} {round(x['score']*100)}%" for x in rest))
        else:
            print("\n  这颗是原创 🎉")
            print(f"  最接近的也只有 {a['name']} {round(a['score']*100)}%")
    print("\n  数据口径：官方差值=官方营养表两餐品之差；推算=以官方为锚(±20%)；创意=许愿项")


def build_stack(args):
    stack = []
    if args.bun:
        item = INDEX["bun"].get(args.bun)
        if not item:
            sys.exit(f"未知面包 id: {args.bun}（可选 {list(INDEX['bun'])})")
        stack.append({"cat": "bun", "item": item})
    for cat, values, limit in (("patty", args.patty, 3), ("cheese", args.cheese, 3),
                               ("veg", args.veg, 4), ("sauce", args.sauce, 3)):
        values = values or []
        if len(values) > limit:
            sys.exit(f"{cat} 最多 {limit} 层")
        for v in values:
            item = INDEX[cat].get(v)
            if not item:
                sys.exit(f"未知 {cat} id: {v}（可选 {list(INDEX[cat])})")
            stack.append({"cat": cat, "item": item})
    return stack


def live_check(args, stack):
    from mcp_client import MCPClient, MCPError, find_stores, fetch_menu  # noqa: E402
    try:
        client = MCPClient()
        stores = find_stores(client, args.city, args.keyword)
        if not stores:
            print(f"\n⚠ 未找到门店：{args.city} {args.keyword}")
            return
        store = stores[0]
        menu = fetch_menu(client, store["storeCode"])
        names = [m.get("name", "") for m in menu.get("meals", {}).values()]
        print(f"\n── 门店实时校验（{store.get('storeName')}）────────────")
        for s in stack:
            if s["item"].get("source") == "creative":
                print(f"  ✗ {s['item']['name']}：创意层，门店无此售卖")
                continue
            carriers = [rb["name"] for rb in DATA["realBurgers"] if s["item"]["id"] in rb["layers"]]
            hit = any(c in n for n in names for c in carriers) if carriers else any(
                s["item"]["name"] in n for n in names)
            print(f"  {'✓' if hit else '✗'} {s['item']['name']}：{'在售可搭' if hit else '本店未见在售'}")
    except MCPError as e:
        print(f"\n⚠ 实时校验失败：{e}")


def main():
    ap = argparse.ArgumentParser(description="麦门汉堡搭建器 CLI — 定制专属于你的麦门汉堡🍔")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="列出组件库")
    p_list.add_argument("--cat", choices=list(CATS), help="只看某一类")

    p_st = sub.add_parser("stores", help="查询附近门店")
    p_st.add_argument("--city", default="深圳市")
    p_st.add_argument("--keyword", default="")

    p_b = sub.add_parser("build", help="搭一颗汉堡")
    p_b.add_argument("--bun", help="面包 id")
    p_b.add_argument("--patty", action="append", help="肉层 id（可重复）")
    p_b.add_argument("--cheese", action="append", help="芝士 id（可重复）")
    p_b.add_argument("--veg", action="append", help="蔬菜 id（可重复）")
    p_b.add_argument("--sauce", action="append", help="酱料 id（可重复）")
    p_b.add_argument("--name", default="无名麦门堡")
    p_b.add_argument("--live", action="store_true", help="实时校验门店在售（需 MCD_TOKEN）")
    p_b.add_argument("--city", default="深圳市")
    p_b.add_argument("--keyword", default="南山")

    args = ap.parse_args()

    if args.cmd == "list":
        cats = [args.cat] if args.cat else list(CATS)
        for cat in cats:
            print(f"\n【{cat}】")
            for cid, c in INDEX[cat].items():
                print(f"  {cid:<14} {c['name']:<16} {round(c['kcal']):>4} kcal · {SRC_LABEL.get(c['source'], c['source'])}")
        return

    if args.cmd == "stores":
        from mcp_client import MCPClient, MCPError, find_stores  # noqa: E402
        try:
            stores = find_stores(MCPClient(), args.city, args.keyword)
        except MCPError as e:
            sys.exit(f"查询失败：{e}")
        for st in stores[:10]:
            print(f"{st.get('storeCode')}  {st.get('storeName')}  {st.get('address')}")
        return

    stack = build_stack(args)
    if not stack:
        sys.exit("至少加一层食材")
    report(stack, args.name)
    if args.live:
        live_check(args, stack)


if __name__ == "__main__":
    main()
