"""Tests for XrayProvisioner."""

from unittest.mock import MagicMock

import pytest

from bot.xray_provisioner import XrayProvisioner, XrayProvisionerError
from xray_client.client import XrayAgentClientError


def test_provision_without_client_not_required() -> None:
    provisioner = XrayProvisioner(client=None, required=False)
    provisioner.provision_key(email="1_phone", uuid="uuid-1")


def test_provision_without_client_required_raises() -> None:
    provisioner = XrayProvisioner(client=None, required=True)
    with pytest.raises(XrayProvisionerError, match="не настроен"):
        provisioner.provision_key(email="1_phone", uuid="uuid-1")


def test_provision_calls_add_user() -> None:
    client = MagicMock()
    provisioner = XrayProvisioner(client=client, required=True)
    provisioner.provision_key(email="99_phone", uuid="abc")
    client.add_user.assert_called_once_with(email="99_phone", uuid="abc", limit=1)


def test_provision_agent_error() -> None:
    client = MagicMock()
    client.add_user.side_effect = XrayAgentClientError("boom")
    provisioner = XrayProvisioner(client=client, required=True)
    with pytest.raises(XrayProvisionerError, match="добавить ключ"):
        provisioner.provision_key(email="99_phone", uuid="abc")


def test_rollback_swallows_remove_error() -> None:
    client = MagicMock()
    client.remove_user.side_effect = XrayAgentClientError("missing")
    provisioner = XrayProvisioner(client=client, required=True)
    provisioner.rollback_key(uuid="abc")
    client.remove_user.assert_called_once_with(uuid="abc")
