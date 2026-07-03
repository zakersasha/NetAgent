from collections.abc import Callable

from sqlalchemy.orm import Session

from bot.billing import BillingClient
from netagent_common.payment_service import PaymentService
from netagent_common.yookassa_client import YooKassaClient


def build_payment_service(
    *,
    session_factory: Callable[[], Session],
    billing: BillingClient,
    payment_provider: str,
    service_name: str,
    yookassa_shop_id: str,
    yookassa_secret_key: str,
    yookassa_return_url: str,
) -> PaymentService | None:
    if payment_provider.strip().lower() != "yookassa":
        return None

    client = YooKassaClient(yookassa_shop_id, yookassa_secret_key)
    if not client.configured:
        raise RuntimeError("PAYMENT_PROVIDER=yookassa, но YOOKASSA_SHOP_ID / YOOKASSA_SECRET_KEY не заданы")
    if not yookassa_return_url.strip():
        raise RuntimeError("Задайте YOOKASSA_RETURN_URL (HTTPS-страница возврата после оплаты)")

    return PaymentService(
        session_factory=session_factory,
        billing=billing,
        yookassa=client,
        service_name=service_name,
        return_url=yookassa_return_url.strip(),
    )
