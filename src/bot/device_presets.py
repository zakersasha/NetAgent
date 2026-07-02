from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DevicePreset:
    slug: str
    emoji: str
    title: str
    email_suffix: str


# Один ключ на подписку — без «слотов» по типу устройства.
VPN_KEY_PRESET = DevicePreset("connection", "🔒", "Защищённый канал", "vpn")

DEVICE_PRESETS: tuple[DevicePreset, ...] = (VPN_KEY_PRESET,)


def get_device_preset(slug: str) -> DevicePreset:
    for preset in DEVICE_PRESETS:
        if preset.slug == slug:
            return preset
    raise ValueError(f"Unknown device preset: {slug}")
