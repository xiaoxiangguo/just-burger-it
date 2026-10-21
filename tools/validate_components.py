#!/usr/bin/env python3
"""校验 data/components.json 的一致性。

为什么需要它：components.json 里的 realBurgers（官方产品组成指纹）是手工维护的，
构建脚本并不生成它。没有校验的话，改错一个 id、漏掉一层、或热量与官方营养表
对不上，都不会有人发现。

检查项：
  ERROR  realBurgers 引用了不存在的食材 id
  ERROR  同一分类内 id 重复
  ERROR  官方产品里混入了 creative（创意）食材
  WARN   跨分类 id 重名（会破坏按 id 聚合的相似度计算，应尽量避免）
  WARN   指纹热量与官方营养表偏差 > 20%

用法：python3 tools/validate_components.py [--strict]
      --strict 时 WARN 也视为失败（默认只报错不拦截）
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CATS = ("buns", "patties", "cheeses", "veggies", "sauces")
DEV_LIMIT = 0.20


def load():
    comp = json.load(open(os.path.join(ROOT, "data", "components.json"), encoding="utf-8"))
    nut_path = os.path.join(ROOT, "data", "nutrition.json")
    nut = {}
    if os.path.exists(nut_path):
        nut = json.load(open(nut_path, encoding="utf-8")).get("items", {})
    return comp, nut


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    comp, nut = load()
    errors, warns = [], []

    # 1) 分类内 id 唯一
    for cat in CATS:
        seen = {}
        for c in comp[cat]:
            if c["id"] in seen:
                errors.append(f"{cat} 内 id 重复：{c['id']}")
            seen[c["id"]] = c
    # 2) 分类间重名
    owner = {}
    for cat in CATS:
        for c in comp[cat]:
            owner.setdefault(c["id"], []).append(cat)
    for cid, cats in owner.items():
        if len(cats) > 1:
            warns.append(f"id「{cid}」同时出现在 {cats}，按 id 聚合时会混淆（渲染无影响）")

    by_id = {c["id"]: c for cat in CATS for c in comp[cat]}

    # 3) 指纹合法性 + 热量偏差
    print(f"{'产品':20}{'估算':>7}{'官方':>7}{'偏差':>8}")
    for rb in comp["realBurgers"]:
        total = 0.0
        for lid in rb["layers"]:
            if lid not in by_id:
                errors.append(f"{rb['name']} 引用了不存在的食材：{lid}")
                continue
            total += by_id[lid]["kcal"]
            if by_id[lid].get("source") in ("creative", "legend"):
                errors.append(f"{rb['name']}（官方产品）含非官方食材：{by_id[lid]['name']}")
        official = rb.get("officialKcal")
        if official:
            dev = (total - official) / official
            flag = "  !! 超出 ±20%" if abs(dev) > DEV_LIMIT else ""
            print(f"{rb['name']:20}{total:>7.0f}{official:>7.0f}{dev * 100:>7.1f}%{flag}")
            if abs(dev) > DEV_LIMIT:
                warns.append(f"{rb['name']} 估算 {total:.0f} vs 官方 {official:.0f}（{dev * 100:+.1f}%）")
        else:
            print(f"{rb['name']:20}{total:>7.0f}{'—':>7}{'—':>8}")

    n_comp = sum(len(comp[c]) for c in CATS)
    print(f"\n组件 {n_comp} 个 · 官方产品 {len(comp['realBurgers'])} 款")

    for w in warns:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"\n失败：{len(errors)} 个错误，{len(warns)} 个警告")
        return 1
    if warns and args.strict:
        print(f"\n严格模式失败：{len(warns)} 个警告")
        return 1
    print(f"\n通过：0 个错误，{len(warns)} 个警告")
    return 0


if __name__ == "__main__":
    sys.exit(main())
