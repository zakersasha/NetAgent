from pathlib import Path

from bot.billing import BillingClient
from bot.xray_provisioner import XrayProvisioner
from netagent_common.payment_factory import build_payment_service
from netagent_common.payment_service import PaymentService
from netagent_db.session import create_session_factory
from bot.support_service import SupportService
from webapp.settings import WebSettings
from webapp.stats import AdminStatsService
from xray_client.client import XrayAgentClient


def build_payment(settings: WebSettings, billing: BillingClient) -> PaymentService | None:
    session_factory = create_session_factory(settings.database_url)
    return build_payment_service(
        session_factory=session_factory,
        billing=billing,
        payment_provider=settings.payment_provider,
        service_name=settings.service_name,
        yookassa_shop_id=settings.yookassa_shop_id,
        yookassa_secret_key=settings.yookassa_secret_key,
        yookassa_return_url=settings.yookassa_return_url,
    )


def build_billing(settings: WebSettings) -> BillingClient:
    agent_url = settings.xray_agent_url.strip()
    xray_agent = None
    if agent_url:
        xray_agent = XrayAgentClient(
            base_url=agent_url,
            api_key=settings.xray_agent_api_key,
            verify_ssl=settings.xray_agent_verify_ssl,
            timeout_seconds=settings.xray_agent_timeout_seconds,
        )
    provisioner = XrayProvisioner(client=xray_agent, required=bool(agent_url))
    session_factory = create_session_factory(settings.database_url)
    return BillingClient(
        session_factory=session_factory,
        public_host=settings.xray_public_host,
        public_port=settings.xray_public_port,
        timezone=settings.timezone,
        reality_public_key=settings.reality_public_key,
        reality_sni=settings.reality_sni,
        reality_short_id=settings.reality_short_id,
        vless_flow=settings.vless_flow,
        xray_provisioner=provisioner,
        xray_agent_api_key=settings.xray_agent_api_key,
        xray_agent_verify_ssl=settings.xray_agent_verify_ssl,
        xray_agent_timeout_seconds=settings.xray_agent_timeout_seconds,
        ai_free_daily_limit=settings.ai_free_daily_limit,
    )


def build_stats(settings: WebSettings) -> AdminStatsService:
    session_factory = create_session_factory(settings.database_url)
    return AdminStatsService(session_factory)


def build_support(settings: WebSettings) -> SupportService:
    session_factory = create_session_factory(settings.database_url)
    return SupportService(session_factory=session_factory)


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"
