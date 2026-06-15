import argparse
import json
import os
import sys
from uuid import uuid4

from xray_client import XrayAgentClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NetAgent Xray Agent CLI")
    parser.add_argument(
        "--url",
        default=os.getenv("XRAY_AGENT_URL", "https://45.93.137.80:8443"),
        help="Xray Agent base URL",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("XRAY_AGENT_API_KEY", "change-me"),
        help="Xray Agent API key",
    )
    parser.add_argument(
        "--verify-ssl",
        action="store_true",
        default=os.getenv("XRAY_AGENT_VERIFY_SSL", "false").lower() == "true",
        help="Verify Agent TLS certificate",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("health")
    subparsers.add_parser("count")

    add = subparsers.add_parser("add")
    add.add_argument("--email", required=True)
    add.add_argument("--uuid", default=str(uuid4()))
    add.add_argument("--limit", required=True, type=int, choices=[1, 2, 3])

    remove = subparsers.add_parser("remove")
    remove.add_argument("--uuid", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    client = XrayAgentClient(
        base_url=args.url,
        api_key=args.api_key,
        verify_ssl=args.verify_ssl,
    )

    if args.command == "health":
        result = client.health()
    elif args.command == "count":
        result = client.users_count()
    elif args.command == "add":
        result = client.add_user(email=args.email, uuid=args.uuid, limit=args.limit)
    elif args.command == "remove":
        result = client.remove_user(uuid=args.uuid)
    else:
        raise AssertionError(f"Unknown command: {args.command}")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
