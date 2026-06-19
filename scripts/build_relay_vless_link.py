#!/usr/bin/env python3
"""Build VLESS Reality URI for Russia relay entry (copy to Streisand / v2rayTun)."""

import argparse

from netagent_common.vless_uri import build_vless_reality_uri


def main() -> None:
    parser = argparse.ArgumentParser(description="Build VLESS link for Russia relay inbound")
    parser.add_argument("--host", required=True, help="Russia server IP, e.g. 37.230.114.25")
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
