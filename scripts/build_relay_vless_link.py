#!/usr/bin/env python3
"""Build VLESS Reality URI for Russia relay entry (copy to Streisand / v2rayTun)."""

from __future__ import annotations

import argparse
from urllib.parse import quote

try:
    from netagent_common.vless_uri import build_vless_reality_uri
except ModuleNotFoundError:
    def build_vless_reality_uri(
        uuid: str,
        host: str,
        label: str,
        *,
        public_key: str,
        short_id: str,
        sni: str = "www.wikipedia.org",
        flow: str = "xtls-rprx-vision",
        port: int = 443,
    ) -> str:
        params = {
            "encryption": "none",
            "type": "tcp",
            "security": "reality",
            "pbk": public_key,
            "flow": flow,
            "sni": sni,
            "fp": "chrome",
            "sid": short_id,
        }
        query = "&".join(f"{key}={quote(str(value), safe='')}" for key, value in params.items())
        return f"vless://{uuid}@{host}:{port}?{query}#{quote(label)}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build VLESS link for Russia relay inbound")
    parser.add_argument("--host", required=True, help="Russia server IP, e.g. 51.250.112.128")
    parser.add_argument("--port", type=int, default=443)
    parser.add_argument("--uuid", required=True)
    parser.add_argument("--pbk", required=True, help="Reality public key (Russia inbound)")
    parser.add_argument("--sid", default="6ba85179e30d4fc2")
    parser.add_argument("--sni", default="www.wikipedia.org")
    parser.add_argument("--flow", default="xtls-rprx-vision")
    parser.add_argument("--name", default="NetAgent-RU")
    args = parser.parse_args()

    uri = build_vless_reality_uri(
        args.uuid,
        args.host,
        args.name,
        port=args.port,
        public_key=args.pbk,
        short_id=args.sid,
        sni=args.sni,
        flow=args.flow,
    )
    print(uri)


if __name__ == "__main__":
    main()
