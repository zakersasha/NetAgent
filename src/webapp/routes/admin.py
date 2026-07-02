from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from bot.support_service import SupportService
from webapp.stats import AdminStatsService
from webapp.telegram_notify import send_telegram_message
from webapp.templating import ctx, templates

router = APIRouter(prefix="/admin")


def _require_admin(request: Request) -> int | None:
    return request.session.get("admin_id")


@router.get("")
async def admin_dashboard(request: Request):
    if not _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    stats: AdminStatsService = request.app.state.stats
    dashboard = stats.dashboard()
    recent_payments = stats.list_payments(limit=10)
    return templates.TemplateResponse(
        "admin/dashboard.html",
        ctx(request, dashboard=dashboard, recent_payments=recent_payments),
    )


@router.get("/users")
async def admin_users(request: Request):
    if not _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    stats: AdminStatsService = request.app.state.stats
    users = stats.list_users()
    return templates.TemplateResponse(
        "admin/users.html",
        ctx(request, users=users),
    )


@router.get("/payments")
async def admin_payments(request: Request):
    if not _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    stats: AdminStatsService = request.app.state.stats
    payments = stats.list_payments(limit=100)
    return templates.TemplateResponse(
        "admin/payments.html",
        ctx(request, payments=payments),
    )


@router.get("/plans")
async def admin_plans(request: Request):
    if not _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    stats: AdminStatsService = request.app.state.stats
    plans = stats.list_plans()
    return templates.TemplateResponse(
        "admin/plans.html",
        ctx(request, plans=plans),
    )


@router.get("/support")
async def admin_support(request: Request):
    if not _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    stats: AdminStatsService = request.app.state.stats
    tickets = stats.list_support_tickets()
    return templates.TemplateResponse(
        "admin/support.html",
        ctx(request, tickets=tickets),
    )


@router.get("/support/{ticket_id}")
async def admin_support_detail(request: Request, ticket_id: int):
    if not _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    stats: AdminStatsService = request.app.state.stats
    ticket = stats.get_support_ticket_row(ticket_id)
    if not ticket:
        return RedirectResponse("/admin/support", status_code=303)
    return templates.TemplateResponse(
        "admin/support_detail.html",
        ctx(request, ticket=ticket),
    )


@router.post("/support/{ticket_id}/reply")
async def admin_support_reply(
    request: Request,
    ticket_id: int,
    reply: str = Form(...),
):
    if not _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    support: SupportService = request.app.state.support
    settings = request.app.state.settings
    try:
        ticket = support.reply_to_ticket(ticket_id, reply)
    except ValueError as exc:
        stats: AdminStatsService = request.app.state.stats
        row = stats.get_support_ticket_row(ticket_id)
        return templates.TemplateResponse(
            "admin/support_detail.html",
            ctx(request, ticket=row, error=str(exc)),
            status_code=400,
        )

    token = settings.telegram_bot_token.strip()
    if ticket.telegram_id and token:
        user_text = (
            f"💬 <b>Ответ поддержки</b> (#{ticket.id})\n\n"
            f"{reply.strip()}\n\n"
            "Если вопрос остался — напишите снова в «Поддержку»."
        )
        try:
            await send_telegram_message(token, ticket.telegram_id, user_text)
        except Exception:
            pass

    return RedirectResponse(f"/admin/support/{ticket_id}?sent=1", status_code=303)
