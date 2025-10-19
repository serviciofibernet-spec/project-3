from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional
from datetime import datetime, timezone


class DeviceStore:
    def __init__(self, file_path: str = "data/devices.json") -> None:
        self._path = Path(file_path)
        self._lock = Lock()
        self._data: Dict[str, Dict] = {"devices": {}}
        self._ensure_parent_dir()
        self._load()

    def _ensure_parent_dir(self) -> None:
        parent = self._path.parent
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            # If directory cannot be created, keep in-memory only
            pass

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            with self._path.open("r", encoding="utf-8") as f:
                self._data = json.load(f)
            if "devices" not in self._data or not isinstance(self._data["devices"], dict):
                self._data = {"devices": {}}
        except Exception:
            # Corrupt file: reset to empty
            self._data = {"devices": {}}

    def _save(self) -> None:
        try:
            tmp_path = self._path.with_suffix(".tmp")
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self._path)
        except Exception:
            # Ignore persistence errors; remain in-memory
            pass

    def upsert_inform(self, inform_data: Dict) -> None:
        device_id = inform_data.get("deviceId") or {}
        serial = device_id.get("serialNumber") or ""
        if not serial:
            return
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._lock:
            devices = self._data.setdefault("devices", {})
            existing = devices.get(serial) or {}

            parameter_values: Dict[str, str] = existing.get("parameterValues") or {}
            parameter_values.update(inform_data.get("parameterValues") or {})

            software_version = (
                parameter_values.get("Device.DeviceInfo.SoftwareVersion")
                or parameter_values.get("InternetGatewayDevice.DeviceInfo.SoftwareVersion")
                or existing.get("softwareVersion")
                or ""
            )

            updated = {
                "deviceId": device_id,
                "events": inform_data.get("events") or [],
                "parameterValues": parameter_values,
                "softwareVersion": software_version,
                "lastInform": now_iso,
            }
            devices[serial] = updated
            self._save()

    def list_devices(self) -> List[Dict]:
        with self._lock:
            result: List[Dict] = []
            for serial, data in (self._data.get("devices") or {}).items():
                did = data.get("deviceId") or {}
                result.append(
                    {
                        "serialNumber": serial,
                        "manufacturer": did.get("manufacturer") or "",
                        "productClass": did.get("productClass") or "",
                        "softwareVersion": data.get("softwareVersion") or "",
                        "lastInform": data.get("lastInform") or "",
                    }
                )
            return sorted(result, key=lambda d: d.get("serialNumber") or "")

    def get_device(self, serial_number: str) -> Optional[Dict]:
        with self._lock:
            return (self._data.get("devices") or {}).get(serial_number)
