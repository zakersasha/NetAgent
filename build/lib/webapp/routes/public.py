from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from webapp.templating import ctx, templates

router = APIRouter()


@router.get("/")
async def landing(request: Request):
    billing = request.app.state.billing
    plans = billing.plans("shop")
    return templates.TemplateResponse(
        "landing.html",
        ctx(request, plans=plans),
    )


@router.get("/health")
async def health():
    return {"ok": True}
