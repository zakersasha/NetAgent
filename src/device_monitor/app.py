import asyncio
import logging
import time

from device_monitor.geo import GeoCountryResolver
from device_monitor.service import DeviceMonitorService
from device_monitor.settings import get_monitor_settings
from netagent_db.session import create_session_factory
from xray_client.client import XrayAgentClient

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_monitor_settings()

    if not settings.database_url.strip():
        raise RuntimeError("Задайте DATABASE_URL в .env")
    if not settings.xray_agent_url.strip():
        raise RuntimeError("Задайте XRAY_AGENT_URL в .env")

    session_factory = create_session_factory(settings.database_url)
    xray_agent = XrayAgentClient(
        base_url=settings.xray_agent_url,
        api_key=settings.xray_agent_api_key,
        verify_ssl=settings.xray_agent_verify_ssl,
        timeout_seconds=settings.xray_agent_timeout_seconds,
    )
    geo = GeoCountryResolver(settings.geoip_database_path)
    monitor = DeviceMonitorService(
        session_factory=session_factory,
        xray_agent=xray_agent,
        geo=geo,
        max_online_ips=settings.max_online_ips,
        timezone=settings.timezone,
    )

    logger.info(
        "Device monitor started (interval=%ss, max_ips=%s, geoip=%s)",
        settings.poll_interval_seconds,
        settings.max_online_ips,
        "yes" if settings.geoip_database_path.strip() else "no",
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
    asyncio.run(main())
