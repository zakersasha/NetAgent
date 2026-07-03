from decimal import Decimal
from typing import Any

import httpx


class YooKassaError(RuntimeError):
    """YooKassa API error."""


class YooKassaClient:
    def __init__(
        self,
        shop_id: str,
        secret_key: str,
        *,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._shop_id = shop_id.strip()
        self._secret_key = secret_key.strip()
        self._timeout = timeout_seconds

    @property
    def configured(self) -> bool:
        return bool(self._shop_id and self._secret_key)

    def create_payment(
        self,
        *,
        amount_rub: Decimal,
        description: str,
        return_url: str,
        metadata: dict[str, str],
        idempotence_key: str,
    ) -> dict[str, Any]:
        payload = {
            "amount": {
                "value": self._format_amount(amount_rub),
                "currency": "RUB",
            },
            "capture": True,
            "confirmation": {
                "type": "redirect",
                "return_url": return_url,
            },
            "description": description[:128],
            "metadata": metadata,
        }
        return self._request("POST", "/payments", payload, idempotence_key)

    def get_payment(self, payment_id: str) -> dict[str, Any]:
        return self._request("GET", f"/payments/{payment_id}", None, f"get-{payment_id}")

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None,
        idempotence_key: str,
    ) -> dict[str, Any]:
        if not self.configured:
            raise YooKassaError("YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY не заданы")

        headers = {
            "Content-Type": "application/json",
            "Idempotence-Key": idempotence_key,
        }
        url = f"https://api.yookassa.ru/v3{path}"
        with httpx.Client(timeout=self._timeout) as client:
            response = client.request(
                method,
                url,
                json=payload,
                auth=(self._shop_id, self._secret_key),
                headers=headers,
            )
        if response.status_code >= 400:
            raise YooKassaError(f"YooKassa HTTP {response.status_code}: {response.text[:500]}")
        data = response.json()
        if not isinstance(data, dict):
            raise YooKassaError("Unexpected YooKassa response")
        return data

    @staticmethod
    def _format_amount(amount_rub: Decimal) -> str:
        normalized = Decimal(amount_rub).quantize(Decimal("0.01"))
        return f"{normalized:.2f}"
