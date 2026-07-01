from urllib.parse import quote


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
