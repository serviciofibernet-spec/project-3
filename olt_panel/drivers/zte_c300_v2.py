from __future__ import annotations

from typing import Optional

from .base import OLTDriver


class ZTEC300V2Driver(OLTDriver):
    """
    ZTE C300 V2 driver (CLI over SSH).

    NOTES:
    - The exact CLI syntax can vary by software version and region.
    - Review and adapt command templates below to your deployment before production use.
    - You can always fall back to send_raw_commands for custom sequences.
    """

    def _port_ctx(self, pon_port: str) -> str:
        # Many ZTE firmwares use gpon-olt_x/x/x as interface context
        # Adjust this template if your platform differs
        return f"gpon-olt_{pon_port}"

    def get_version(self) -> str:
        cmds = [
            "enable",
            # Try common variants; the device will ignore unknown ones
            "show version",
            "show board",
        ]
        return self.send_raw_commands(cmds)

    def list_onus(self, pon_port: Optional[str] = None) -> str:
        if pon_port:
            iface = self._port_ctx(pon_port)
            cmds = [
                "enable",
                "configure terminal",
                f"interface {iface}",
                # Common show variants
                "show onu-information",
                "show gpon onu state",
                "exit",
                "exit",
            ]
        else:
            cmds = [
                "enable",
                "show gpon onu state",
                "show onu-information",
            ]
        return self.send_raw_commands(cmds)

    def add_onu(
        self,
        pon_port: str,
        onu_id: int,
        serial_number: str,
        description: Optional[str] = None,
        line_profile: Optional[str] = None,
        service_profile: Optional[str] = None,
    ) -> str:
        iface = self._port_ctx(pon_port)
        desc = description or f"ONU-{onu_id}"
        # Typical ZTE sequence (verify against your firmware):
        cmds = [
            "enable",
            "configure terminal",
            f"interface {iface}",
            # Examples of add command variants; keep only the one your OLT supports
            f"onu add {onu_id} sn {serial_number} desc {desc}",
            f"onu add {onu_id} sn {serial_number}",
            # Bind profiles (line/srv) under the per-ONU interface context
            f"interface gpon-onu_{pon_port}:{onu_id}",
        ]
        if line_profile:
            cmds.append(f"profile line {line_profile}")
        if service_profile:
            cmds.append(f"profile srv {service_profile}")
        cmds.extend(["exit", "exit"])
        return self.send_raw_commands(cmds, stop_on_error=True)

    def delete_onu(self, pon_port: str, onu_id: int) -> str:
        iface = self._port_ctx(pon_port)
        cmds = [
            "enable",
            "configure terminal",
            f"interface {iface}",
            f"no onu {onu_id}",
            "exit",
            "exit",
        ]
        return self.send_raw_commands(cmds, stop_on_error=True)
