from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from webapp.stats import AdminStatsService
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
