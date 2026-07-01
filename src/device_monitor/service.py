import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from device_monitor.geo import GeoCountryResolver
from netagent_common.traffic import bytes_to_gb
from netagent_db.models import Device, Plan, Subscription
from xray_agent.models import OnlineIpEntry, UserOnlineStats
from xray_client.client import XrayAgentClient, XrayAgentClientError

logger = logging.getLogger(__name__)
GB = 1024**3


class ViolationType(str, Enum):
    MULTIPLE_IPS = "multiple_ips"
    MULTIPLE_COUNTRIES = "multiple_countries"
    TRAFFIC_EXCEEDED = "traffic_exceeded"


@dataclass(frozen=True, slots=True)
class Violation:
    type: ViolationType
    detail: str


def detect_violation(
    ips: list[str],
    geo,
    max_online_ips: int,
) -> Violation | None:
    unique_ips = sorted({ip.strip() for ip in ips if ip.strip()})
    if len(unique_ips) > max_online_ips:
        return Violation(
            type=ViolationType.MULTIPLE_IPS,
            detail=f"online IPs: {', '.join(unique_ips)}",
        )

    countries = sorted({code for ip in unique_ips for code in [geo.country_code(ip)] if code})
    if len(countries) > 1:
        return Violation(
            type=ViolationType.MULTIPLE_COUNTRIES,
            detail=f"countries: {', '.join(countries)}; IPs: {', '.join(unique_ips)}",
        )
    return None


def apply_traffic_delta(current_xray_bytes: int, snapshot_bytes: int, used_bytes: int) -> tuple[int, int]:
    """Return (new_used_bytes, new_snapshot_bytes)."""
    if current_xray_bytes < snapshot_bytes:
        delta = current_xray_bytes
    else:
        delta = current_xray_bytes - snapshot_bytes
    return used_bytes + max(0, delta), current_xray_bytes


def pick_latest_ip(stats: UserOnlineStats) -> tuple[str | None, datetime | None]:
    if not stats.ips:
        return None, None
    latest = max(stats.ips, key=lambda item: item.last_seen)
    if latest.last_seen <= 0:
        return latest.ip, None
    return latest.ip, datetime.fromtimestamp(latest.last_seen, tz=ZoneInfo("UTC"))


class DeviceMonitorService:
    def __init__(
        self,
        session_factory,
        xray_agent: XrayAgentClient,
        geo: GeoCountryResolver,
        max_online_ips: int = 1,
        timezone: str = "Europe/Moscow",
    ) -> None:
        self._session_factory = session_factory
        self._xray_agent = xray_agent
        self._geo = geo
        self._max_online_ips = max_online_ips
        self._timezone = ZoneInfo(timezone)

    def poll_once(self) -> int:
        online_stats = self._fetch_online_stats()
        stats_by_email = {item.email: item for item in online_stats}
        suspended = 0

        with self._session_factory() as session:
            devices = session.scalars(
                select(Device)
                .where(Device.status == "active")
                .options(joinedload(Device.subscription).joinedload(Subscription.plan))
            ).all()

            for device in devices:
                subscription = device.subscription
                plan = subscription.plan if subscription else None

                if plan and plan.traffic_limit_gb:
                    violation = self._sync_traffic(session, device, subscription, plan)
                    if violation:
                        self._suspend_device(session, device, violation.detail)
                        suspended += 1
                        continue

                stats = stats_by_email.get(device.xray_email)
                if not stats or not stats.ips:
                    continue

                ips = [entry.ip for entry in stats.ips]
                last_ip, last_seen = pick_latest_ip(stats)
                device.last_ip = last_ip
                device.last_seen = last_seen

                violation = detect_violation(ips, self._geo, self._max_online_ips)
                if violation is None:
                    continue

                reason = f"{violation.type.value}: {violation.detail}"
                logger.warning(
                    "Suspending device %s (%s): %s",
                    device.device_id,
                    device.xray_email,
                    reason,
                )
                self._suspend_device(session, device, reason)
                suspended += 1

            session.commit()
        return suspended

    def _sync_traffic(
        self,
        session: Session,
        device: Device,
        subscription: Subscription,
        plan: Plan,
    ) -> Violation | None:
        try:
            current = self._xray_agent.user_traffic_bytes(device.xray_email)
        except XrayAgentClientError as exc:
            logger.warning("Traffic stats unavailable for %s: %s", device.xray_email, exc)
            return None

        used = int(subscription.traffic_used_bytes or 0)
        snapshot = int(subscription.traffic_xray_snapshot_bytes or 0)
        new_used, new_snapshot = apply_traffic_delta(current, snapshot, used)
        subscription.traffic_used_bytes = new_used
        subscription.traffic_xray_snapshot_bytes = new_snapshot

        limit_bytes = int(plan.traffic_limit_gb) * GB
        if new_used >= limit_bytes:
            detail = (
                f"traffic: {bytes_to_gb(new_used)} GB / {plan.traffic_limit_gb} GB"
            )
            logger.warning("Traffic limit for %s: %s", device.xray_email, detail)
            return Violation(type=ViolationType.TRAFFIC_EXCEEDED, detail=detail)
        return None

    def _fetch_online_stats(self) -> list[UserOnlineStats]:
        raw = self._xray_agent.users_online_stats()
        result: list[UserOnlineStats] = []
        for item in raw:
            ips: list[OnlineIpEntry] = []
            for ip_item in item.get("ips", []):
                if not isinstance(ip_item, dict):
                    continue
                ip = str(ip_item.get("ip", "")).strip()
                if not ip:
                    continue
                last_seen = int(ip_item.get("last_seen", ip_item.get("lastSeen", 0)) or 0)
                ips.append(OnlineIpEntry(ip=ip, last_seen=last_seen))
            result.append(UserOnlineStats(email=str(item.get("email", "")), ips=ips))
        return result

    def _suspend_device(self, session: Session, device: Device, reason: str) -> None:
        try:
            self._xray_agent.remove_user(device.uuid)
        except XrayAgentClientError as exc:
            logger.error("Xray remove_user failed for %s: %s", device.uuid, exc)

        device.status = "suspended"
        device.suspended_at = datetime.now(self._timezone)
        device.suspended_reason = reason[:255]
