from __future__ import annotations

from typing import Dict, List, Optional, Type

from ..config import AppConfig, OLTDeviceConfig, get_config
from ..drivers import OLTDriver, ZTEC300V2Driver


_DRIVER_REGISTRY: Dict[str, Type[OLTDriver]] = {
    "zte_c300_v2": ZTEC300V2Driver,
}


class OLTService:
    def __init__(self, config: AppConfig):
        self._config = config

    def list_devices(self) -> List[OLTDeviceConfig]:
        return list(self._config.devices)

    def get_device(self, name: str) -> Optional[OLTDeviceConfig]:
        for d in self._config.devices:
            if d.name == name:
                return d
        return None

    def get_driver(self, device_name: str) -> OLTDriver:
        device = self.get_device(device_name)
        if device is None:
            raise ValueError(f"Device '{device_name}' not found in configuration")
        driver_cls = _DRIVER_REGISTRY.get(device.driver)
        if not driver_cls:
            raise ValueError(f"Unknown driver key '{device.driver}' for device '{device_name}'")
        return driver_cls(device)


# Simple global accessor used by FastAPI dependencies
_service_singleton: Optional[OLTService] = None


def get_olt_service() -> OLTService:
    global _service_singleton
    if _service_singleton is None:
        _service_singleton = OLTService(get_config())
    return _service_singleton
