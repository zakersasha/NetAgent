#!/usr/bin/env python3
"""Diagnose Xray entry relay: clients, inbounds, outbound bridge."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def list_vless_inbounds(config: dict) -> list[tuple[str, int | None, object, list[dict]]]:
    rows: list[tuple[str, int | None, object, list[dict]]] = []
    for inbound in config.get("inbounds", []):
        if inbound.get("protocol") != "vless":
            continue
        tag = str(inbound.get("tag", ""))
        port = inbound.get("port")
        reality = inbound.get("streamSettings", {}).get("realitySettings", {})
        short_ids = reality.get("shortIds") or reality.get("shortId")
        clients = inbound.get("settings", {}).get("clients", [])
        if not isinstance(clients, list):
            clients = []
        rows.append((tag, port, short_ids, clients))
    return rows


def list_vless_clients(config: dict) -> list[tuple[str, int | None, str, str, str | None]]:
    rows: list[tuple[str, int | None, str, str, str | None]] = []
    for tag, port, _, clients in list_vless_inbounds(config):
        for client in clients:
            rows.append(
                (
                    tag,
                    port,
                    str(client.get("id", "")),
                    str(client.get("email", "")),
                    client.get("flow"),
                )
            )
    return rows


def find_outbound(config: dict, tag: str) -> dict | None:
    for outbound in config.get("outbounds", []):
        if outbound.get("tag") == tag:
            return outbound
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose VPN entry Xray config")
    parser.add_argument(
        "--config",
        default="/usr/local/etc/xray/config.json",
        help="Path to xray config.json",
    )
    parser.add_argument("--uuid", default="", help="Client UUID to locate")
    parser.add_argument("--xray-bin", default="xray")
    args = parser.parse_args()

    path = Path(args.config)
    if not path.is_file():
        print(f"ERROR: config not found: {path}", file=sys.stderr)
        return 1

    config = load_config(path)
    clients = list_vless_clients(config)

    print(f"Config: {path}")
    print(f"VLESS clients: {len(clients)}")
    print()

    by_inbound: dict[str, tuple[object, list]] = {}
    for tag, port, short_ids, clients in list_vless_inbounds(config):
        key = f"{tag}:{port}"
        items = [
            (str(client.get("id", "")), str(client.get("email", "")), client.get("flow"))
            for client in clients
        ]
        by_inbound[key] = (short_ids, items)

    for key, (short_ids, items) in by_inbound.items():
        print(f"=== inbound {key} ===")
        print(f"  reality shortIds: {short_ids}")
        for uuid, email, flow in items:
            marker = " <-- TARGET" if args.uuid and uuid == args.uuid else ""
            print(f"  {uuid}  {email}  flow={flow}{marker}")
        print()

    if args.uuid:
        matches = [row for row in clients if row[2] == args.uuid]
        if not matches:
            print(f"UUID {args.uuid} NOT FOUND in any vless inbound")
            print("Bot link will NOT work until UUID is in users-in (port 2053).")
        else:
            tag, port, _, email, _ = matches[0]
            print(f"UUID found: inbound={tag} port={port} email={email}")
            if tag != "users-in" or port != 2053:
                print(
                    "WARNING: link uses 51.250.112.128:2053 (users-in) "
                    f"but UUID is in {tag}:{port}. Fix XRAY_INBOUND_TAG on agent :8443."
                )
        print()

    bridge = find_outbound(config, "to-lithuania")
    if bridge is None:
        print("ERROR: outbound 'to-lithuania' missing — relay will not work")
    else:
        vnext = bridge.get("settings", {}).get("vnext", [{}])[0]
        address = vnext.get("address")
        port = vnext.get("port")
        users = vnext.get("users", [{}])
        bridge_uuid = users[0].get("id") if users else None
        print(f"Outbound to-lithuania: {address}:{port} bridge_uuid={bridge_uuid}")

    fi1 = find_outbound(config, "to-fi1")
    if fi1 is not None:
        vnext = fi1.get("settings", {}).get("vnext", [{}])[0]
        print(f"Outbound to-fi1: {vnext.get('address')}:{vnext.get('port')}")

    print()
    test_cmd = [args.xray_bin, "run", "-test", "-c", str(path)]
    try:
        completed = subprocess.run(test_cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        print(f"Skip config test: {args.xray_bin} not found")
        return 0

    if completed.returncode == 0:
        print("xray -test: OK")
    else:
        print("xray -test: FAILED")
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
