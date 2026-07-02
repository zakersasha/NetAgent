from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from bot.billing import BillingClient, BillingError
from netagent_common.traffic import format_traffic
from webapp.templating import ctx, templates

router = APIRouter(prefix="/cabinet")


def _require_user(request: Request) -> int | None:
    return request.session.get("user_id")


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
            format_traffic=format_traffic,
            featured_plan=featured,
        ),
    )


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
