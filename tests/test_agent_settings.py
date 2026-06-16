import pytest

from xray_agent.settings import AgentSettings


def test_reality_public_key_rejects_short_id() -> None:
    with pytest.raises(ValueError, match="REALITY_PUBLIC_KEY"):
        AgentSettings(reality_public_key="6ba85179e30d4fc2")
