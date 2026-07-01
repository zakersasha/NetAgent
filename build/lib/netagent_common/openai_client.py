from typing import Any

import httpx

from netagent_common.proxy_urls import ProxyRotator


class OpenAIClientError(Exception):
    """OpenAI API request failed."""


class OpenAIChatClient:
    def __init__(
        self,
        api_keys: tuple[str, ...],
        model: str = "gpt-4o-mini",
        proxy_rotator: ProxyRotator | None = None,
        timeout_seconds: float = 120.0,
        system_prompt: str = "",
    ) -> None:
        keys = tuple(key.strip() for key in api_keys if key and key.strip())
        if not keys:
            raise ValueError("At least one OpenAI API key is required")
        self._api_keys = keys
        self._key_index = 0
        self._model = model.strip() or "gpt-4o-mini"
        self._proxy_rotator = proxy_rotator or ProxyRotator(())
        self._timeout = timeout_seconds
        self._system_prompt = system_prompt.strip()

    def complete(self, user_message: str) -> str:
        message = user_message.strip()
        if not message:
            raise OpenAIClientError("Пустое сообщение")

        keys = self._key_order()
        proxies = self._proxy_rotator.cycle()
        last_error: Exception | None = None

        for proxy in proxies:
            for api_key in keys:
                try:
                    return self._request(api_key, message, proxy)
                except (httpx.HTTPError, OpenAIClientError) as exc:
                    last_error = exc
                    continue

        if last_error:
            raise OpenAIClientError(f"OpenAI недоступен: {last_error}") from last_error
        raise OpenAIClientError("OpenAI недоступен")

    def _key_order(self) -> list[str]:
        start = self._key_index % len(self._api_keys)
        ordered = self._api_keys[start:] + self._api_keys[:start]
        self._key_index += 1
        return list(ordered)

    def _request(self, api_key: str, user_message: str, proxy: str | None) -> str:
        messages: list[dict[str, str]] = []
        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})
        messages.append({"role": "user", "content": user_message})

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.7,
        }

        with httpx.Client(
            timeout=self._timeout,
            proxy=proxy or None,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        ) as client:
            response = client.post("https://api.openai.com/v1/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise OpenAIClientError("Некорректный ответ OpenAI") from exc

        text = str(content).strip()
        if not text:
            raise OpenAIClientError("Пустой ответ модели")
        return text
