from unittest.mock import MagicMock, patch

import httpx
import pytest

from netagent_common.openai_client import OpenAIChatClient, OpenAIClientError


def test_openai_returns_content() -> None:
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"choices": [{"message": {"content": "Ответ"}}]}

    with patch("httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__.return_value.post.return_value = response
        client = OpenAIChatClient(api_keys=("key-a", "key-b"))
        assert client.complete("вопрос") == "Ответ"


def test_openai_retries_second_key() -> None:
    ok_response = MagicMock()
    ok_response.raise_for_status = MagicMock()
    ok_response.json.return_value = {"choices": [{"message": {"content": "OK"}}]}

    fail_response = MagicMock()
    fail_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "fail",
        request=MagicMock(),
        response=MagicMock(status_code=500),
    )

    with patch("httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__.return_value.post.side_effect = [
            fail_response,
            ok_response,
        ]
        client = OpenAIChatClient(api_keys=("key-a", "key-b"))
        assert client.complete("test") == "OK"


def test_openai_all_fail() -> None:
    client = OpenAIChatClient(api_keys=("bad-key"))
    with patch("httpx.Client", side_effect=httpx.ConnectError("down")):
        with pytest.raises(OpenAIClientError):
            client.complete("x")
