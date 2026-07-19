#!/usr/bin/env python3
"""Remove stale VLESS clients from entry Xray config (after Postgres volume wipe).

Postgres lives on Moscow Docker; Xray config on provmonstage is separate.
Wiping DB volumes creates new UUIDs in the bot while old clients stay in config.json.

Usage on provmonstage:
  python3 scripts/clean_entry_clients.py --list
  python3 scripts/clean_entry_clients.py --keep-email 653663497_vpn --apply \\
    --restart 'sudo systemctl restart xray'

  # config lives in /usr/local/etc/xray — apply needs root:
  sudo python3 scripts/clean_entry_clients.py --keep-email 653663497_vpn --apply \\
    --restart 'systemctl restart xray'

Keep admin/family profile only (also reads AGENT_RESERVED_* from env or --env-file):
  python3 scripts/clean_entry_clients.py --env-file /opt/xray-agent/.env --apply --restart '...'
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile


def parse_csv(value: str) -> set[str]:
    return {item.strip() for item in value.split(",") if item.strip()}


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, raw = line.partition("=")
        values[key.strip()] = raw.strip().strip("'\"")
    return values


def is_reserved(client: dict, keep_emails: set[str], keep_uuids: set[str]) -> bool:
    email = str(client.get("email", ""))
    uuid = str(client.get("id", ""))
    return email in keep_emails or uuid in keep_uuids


def iter_vless_clients(
    config: dict,
    inbound_tags: set[str] | None,
) -> list[tuple[str, int | None, dict]]:
    rows: list[tuple[str, int | None, dict]] = []
    for inbound in config.get("inbounds", []):
        if inbound.get("protocol") != "vless":
            continue
        tag = str(inbound.get("tag", ""))
        if inbound_tags and tag not in inbound_tags:
            continue
        port = inbound.get("port")
        for client in inbound.get("settings", {}).get("clients", []):
            if isinstance(client, dict):
                rows.append((tag, port, client))
    return rows


def clean_config(
    config: dict,
    *,
    keep_emails: set[str],
    keep_uuids: set[str],
    inbound_tags: set[str] | None,
) -> tuple[dict, list[tuple[str, str, str]]]:
    removed: list[tuple[str, str, str]] = []
    for inbound in config.get("inbounds", []):
        if inbound.get("protocol") != "vless":
            continue
        tag = str(inbound.get("tag", ""))
        if inbound_tags and tag not in inbound_tags:
            continue
        clients = inbound.setdefault("settings", {}).setdefault("clients", [])
        if not isinstance(clients, list):
            continue
        kept: list[dict] = []
        for client in clients:
            if is_reserved(client, keep_emails, keep_uuids):
                kept.append(client)
            else:
                removed.append((tag, str(client.get("id", "")), str(client.get("email", ""))))
        inbound["settings"]["clients"] = kept
    return config, removed


def config_is_writable(path: Path) -> bool:
    return os.access(path, os.W_OK) and os.access(path.parent, os.W_OK)


def make_backup(path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup = Path(tempfile.gettempdir()) / f"netagent-{path.name}.{stamp}.bak"
    shutil.copy2(path, backup)
    return backup


def restore_backup(backup: Path, path: Path) -> None:
    shutil.copy2(backup, path)
    _ensure_world_readable(path)


def _ensure_world_readable(path: Path) -> None:
    """Xray systemd unit runs as User=nobody — config must be world-readable."""
    path.chmod(0o644)


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove paying clients from entry Xray config")
    parser.add_argument(
        "--config",
        default=os.environ.get("XRAY_CONFIG_PATH", "/usr/local/etc/xray/config.json"),
    )
    parser.add_argument(
        "--keep-email",
        action="append",
        default=[],
        help="Email to preserve (repeatable). Also reads AGENT_RESERVED_EMAILS from env.",
    )
    parser.add_argument(
        "--keep-uuid",
        action="append",
        default=[],
        help="UUID to preserve (repeatable). Also reads AGENT_RESERVED_UUIDS from env.",
    )
    parser.add_argument(
        "--inbound",
        action="append",
        default=[],
        help="Only these inbound tags (default: all vless). E.g. --inbound users-in",
    )
    parser.add_argument(
        "--env-file",
        default="",
        help="Load AGENT_RESERVED_EMAILS / AGENT_RESERVED_UUIDS from agent .env",
    )
    parser.add_argument("--list", action="store_true", help="List all vless clients and keep/remove status")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed")
    parser.add_argument("--apply", action="store_true", help="Write config changes")
    parser.add_argument("--restart", default="", help="Shell command after apply, e.g. systemctl restart xray")
    parser.add_argument("--xray-bin", default=os.environ.get("XRAY_BIN", "xray"))
    args = parser.parse_args()

    path = Path(args.config)
    if not path.is_file():
        print(f"ERROR: config not found: {path}", file=sys.stderr)
        return 1

    keep_emails = set(args.keep_email) | parse_csv(os.environ.get("AGENT_RESERVED_EMAILS", ""))
    keep_uuids = set(args.keep_uuid) | parse_csv(os.environ.get("AGENT_RESERVED_UUIDS", ""))
    if args.env_file:
        env = load_env_file(Path(args.env_file))
        keep_emails |= parse_csv(env.get("AGENT_RESERVED_EMAILS", ""))
        keep_uuids |= parse_csv(env.get("AGENT_RESERVED_UUIDS", ""))
    inbound_tags = set(args.inbound) if args.inbound else None

    original = json.loads(path.read_text(encoding="utf-8"))

    if args.list:
        rows = iter_vless_clients(original, inbound_tags)
        if not rows:
            print("No vless clients found.")
            return 0
        print(f"{'KEEP' if keep_emails or keep_uuids else 'STAT':<6}  {'INBOUND':<16}  {'PORT':<6}  UUID  EMAIL")
        for tag, port, client in rows:
            reserved = is_reserved(client, keep_emails, keep_uuids)
            mark = "KEEP" if reserved else "REMOVE"
            if not (keep_emails or keep_uuids):
                mark = "----"
            print(
                f"{mark:<6}  {tag:<16}  {str(port or ''):<6}  "
                f"{client.get('id', '')}  {client.get('email', '')}"
            )
        if not (keep_emails or keep_uuids):
            print("\nPass --keep-email / --keep-uuid (or AGENT_RESERVED_*) to mark what stays.")
        return 0

    if not keep_emails and not keep_uuids:
        print("WARNING: no --keep-email / --keep-uuid — ALL vless clients will be removed.", file=sys.stderr)
        print("Use --list first, then pass your admin profile.", file=sys.stderr)

    if keep_emails or keep_uuids:
        print("Keeping:")
        for email in sorted(keep_emails):
            print(f"  email: {email}")
        for uuid in sorted(keep_uuids):
            print(f"  uuid:  {uuid}")
        print()

    updated, removed = clean_config(
        original,
        keep_emails=keep_emails,
        keep_uuids=keep_uuids,
        inbound_tags=inbound_tags,
    )

    if not removed:
        print("Nothing to remove — no non-reserved clients found.")
        return 0

    print(f"Will remove {len(removed)} client(s):")
    for tag, uuid, email in removed:
        print(f"  [{tag}] {uuid}  {email}")

    if args.dry_run or not args.apply:
        if not args.apply:
            print("\nDry-run only. Pass --apply to write changes.")
        return 0

    if not config_is_writable(path):
        print(f"ERROR: no write permission for {path}", file=sys.stderr)
        print("Re-run with sudo, e.g.:", file=sys.stderr)
        print(
            "  sudo python3 scripts/clean_entry_clients.py "
            f"--keep-email ... --apply --restart 'systemctl restart xray'",
            file=sys.stderr,
        )
        return 1

    test_cmd = [args.xray_bin, "run", "-test", "-c", str(path)]
    backup = make_backup(path)
    print(f"\nBackup: {backup}")

    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        json.dump(updated, tmp, ensure_ascii=False, indent=2)
        tmp.write("\n")
        temp_path = Path(tmp.name)

    temp_path.replace(path)
    _ensure_world_readable(path)

    result = subprocess.run(test_cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        restore_backup(backup, path)
        print("xray -test FAILED, config restored from backup", file=sys.stderr)
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        return 1

    print("xray -test: OK")

    restart_cmd = args.restart
    if restart_cmd.startswith("sudo ") and os.geteuid() == 0:
        restart_cmd = restart_cmd.removeprefix("sudo ").strip()

    if restart_cmd:
        restart = subprocess.run(restart_cmd, shell=True, capture_output=True, text=True, check=False)
        if restart.returncode != 0:
            print(f"Restart failed: {restart_cmd}", file=sys.stderr)
            print(restart.stdout)
            print(restart.stderr, file=sys.stderr)
            return 1
        print(f"Restarted: {restart_cmd}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
