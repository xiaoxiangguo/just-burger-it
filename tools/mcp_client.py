#!/usr/bin/env python3
"""Shared McDonald's MCP client (Streamable HTTP, stdlib only).

The server (mcp.mcd.cn) is stateless: it returns no mcp-session-id, so each
logical call sends `initialize` first, then the actual request.
"""
import json
import os
import urllib.error
import urllib.request

URL = "https://mcp.mcd.cn"
PROTOCOL = "2024-11-05"


class MCPError(RuntimeError):
    pass


class MCPClient:
    def __init__(self, token=None, url=URL, timeout=30):
        self.token = token or os.environ.get("MCD_TOKEN", "")
        if not self.token:
            raise MCPError("缺少 MCP Token：请设置环境变量 MCD_TOKEN 或显式传入")
        self.url = url
        self.timeout = timeout
        self._seq = 0

    # ---------- transport ----------
    def _post(self, payload):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {self.token}",
        }
        req = urllib.request.Request(
            self.url, data=json.dumps(payload).encode(), headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.headers.get("Content-Type", ""), resp.read().decode()
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:800]
            if e.code == 401:
                raise MCPError("MCP Token 无效或已过期（401）") from e
            if e.code == 429:
                raise MCPError("触发限流 600 次/分钟（429），请稍后重试") from e
            raise MCPError(f"HTTP {e.code}: {body}") from e

    @staticmethod
    def _parse(ctype, body):
        if "text/event-stream" in ctype:
            out = None
            for line in body.splitlines():
                if line.startswith("data:"):
                    try:
                        out = json.loads(line[5:].strip())
                    except json.JSONDecodeError:
                        pass
            return out
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"_raw": body[:500]}

    # ---------- JSON-RPC ----------
    def _init(self):
        self._post({
            "jsonrpc": "2.0", "id": 0, "method": "initialize",
            "params": {"protocolVersion": PROTOCOL, "capabilities": {},
                       "clientInfo": {"name": "just-burger-it", "version": "0.2"}},
        })

    def list_tools(self):
        self._init()
        self._seq += 1
        ctype, body = self._post({"jsonrpc": "2.0", "id": self._seq, "method": "tools/list", "params": {}})
        data = self._parse(ctype, body) or {}
        return data.get("result", {}).get("tools", [])

    def call(self, tool, arguments=None):
        """Call a tool and return the embedded API JSON (parsed)."""
        self._init()
        self._seq += 1
        ctype, body = self._post({
            "jsonrpc": "2.0", "id": self._seq, "method": "tools/call",
            "params": {"name": tool, "arguments": arguments or {}},
        })
        data = self._parse(ctype, body) or {}
        if "error" in data:
            raise MCPError(f"{tool} 调用失败: {data['error']}")
        result = data.get("result", {})
        if result.get("isError"):
            raise MCPError(f"{tool} 返回错误: {str(result)[:300]}")
        content = result.get("content") or []
        text = "".join(c.get("text", "") for c in content if c.get("type") == "text")
        return self._extract_api_json(text) if text else result

    @staticmethod
    def _extract_api_json(text):
        """MCP wraps the raw API response in a markdown-ish text block."""
        idx = text.find('{"success"')
        if idx < 0:
            return {"_text": text}
        try:
            obj, _ = json.JSONDecoder().raw_decode(text[idx:])
            return obj
        except json.JSONDecodeError:
            return {"_text": text}


# ---------------- domain helpers ----------------
def find_stores(client, city, keyword=""):
    r = client.call("query-nearby-stores", {"beType": 1, "searchType": 2, "city": city, "keyword": keyword})
    return r.get("data") or []


def fetch_menu(client, store_code):
    r = client.call("query-meals", {"storeCode": store_code, "orderType": 1, "beType": 1})
    return r.get("data") or {}


def meal_detail(client, store_code, code):
    r = client.call("query-meal-detail", {"storeCode": store_code, "orderType": 1, "beType": 1, "code": code})
    return r.get("data") or {}


def nutrition_table(client):
    r = client.call("list-nutrition-foods")
    rows = {}
    for line in (r.get("data") or "").splitlines():
        parts = [p.strip() for p in line.strip().split(",")]
        if len(parts) < 9 or line.startswith("[") or line.startswith("{"):
            continue
        try:
            rows[parts[0]] = {
                "energyKcal": float(parts[3]), "protein": float(parts[4]),
                "fat": float(parts[5]), "carbohydrate": float(parts[6]), "sodium": float(parts[7]),
            }
        except ValueError:
            continue
    return rows
