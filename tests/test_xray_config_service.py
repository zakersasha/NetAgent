import json
from pathlib import Path

import pytest

from xray_agent.config_service import XrayConfigService
from xray_agent.errors import ReservedUserError
from xray_agent.models import AddUserRequest
from xray_agent.settings import AgentSettings


def write_config(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "inbounds": [
                    {
                        "tag": "vless-reality-in",
                        "protocol": "vless",
                        "settings": {
                            "clients": [
                                {
                                    "id": "admin-uuid",
                                    "email": "admin@netagent.local",
                                    "flow": "xtls-rprx-vision",
                                    "limit": 3,
                                }
                            ],
                            "decryption": "none",
                        },
                        "streamSettings": {
                            "network": "tcp",
                            "security": "reality",
                            "realitySettings": {
                                "serverNames": ["www.wikipedia.org"],
                                "shortIds": ["6ba85179e30d4fc2"],
                            },
                        },
                    }
                ],
                "outbounds": [{"protocol": "freedom"}],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def settings(config_path: Path) -> AgentSettings:
    return AgentSettings(
        xray_config_path=config_path,
        xray_test_cmd="",
        xray_reload_cmd="",
        agent_api_key="test-key",
        agent_reserved_emails={"admin@netagent.local"},
        reality_public_key="test-public-key",
    )


def test_add_user_writes_limit_and_keeps_reserved_out_of_paying_count(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_config(config_path)
    service = XrayConfigService(settings(config_path))

    response = service.add_user(
        AddUserRequest(uuid="user-uuid", email="user_1@netagent.local", limit=2)
    )

    assert response.limit == 2
    assert "pbk=test-public-key" in (response.connection_uri or "")
    count = service.count_users()
    assert count.total == 2
    assert count.reserved == 1
    assert count.paying == 1


def test_add_existing_user_updates_limit(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_config(config_path)
    service = XrayConfigService(settings(config_path))

    service.add_user(AddUserRequest(uuid="user-uuid", email="user_1@netagent.local", limit=1))
    service.add_user(AddUserRequest(uuid="user-uuid", email="user_1@netagent.local", limit=3))

    user = next(item for item in service.list_users() if item.uuid == "user-uuid")
    assert user.limit == 3


def test_reserved_user_cannot_be_removed(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_config(config_path)
    service = XrayConfigService(settings(config_path))

    with pytest.raises(ReservedUserError):
        service.remove_user("admin-uuid")
