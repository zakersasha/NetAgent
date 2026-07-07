import json
from datetime import datetime
from typing import Any


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def extract_yookassa_payment_details(payment_obj: dict[str, Any]) -> dict[str, Any]:
    """Extract audit fields from YooKassa payment object (webhook or API)."""
    payment_method = payment_obj.get("payment_method") or {}
    receipt = payment_obj.get("receipt") or {}
    receipt_registration = payment_obj.get("receipt_registration")

    fiscal_document_number = None
    fiscal_storage_number = None
    fiscal_attribute = None
    receipt_registered_at = None

    if isinstance(receipt, dict):
        fiscal_document_number = (
            receipt.get("fiscal_document_number")
            or receipt.get("fiscal_document_id")
            or receipt.get("fiscal_document")
        )
        fiscal_storage_number = receipt.get("fiscal_storage_number")
        fiscal_attribute = receipt.get("fiscal_attribute")
        receipt_registered_at = _parse_iso(receipt.get("registered_at"))

    if isinstance(receipt_registration, dict):
        fiscal_document_number = fiscal_document_number or receipt_registration.get(
            "fiscal_document_number"
        )
        fiscal_storage_number = fiscal_storage_number or receipt_registration.get(
            "fiscal_storage_number"
        )
        fiscal_attribute = fiscal_attribute or receipt_registration.get("fiscal_attribute")
        receipt_registered_at = receipt_registered_at or _parse_iso(
            receipt_registration.get("registered_at")
        )

    paid_at = _parse_iso(payment_obj.get("captured_at")) or _parse_iso(
        payment_obj.get("created_at")
    )

    return {
        "description": payment_obj.get("description"),
        "paid_at": paid_at,
        "payment_method_type": payment_method.get("type"),
        "payment_method_title": payment_method.get("title"),
        "receipt_fiscal_document_number": _str_or_none(fiscal_document_number),
        "receipt_fiscal_storage_number": _str_or_none(fiscal_storage_number),
        "receipt_fiscal_attribute": _str_or_none(fiscal_attribute),
        "receipt_registered_at": receipt_registered_at,
        "provider_payload": json.dumps(payment_obj, ensure_ascii=False, sort_keys=True),
    }


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
