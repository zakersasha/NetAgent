"""User-facing plan copy — без технических и рискованных формулировок."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlanMarketing:
    devices: str
    audience: str
    channel_label: str


PLAN_MARKETING: dict[str, PlanMarketing] = {
    "connect": PlanMarketing(
        devices="1 устройство",
        audience="личная подписка",
        channel_label="Защищённый канал",
    ),
    "connect_plus": PlanMarketing(
        devices="до 3 устройств",
        audience="малая команда",
        channel_label="Защищённый канал",
    ),
    "combo": PlanMarketing(
        devices="до 3 устройств",
        audience="полный пакет",
        channel_label="Защищённый канал + AI",
    ),
    "combo_max": PlanMarketing(
        devices="до 5 устройств",
        audience="семья + AI",
        channel_label="Защищённый канал + AI",
    ),
    "lite_ai": PlanMarketing(
        devices="—",
        audience="AI-помощник",
        channel_label="AI в Telegram",
    ),
}


def marketing_for(slug: str) -> PlanMarketing | None:
    return PLAN_MARKETING.get(slug)


def plan_feature_lines(slug: str, product_type: str) -> list[str]:
    m = marketing_for(slug)
    lines: list[str] = []
    if product_type in {"vpn", "bundle"}:
        if m:
            lines.append(f"{m.devices} · {m.audience}")
        lines.append("Защищённый канал для удалённой работы")
        lines.append("Профиль доступа в личном кабинете")
    if product_type in {"bundle", "ai"}:
        lines.append("AI-помощник в Telegram без лимита")
    elif product_type == "vpn":
        lines.append("3 сообщения AI бесплатно в день")
    lines.append("Поддержка в боте и на сайте")
    return lines


def channel_product_label(product_type: str) -> str:
    if product_type == "ai":
        return "AI-помощник"
    if product_type == "bundle":
        return "Канал + AI"
    return "Защищённый канал"
