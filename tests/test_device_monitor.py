from device_monitor.geo import GeoCountryResolver
from device_monitor.service import apply_traffic_delta, detect_violation, ViolationType


class FakeGeo:
    def __init__(self, mapping: dict[str, str]) -> None:
        self._mapping = mapping

    def country_code(self, ip: str) -> str | None:
        return self._mapping.get(ip)


def test_multiple_ips_triggers_suspension() -> None:
    geo = GeoCountryResolver("")
    violation = detect_violation(["1.0.0.1", "1.0.0.2"], geo, max_online_ips=1)
    assert violation is not None
    assert violation.type == ViolationType.MULTIPLE_IPS


def test_multiple_countries_triggers_suspension() -> None:
    geo = FakeGeo({"1.0.0.1": "RU", "2.0.0.1": "DE"})
    violation = detect_violation(["1.0.0.1", "2.0.0.1"], geo, max_online_ips=2)
    assert violation is not None
    assert violation.type == ViolationType.MULTIPLE_COUNTRIES


def test_single_ip_same_country_is_ok() -> None:
    geo = FakeGeo({"1.0.0.1": "RU"})
    violation = detect_violation(["1.0.0.1"], geo, max_online_ips=1)
    assert violation is None


def test_traffic_delta_handles_xray_restart() -> None:
    used, snapshot = apply_traffic_delta(current_xray_bytes=100, snapshot_bytes=500, used_bytes=1000)
    assert used == 1100
    assert snapshot == 100


def test_traffic_delta_accumulates() -> None:
    used, snapshot = apply_traffic_delta(current_xray_bytes=600, snapshot_bytes=500, used_bytes=1000)
    assert used == 1100
    assert snapshot == 600
