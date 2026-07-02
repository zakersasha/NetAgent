from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from bot.billing import BillingClient, BillingError
from bot.messages import support_notify_text
from bot.support_service import SupportService
from webapp.telegram_notify import send_telegram_message
from webapp.templating import ctx, templates

router = APIRouter(prefix="/cabinet")


def _require_user(request: Request) -> int | None:
    return request.session.get("user_id")


async def _notify_admin(request: Request, ticket_id: int, telegram_id: int | None, category: str | None, message: str, source: str) -> None:
    settings = request.app.state.settings
    notify_id = settings.support_notify_telegram_id
    token = settings.telegram_bot_token.strip()
    if not notify_id or not token:
        return
    text = support_notify_text(ticket_id, telegram_id or 0, category, message)
    text += f"\n\n📨 Источник: {source}"
    try:
        await send_telegram_message(token, notify_id, text)
    except Exception:
        pass


@router.get("")
async def cabinet_index(request: Request):
    user_id = _require_user(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    billing: BillingClient = request.app.state.billing
    status = billing.get_account_status_for_user(user_id)
    plans = billing.plans("shop")
    featured = next((p for p in plans if p.slug == "combo"), None)
    return templates.TemplateResponse(
        "cabinet.html",
        ctx(
            request,
            account=status,
            featured_plan=featured,
        ),
    )


@router.get("/support")
async def support_form(request: Request):
    user_id = _require_user(request)
    if not user_id:
        return RedirectResponse("/login?next=/cabinet/support", status_code=303)

    support: SupportService = request.app.state.support
    tickets = support.list_tickets_for_user(user_id)
    return templates.TemplateResponse(
        "support.html",
        ctx(request, tickets=tickets),
    )


@router.post("/support")
async def support_submit(
    request: Request,
    message: str = Form(...),
    category: str = Form(""),
):
    user_id = _require_user(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    support: SupportService = request.app.state.support
    cat = category.strip() or None
    try:
        ticket = support.create_ticket_for_user_id(user_id, message, cat)
    except ValueError as exc:
        tickets = support.list_tickets_for_user(user_id)
        return templates.TemplateResponse(
            "support.html",
            ctx(request, tickets=tickets, error=str(exc)),
            status_code=400,
        )

    await _notify_admin(request, ticket.id, ticket.telegram_id, cat, message.strip(), "сайт")
    return RedirectResponse("/cabinet/support?sent=1", status_code=303)


@router.get("/plans/{plan_slug}")
async def checkout(request: Request, plan_slug: str):
    user_id = _require_user(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    billing: BillingClient = request.app.state.billing
    plan = billing.get_plan(plan_slug)
    if not plan:
        return RedirectResponse("/cabinet", status_code=303)
    return templates.TemplateResponse(
        "checkout.html",
        ctx(request, plan=plan),
    )


@router.post("/pay/{plan_slug}")
async def mock_pay(request: Request, plan_slug: str):
    user_id = _require_user(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    billing: BillingClient = request.app.state.billing
    try:
        billing.activate_mock_payment_for_user(user_id, plan_slug)
    except BillingError as exc:
        plan = billing.get_plan(plan_slug)
        return templates.TemplateResponse(
            "checkout.html",
            ctx(request, plan=plan, error=str(exc)),
            status_code=400,
        )
    return RedirectResponse("/cabinet?paid=1", status_code=303)


@router.post("/regenerate-key")
async def regenerate_key(request: Request):
    user_id = _require_user(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    billing: BillingClient = request.app.state.billing
    try:
        billing.regenerate_vpn_key_for_user(user_id)
    except Exception:
        pass
    return RedirectResponse("/cabinet", status_code=303)
