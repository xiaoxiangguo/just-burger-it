#!/usr/bin/env python3
"""McDonald's MCP probe client (Streamable HTTP, stdlib only).

Usage: python3 mcp_probe.py <command> [args_json]
Commands:
  list-tools                       - enumerate tools
  call <tool_name> [args_json]     - call a tool
Env: MCD_TOKEN
"""
import json
import os
import sys
import urllib.request
import urllib.error

URL = "https://mcp.mcd.cn"
TOKEN = os.environ.get("MCD_TOKEN", "")
SESSION_FILE = "/tmp/mcd_mcp_session.txt"


def post(payload, session_id=None, timeout=30):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {TOKEN}",
    }
    if session_id:
        headers["mcp-session-id"] = session_id
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read().decode()
        sid = resp.headers.get("mcp-session-id", "")
        ctype = resp.headers.get("Content-Type", "")
        return resp.status, sid, ctype, body
    except urllib.error.HTTPError as e:
        return e.code, "", "", e.read().decode()[:2000]


def parse_body(ctype, body):
    """Handle both plain JSON and SSE responses."""
    if "text/event-stream" in ctype:
        # parse SSE: take last data: line that parses as JSON
        result = None
        for line in body.splitlines():
            if line.startswith("data:"):
                chunk = line[5:].strip()
                try:
                    result = json.loads(chunk)
                except json.JSONDecodeError:
                    pass
        return result
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"_raw": body[:1000]}


def ensure_session():
    """Initialize MCP session, persist session id."""
    if os.path.exists(SESSION_FILE):
        return json.load(open(SESSION_FILE))
    status, sid, ctype, body = post({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "burger-lab-probe", "version": "0.1"},
        },
    })
    if status != 200 or not sid:
        print(json.dumps({"error": f"initialize failed: {status}", "body": body[:800]}, ensure_ascii=False))
        sys.exit(1)
    # send initialized notification
    post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    json.dump({"sid": sid}, open(SESSION_FILE, "w"))
    return {"sid": sid}


def rpc(method, params, req_id=None):
    """Stateless mode: the server returns no session id, so send
    initialize + the actual request in one POST batch."""
    payload = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
               "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                          "clientInfo": {"name": "burger-lab-probe", "version": "0.1"}}}
    status, _, ctype, body = post(payload)
    if status != 200:
        return status, {"error": "initialize failed", "body": body[:500]}
    payload2 = {"jsonrpc": "2.0", "method": method, "params": params}
    if req_id is not None:
        payload2["id"] = req_id
    status, _, ctype, body = post(payload2)
    return status, parse_body(ctype, body)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list-tools"
    if cmd == "list-tools":
        status, result = rpc("tools/list", {}, 2)
        print(json.dumps({"status": status, "result": result}, ensure_ascii=False, indent=1))
    elif cmd == "call":
        tool = sys.argv[2]
        args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        status, result = rpc("tools/call", {"name": tool, "arguments": args}, 3)
        print(json.dumps({"status": status, "result": result}, ensure_ascii=False))
    else:
        print("unknown command")


if __name__ == "__main__":
    main()
