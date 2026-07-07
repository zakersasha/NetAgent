import logging
from collections.abc import Callable

from device_monitor.geo import GeoCountryResolver
from device_monitor.service import DeviceMonitorService
from device_monitor.settings import get_monitor_settings
from netagent_common.vpn_nodes import list_active_vpn_nodes
from netagent_db.session import create_session_factory
from xray_client.client import XrayAgentClient

logger = logging.getLogger(__name__)


def _build_agent_factory(
    settings,
) -> tuple[Callable[[str], XrayAgentClient], XrayAgentClient | None]:
    cache: dict[str, XrayAgentClient] = {}

    def get_agent(agent_url: str) -> XrayAgentClient:
        url = agent_url.rstrip("/")
        if url not in cache:
            cache[url] = XrayAgentClient(
                base_url=url,
                api_key=settings.xray_agent_api_key,
                verify_ssl=settings.xray_agent_verify_ssl,
                timeout_seconds=settings.xray_agent_timeout_seconds,
            )
        return cache[url]

    default_url = settings.xray_agent_url.strip().rstrip("/")
    default_agent = get_agent(default_url) if default_url else None
    return get_agent, default_agent


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_monitor_settings()

    if not settings.database_url.strip():
        raise RuntimeError("Задайте DATABASE_URL в .env")
    if not settings.xray_agent_url.strip():
        raise RuntimeError("Задайте XRAY_AGENT_URL в .env")

    session_factory = create_session_factory(settings.database_url)
    get_agent, default_agent = _build_agent_factory(settings)

    with session_factory() as session:
        nodes = list_active_vpn_nodes(session)
    agent_urls = {node.agent_url.rstrip("/") for node in nodes}
    if default_agent:
        agent_urls.add(default_agent.base_url.rstrip("/"))

    geo = GeoCountryResolver(settings.geoip_database_path)
    monitor = DeviceMonitorService(
        session_factory=session_factory,
        get_agent=get_agent,
        default_agent=default_agent,
        geo=geo,
        max_online_ips=settings.max_online_ips,
        timezone=settings.timezone,
    )

    logger.info(
        "Device monitor started (interval=%ss, max_ips=%s, geoip=%s, nodes=%s)",
        settings.poll_interval_seconds,
        settings.max_online_ips,
        "yes" if settings.geoip_database_path.strip() else "no",
        len(agent_urls),
    )

    try:
        while True:
            try:
                suspended = await asyncio.to_thread(monitor.poll_once)
                if suspended:
                    logger.info("Suspended %s device(s)", suspended)
            except Exception:
                logger.exception("Device monitor poll failed")
            await asyncio.sleep(settings.poll_interval_seconds)
    finally:
        geo.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
