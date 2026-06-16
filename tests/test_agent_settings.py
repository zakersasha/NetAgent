from xray_agent.settings import AgentSettings, _csv_to_set


def test_csv_to_set() -> None:
    assert _csv_to_set("37.230.114.25") == {"37.230.114.25"}
    assert _csv_to_set("a@x.com, b@x.com") == {"a@x.com", "b@x.com"}
    assert _csv_to_set("") == set()


def test_agent_settings_allowed_ips_from_csv_string() -> None:
    settings = AgentSettings(agent_allowed_ips="37.230.114.25, 1.2.3.4")
    assert settings.allowed_ips() == {"37.230.114.25", "1.2.3.4"}
