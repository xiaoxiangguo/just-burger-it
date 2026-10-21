#!/usr/bin/env python3
"""向 data/components.json 注入「传说食材」，保持原有单行对象格式。"""
import json
import os
import sys

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "components.json")

BASIS = "传说层：官方菜单无此物，热量按同类食材粗估，仅供构词"

LEGEND = {
    "buns": [
        ("cheesecrown", "芝士火山包", 260, 8, 9, 36, 520, "#f0a53a"),
        ("charcoalbun", "黑金竹炭包", 150, 5, 3, 27, 300, "#3a3a42"),
        ("croissant", "可颂牛角包", 230, 5, 12, 26, 380, "#d9a353"),
        ("tartbun", "蛋挞壳包", 180, 3, 8, 24, 210, "#e8c07a"),
    ],
    "patties": [
        ("lobster", "整只龙虾", 120, 18, 2, 3, 420, "#ef6a52"),
        ("malahotpot", "麻辣香锅饼", 320, 12, 22, 20, 780, "#b23a2e"),
        ("luosifen", "螺蛳粉饼", 280, 9, 14, 30, 900, "#b8a05a"),
        ("roastduck", "北京烤鸭片", 260, 16, 19, 6, 480, "#a8552f"),
        ("stinkytofu", "臭豆腐排", 180, 12, 11, 8, 520, "#8a8f5e"),
        ("crayfish", "小龙虾肉饼", 150, 14, 6, 5, 380, "#e2593f"),
        ("wagyu", "和牛厚切", 380, 20, 32, 2, 300, "#7d3f33"),
    ],
    "cheeses": [
        ("bluecheese", "蓝纹芝士", 90, 5, 7, 1, 320, "#9fb8c9"),
        ("cheesefall", "芝士瀑布", 160, 8, 12, 4, 460, "#f7c948"),
        ("mozzarella", "马苏里拉球", 120, 8, 8, 2, 280, "#fbf0d0"),
    ],
    "veggies": [
        ("durian", "榴莲果肉", 150, 2, 5, 24, 10, "#e3c65b"),
        ("boba", "黑糖珍珠", 180, 1, 4, 36, 20, "#4a3b33"),
        ("nori", "海苔脆片", 10, 1, 0.2, 1, 40, "#3f5b3a"),
        ("kimchi", "韩式泡菜", 15, 1, 0.2, 2, 300, "#d9534f"),
        ("hashbrown", "薯饼", 150, 2, 9, 16, 300, "#d9a441"),
        ("strawberry", "草莓", 25, 0.5, 0.2, 6, 2, "#e05a6b"),
    ],
    "sauces": [
        ("laoganma", "老干妈", 60, 1, 5.5, 2, 380, "#a5251c"),
        ("bobatea", "珍珠奶茶酱", 120, 1, 5, 18, 40, "#c39b6b"),
        ("tomyum", "冬阴功酱", 45, 1, 3, 3, 420, "#d97437"),
        ("honeymustard", "蜂蜜芥末", 70, 0.3, 5, 6, 180, "#e6b93c"),
    ],
}


def array_end(s, key):
    """返回 key 对应数组右括号的索引。"""
    start = s.index('"%s": [' % key)
    i = s.index("[", start)
    depth, in_str, esc = 0, False, False
    while i < len(s):
        c = s[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    raise ValueError("unbalanced array: " + key)


def main():
    s = open(P, encoding="utf-8").read()
    data = json.loads(s)
    added = 0
    for cat, rows in LEGEND.items():
        have = {c["id"] for c in data[cat]}
        chunk = []
        for (cid, name, cal, pro, fat, carb, sod, color) in rows:
            if cid in have:
                print("跳过已存在:", cid)
                continue
            chunk.append({
                "id": cid, "name": name, "kcal": cal, "protein": pro, "fat": fat,
                "carb": carb, "sodium": sod, "source": "legend", "basis": BASIS, "color": color,
            })
        if not chunk:
            continue
        lines = ",\n".join("    " + json.dumps(x, ensure_ascii=False) for x in chunk)
        pos = array_end(s, cat)
        s = s[:pos].rstrip() + ",\n" + lines + "\n  " + s[pos:]
        added += len(chunk)

    open(P, "w", encoding="utf-8").write(s)
    d2 = json.loads(open(P, encoding="utf-8").read())
    for cat in LEGEND:
        print(cat, len(d2[cat]))
    total = sum(len(d2[c]) for c in ("buns", "patties", "cheeses", "veggies", "sauces"))
    print("新增:", added, "| 组件总数:", total)


if __name__ == "__main__":
    main()
