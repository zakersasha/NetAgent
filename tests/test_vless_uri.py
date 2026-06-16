from urllib.parse import quote

from netagent_common.vless_uri import build_vless_reality_uri


def test_build_vless_reality_uri_matches_admin_format() -> None:
    uri = build_vless_reality_uri(
        "6f176e02-bae9-4998-8bb4-099cbb21212c",
        "45.93.137.80",
        "MyVPN",
        public_key="YTQ_dIa_739_d6x7OUAd3XjMbpX3UOnWBMkGVtEhi18",
        short_id="6ba85179e30d4fc3",
    )

    assert uri.startswith("vless://6f176e02-bae9-4998-8bb4-099cbb21212c@45.93.137.80:443?")
    assert "type=tcp" in uri
    assert "security=reality" in uri
    assert "pbk=YTQ_dIa_739_d6x7OUAd3XjMbpX3UOnWBMkGVtEhi18" in uri
    assert "flow=xtls-rprx-vision" in uri
    assert "sni=www.wikipedia.org" in uri
    assert "sid=6ba85179e30d4fc3" in uri
    assert uri.endswith(f"#{quote('MyVPN')}")
