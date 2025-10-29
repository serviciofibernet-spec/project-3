from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from ..config import OLTDeviceConfig
from ..network.ssh_client import SSHClient, SSHClientConfig


class OLTDriver(ABC):
    def __init__(self, device: OLTDeviceConfig):
        self.device = device

    def _new_ssh(self) -> SSHClient:
        ssh_cfg = SSHClientConfig(
            host=self.device.host,
            port=self.device.port,
            username=self.device.username,
            password=self.device.password,
            prompt_regex=self.device.prompt_regex or r"[#>] ?$",
            timeout_s=self.device.ssh_timeout_s,
        )
        return SSHClient(ssh_cfg)

    def send_raw_commands(self, commands: Iterable[str], stop_on_error: bool = False) -> str:
        with self._new_ssh() as ssh:
            return ssh.run_commands(commands, stop_on_error=stop_on_error)

    @abstractmethod
    def get_version(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def list_onus(self, pon_port: Optional[str] = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def add_onu(
        self,
        pon_port: str,
        onu_id: int,
        serial_number: str,
        description: Optional[str] = None,
        line_profile: Optional[str] = None,
        service_profile: Optional[str] = None,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def delete_onu(self, pon_port: str, onu_id: int) -> str:
        raise NotImplementedError
