from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DevicePreset:
    slug: str
    emoji: str
    title: str
    email_suffix: str


DEVICE_PRESETS: tuple[DevicePreset, ...] = (
    DevicePreset("iphone", "📱", "iPhone", "phone"),
    DevicePreset("android", "📱", "Android", "android"),
    DevicePreset("ipad", "📱", "iPad", "ipad"),
    DevicePreset("macbook", "💻", "MacBook", "macbook"),
    DevicePreset("windows", "🖥", "Windows PC", "windows"),
)


def get_device_preset(slug: str) -> DevicePreset:
    for preset in DEVICE_PRESETS:
        if preset.slug == slug:
            return preset
    raise ValueError(f"Unknown device preset: {slug}")
