#!/usr/bin/env python3
"""Build data/nutrition.json + data/components.json from raw MCP probe outputs.

Inputs (fetched via tools/mcp_probe.py, kept under tools/raw/):
  tools/raw/nutrition.json       - list-nutrition-foods response
  tools/raw/burger_details.json  - query-meal-detail responses for all single burgers
  tools/raw/meals.json           - query-meals response (store menu)

All component nutrition values are either:
  - source: "mcp"        -> taken verbatim from the official nutrition table
  - source: "estimated"  -> derived from official product values (documented diff method)
Never invent numbers silently: every estimated field keeps its estimate basis.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(os.path.dirname(HERE), "data")


def load_raw(name):
    p = os.path.join(RAW, name)
    if not os.path.exists(p):
        sys.exit(f"missing raw input: {p} (see tools/README.md for fetch commands)")
    return json.load(open(p))


def extract_structured(mcp_response_text):
    """MCP tool text embeds the original API JSON. Extract it."""
    start = mcp_response_text.index('{"success":')
    raw, _ = json.JSONDecoder().raw_decode(mcp_response_text[start:])
    return raw


def parse_nutrition():
    resp = load_raw("nutrition.json")
    text = resp["result"]["result"]["content"][0]["text"]
    raw = extract_structured(text)
    table = raw["data"]  # string: "[160]{cols}:\n  rows..."
    rows = {}
    for line in table.splitlines():
        line = line.strip()
        if not line or line.startswith("[") or line.startswith("{"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 9:
            continue
        name = parts[0]
        try:
            rows[name] = {
                "energyKj": float(parts[2]),
                "energyKcal": float(parts[3]),
                "protein": float(parts[4]),
                "fat": float(parts[5]),
                "carbohydrate": float(parts[6]),
                "sodium": float(parts[7]),
                "calcium": float(parts[8]),
            }
        except ValueError:
            continue
    return rows


def build_components(nutrition):
    details = load_raw("burger_details.json")
    meals = extract_structured(
        load_raw("meals.json")["result"]["result"]["content"][0]["text"]
    )["data"]

    # ---- collect the real modification (特调) ingredient universe ----
    mod_items = {}  # name -> {"codes": set, "burgers": list}
    for code, entry in details.items():
        mod = entry["detail"].get("modification", {})
        for item in mod.get("items", []):
            for v in item["values"]:
                e = mod_items.setdefault(v["name"], {"codes": [], "burgers": []})
                if v["code"] not in e["codes"]:
                    e["codes"].append(v["code"])
                e["burgers"].append(entry["name"])

    for name, e in sorted(mod_items.items()):
        print(f"  mod item: {name} ({len(set(e['burgers']))} burgers)")

    return mod_items, details, meals


def main():
    nutrition = parse_nutrition()
    print(f"nutrition rows: {len(nutrition)}")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "nutrition.json"), "w") as f:
        json.dump(
            {"fetchedAt": "2026-10-21", "storeCode": "1420207",
             "source": "mcp.mcd.cn list-nutrition-foods", "items": nutrition},
            f, ensure_ascii=False, indent=1)
    mod_items, details, meals = build_components(nutrition)
    with open(os.path.join(OUT, "mod_items.json"), "w") as f:
        json.dump(mod_items, f, ensure_ascii=False, indent=1)
    print("wrote data/nutrition.json + data/mod_items.json")


if __name__ == "__main__":
    main()
