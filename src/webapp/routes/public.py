from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from webapp.templating import ctx, templates

router = APIRouter()


def _split_plans(plans):
    bundles = [p for p in plans if p.product_type == "bundle"]
    vpns = [p for p in plans if p.product_type == "vpn"]
    ais = [p for p in plans if p.product_type == "ai"]
    featured = next((p for p in plans if p.slug == "combo"), bundles[0] if bundles else None)
    return bundles, vpns, ais, featured


@router.get("/")
async def landing(request: Request):
    billing = request.app.state.billing
    plans = billing.plans("shop")
    bundles, vpns, ais, featured = _split_plans(plans)
    return templates.TemplateResponse(
        "landing.html",
        ctx(
            request,
            plans=plans,
            bundle_plans=bundles,
            vpn_plans=vpns,
            ai_plans=ais,
            featured_plan=featured,
        ),
    )


@router.get("/terms")
async def terms(request: Request):
    return templates.TemplateResponse("terms.html", ctx(request))


@router.get("/privacy")
async def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", ctx(request))


@router.get("/contacts")
async def contacts(request: Request):
    return templates.TemplateResponse("contacts.html", ctx(request))


@router.get("/health")
async def health():
    return {"ok": True}
