import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from bot.messages import payment_success_text
from netagent_common.payment_service import PaymentService
from webapp.telegram_notify import send_telegram_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payments")


@router.post("/webhook/yookassa")
async def yookassa_webhook(request: Request) -> JSONResponse:
    payment_service: PaymentService | None = request.app.state.payment_service
    if not payment_service:
        return JSONResponse({"status": "ignored"})

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"status": "bad_request"}, status_code=400)

    if not isinstance(payload, dict):
        return JSONResponse({"status": "bad_request"}, status_code=400)

    try:
        result = payment_service.handle_yookassa_webhook(payload)
    except Exception:
        logger.exception("YooKassa webhook processing failed")
        return JSONResponse({"status": "error"}, status_code=500)

    if result and result.telegram_id:
        settings = request.app.state.settings
        token = settings.telegram_bot_token.strip()
        if token:
            text = payment_success_text(result.subscription)
            markup = {
                "inline_keyboard": [
                    [{"text": "📋 Моя подписка", "callback_data": "account"}],
                ]
            }
            try:
                await send_telegram_message(
                    token,
                    result.telegram_id,
                    text,
                    reply_markup=markup,
                )
            except Exception:
                logger.exception("Failed to notify telegram_id=%s about payment", result.telegram_id)

    return JSONResponse({"status": "ok"})
