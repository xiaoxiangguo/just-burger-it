#!/usr/bin/env python3
"""Local proxy for the browser's "live mode".

Browsers cannot call mcp.mcd.cn directly (CORS + token exposure), so the H5
talks to this tiny stdlib server instead:

    POST /api/live-menu  {token, city, keyword}
      -> {ok, storeName, storeCode, burgers, soldOut: [componentId...]}

Run:  python3 tools/live_proxy.py [--port 8787]
Token never leaves the machine: it is passed per-request from the browser and
only used in-memory for that single call chain.
"""
import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mcp_client import MCPClient, MCPError, find_stores, fetch_menu  # noqa: E402

ROOT = os.path.dirname(HERE)
COMPONENTS = json.load(open(os.path.join(ROOT, "data", "components.json"), encoding="utf-8"))


def carriers():
    """componentId -> names of real burgers that contain it."""
    m = {}
    for rb in COMPONENTS["realBurgers"]:
        for cid in rb["layers"]:
            m.setdefault(cid, []).append(rb["name"])
    return m


CARRIERS = carriers()

# 含这些字样的菜单项不是“单点汉堡”（套餐/组合/桶/儿童餐/任选拼盘等）
NOT_SINGLE = ("套餐", "件套", "桶", "分享", "乐园", "组合", "加购", "换购",
              "任选", "精选", "随心", "专享", "小食", "拼")


def _norm(name):
    """去掉「汉堡/堡」后缀再比对，避免子串误判（如 汉堡包 ⊂ 吉士汉堡包套餐）。"""
    n = name.replace("汉堡", "").replace("堡", "").strip()
    return n


def looks_like_burger(name):
    return ("堡" in name) or name in ("巨无霸", "麦香鱼", "麦香鸡") or name.endswith("霸")


def classify_menu(menu_names):
    """把菜单名分成：本店在售的官方产品 / 本店有但未收录的汉堡。

    只做「单点」比对：套餐一律排除，且先精确匹配，再退化到去后缀比对。
    """
    single = [n for n in menu_names if n and not any(x in n for x in NOT_SINGLE)]
    exact = set(single)
    normalized = {_norm(n) for n in single}

    on_sale = []
    for rb in COMPONENTS["realBurgers"]:
        name = rb["name"]
        if name in exact or _norm(name) in normalized:
            on_sale.append(name)

    known_names = {rb["name"] for rb in COMPONENTS["realBurgers"]}
    known_norm = {_norm(n) for n in known_names}
    unlisted = sorted({
        n for n in single
        if looks_like_burger(n) and n not in known_names and _norm(n) not in known_norm
    })
    return on_sale, unlisted, len([n for n in single if looks_like_burger(n)])


def live_menu(token, city, keyword):
    client = MCPClient(token)
    stores = find_stores(client, city, keyword)
    if not stores:
        return {"ok": False, "error": f"未找到门店：{city} {keyword}"}
    store = stores[0]
    menu = fetch_menu(client, store["storeCode"])
    meals = menu.get("meals") or {}
    names = [m.get("name", "") for m in meals.values()]

    on_sale, unlisted, burger_count = classify_menu(names)
    sold_out = []
    all_components = [c for cat in ("buns", "patties", "cheeses", "veggies", "sauces")
                      for c in COMPONENTS[cat]]
    for comp in all_components:
        cid = comp["id"]
        # 创意食材永远不在真实门店售卖
        if comp.get("source") == "creative":
            sold_out.append(cid)
            continue
        # 所有承载它的真实汉堡都不在售 -> 判定本店不可用
        carrier_names = CARRIERS.get(cid, [])
        if carrier_names and not any(n in on_sale for n in carrier_names):
            sold_out.append(cid)

    return {
        "ok": True,
        "storeName": store.get("storeName"),
        "storeCode": store.get("storeCode"),
        "burgers": burger_count,
        "onSaleReal": sorted(on_sale),
        "unlisted": unlisted,
        "soldOut": sold_out,
    }


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/api/live-menu":
            self.send_response(404)
            self._cors()
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            token = body.get("token") or os.environ.get("MCD_TOKEN", "")
            result = live_menu(token, body.get("city", "深圳市"), body.get("keyword", ""))
        except MCPError as e:
            result = {"ok": False, "error": str(e)}
        except Exception as e:  # noqa: BLE001
            result = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        payload = json.dumps(result, ensure_ascii=False).encode()
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        sys.stderr.write("[proxy] " + fmt % args + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    args = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"live proxy on http://127.0.0.1:{args.port}  (POST /api/live-menu)")
    srv.serve_forever()


if __name__ == "__main__":
    main()
