import json
import os
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
        agent_reserved_emails="admin@netagent.local",
        reality_public_key="test-public-key",
    )


def test_add_user_writes_minimal_client_and_keeps_reserved_out_of_paying_count(
    tmp_path: Path,
) -> None:
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

    saved = json.loads(config_path.read_text(encoding="utf-8"))
    clients = saved["inbounds"][0]["settings"]["clients"]
    user = next(client for client in clients if client["id"] == "user-uuid")
    admin = next(client for client in clients if client["id"] == "admin-uuid")
    assert "limit" not in user
    assert "level" not in user
    assert "limit" not in admin
    assert "level" not in admin
    assert "policy" not in saved


def test_add_existing_user_updates_limit(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_config(config_path)
    service = XrayConfigService(settings(config_path))

    service.add_user(AddUserRequest(uuid="user-uuid", email="user_1@netagent.local", limit=1))
    service.add_user(AddUserRequest(uuid="user-uuid", email="user_1@netagent.local", limit=3))

    saved = json.loads(config_path.read_text(encoding="utf-8"))
    clients = saved["inbounds"][0]["settings"]["clients"]
    user = next(client for client in clients if client["id"] == "user-uuid")
    assert user["email"] == "user_1@netagent.local"
    assert user["flow"] == "xtls-rprx-vision"
    assert "limit" not in user
    assert "level" not in user


def test_add_user_moves_email_from_other_inbound(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "inbounds": [
                    {
                        "tag": "users-in",
                        "protocol": "vless",
                        "settings": {
                            "clients": [
                                {
                                    "id": "old-uuid",
                                    "email": "544709692_vpn",
                                    "flow": "xtls-rprx-vision",
                                }
                            ],
                            "decryption": "none",
                        },
                    },
                    {
                        "tag": "users-in-fi1",
                        "protocol": "vless",
                        "settings": {"clients": [], "decryption": "none"},
                    },
                ],
                "outbounds": [{"protocol": "freedom"}],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    fi1_settings = AgentSettings(
        xray_config_path=config_path,
        xray_inbound_tag="users-in-fi1",
        xray_test_cmd="",
        xray_reload_cmd="",
        agent_api_key="test-key",
        reality_public_key="test-public-key",
    )
    service = XrayConfigService(fi1_settings)
    service.add_user(AddUserRequest(uuid="new-uuid", email="544709692_vpn", limit=1))

    saved = json.loads(config_path.read_text(encoding="utf-8"))
    lt1_clients = saved["inbounds"][0]["settings"]["clients"]
    fi1_clients = saved["inbounds"][1]["settings"]["clients"]
    assert lt1_clients == []
    assert len(fi1_clients) == 1
    assert fi1_clients[0]["id"] == "new-uuid"
    assert fi1_clients[0]["email"] == "544709692_vpn"


def test_add_user_upserts_same_email_with_new_uuid(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_config(config_path)
    service = XrayConfigService(settings(config_path))

    service.add_user(AddUserRequest(uuid="old-uuid", email="544709692_vpn", limit=1))
    service.add_user(AddUserRequest(uuid="new-uuid", email="544709692_vpn", limit=1))

    saved = json.loads(config_path.read_text(encoding="utf-8"))
    clients = saved["inbounds"][0]["settings"]["clients"]
    paying = [client for client in clients if client.get("email") == "544709692_vpn"]
    assert len(paying) == 1
    assert paying[0]["id"] == "new-uuid"


def test_reserved_user_cannot_be_removed(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_config(config_path)
    service = XrayConfigService(settings(config_path))

    with pytest.raises(ReservedUserError):
        service.remove_user("admin-uuid")


@pytest.mark.skipif(os.name == "nt", reason="POSIX file modes are not enforced on Windows")
def test_atomic_write_preserves_readable_config_permissions(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_config(config_path)
    config_path.chmod(0o644)
    service = XrayConfigService(settings(config_path))

    service.add_user(AddUserRequest(uuid="user-uuid", email="user_1@netagent.local", limit=1))

    assert os.stat(config_path).st_mode & 0o777 == 0o644
