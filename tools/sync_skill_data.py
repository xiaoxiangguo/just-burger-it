#!/usr/bin/env python3
"""把仓库根的数据与 MCP 客户端同步进 skill/ 目录。

skill/ 需要能独立安装到 ~/.workbuddy/skills/ 下运行，因此必须自带：
  skill/data/components.json   <- data/components.json
  skill/scripts/mcp_client.py  <- tools/mcp_client.py

单一来源仍是仓库根的 data/ 与 tools/，本脚本只做发布态复制。
改了 data/components.json 后跑一次本脚本，再用 --check 确认两份一致。

用法：
  python3 tools/sync_skill_data.py           # 同步
  python3 tools/sync_skill_data.py --check   # 只校验，不一致则退出码 1
"""
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PAIRS = [
    (os.path.join(ROOT, "data", "components.json"), os.path.join(ROOT, "skill", "data", "components.json")),
    (os.path.join(ROOT, "tools", "mcp_client.py"), os.path.join(ROOT, "skill", "scripts", "mcp_client.py")),
]


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    check_only = "--check" in sys.argv[1:]
    bad = []
    for src, dst in PAIRS:
        rel_src = os.path.relpath(src, ROOT)
        rel_dst = os.path.relpath(dst, ROOT)
        if not os.path.exists(src):
            print(f"✗ 源文件不存在：{rel_src}")
            bad.append(rel_dst)
            continue
        if check_only:
            if not os.path.exists(dst):
                print(f"✗ 缺失：{rel_dst}（请运行 python3 tools/sync_skill_data.py）")
                bad.append(rel_dst)
            elif sha256(src) != sha256(dst):
                print(f"✗ 不一致：{rel_dst} 与 {rel_src} 内容不同")
                bad.append(rel_dst)
            else:
                print(f"✓ 一致：{rel_dst}")
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        print(f"✓ {rel_src} → {rel_dst}  ({os.path.getsize(dst)} bytes)")
    if bad:
        print(f"\n{len(bad)} 个文件需要处理")
        sys.exit(1)
    print("\nskill/ 目录已与仓库源同步" if not check_only else "\nskill/ 目录与仓库源完全一致")


if __name__ == "__main__":
    main()
