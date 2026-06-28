from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DevicePreset:
    slug: str
    emoji: str
    title: str
    email_suffix: str
    selectable: bool = True


# Slugs blocked in UI (e.g. clients that need a subscription parser).
BLOCKED_PRESET_SLUGS: frozenset[str] = frozenset({"linkedin", "linux", "happ"})

DEVICE_PRESETS: tuple[DevicePreset, ...] = (
    DevicePreset("iphone", "📱", "iPhone", "phone"),
    DevicePreset("android", "📱", "Android", "android"),
    DevicePreset("ipad", "📱", "iPad", "ipad"),
    DevicePreset("macbook", "💻", "MacBook", "macbook"),
    DevicePreset("windows", "🖥", "Windows PC", "windows"),
)


def is_preset_selectable(slug: str) -> bool:
    if slug in BLOCKED_PRESET_SLUGS:
        return False
    preset = get_device_preset(slug)
    return preset.selectable


def selectable_device_presets() -> tuple[DevicePreset, ...]:
    return tuple(p for p in DEVICE_PRESETS if p.selectable and p.slug not in BLOCKED_PRESET_SLUGS)


def get_device_preset(slug: str) -> DevicePreset:
    for preset in DEVICE_PRESETS:
        if preset.slug == slug:
            return preset
    raise ValueError(f"Unknown device preset: {slug}")
